########################################################################
# IAM roles for Terraform in GitHub Actions.
#
# They live here, in bootstrap (local state, applied by an admin), on
# purpose: a CI role must never be able to change its own permissions,
# so nothing that CI applies may manage these roles.
#
#   brand-clothing-terraform-plan              read-only, PR plans + drift checks
#   brand-clothing-terraform-apply-staging     apply, GitHub Environment "infra-staging"  (develop)
#   brand-clothing-terraform-apply-production  apply, GitHub Environment "infra-production" (main + approval)
#
# The GitHub OIDC provider itself is managed in environments/prod.
########################################################################

data "aws_caller_identity" "current" {}

data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

locals {
  account_id = data.aws_caller_identity.current.account_id

  # The MateTeam251 org uses GitHub's ID-based OIDC subject.
  github_subject = "repo:MateTeam251@327962530/brand-clothing-tp251@1350646589"

  apply_environments = {
    staging    = "infra-staging"
    production = "infra-production"
  }
}

# --- Trust policies -----------------------------------------------------

data "aws_iam_policy_document" "plan_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [data.aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # PR plans, plus scheduled drift checks on develop/main.
    # Fork PRs never get an OIDC token, so this means collaborators' PRs only.
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values = [
        "${local.github_subject}:pull_request",
        "${local.github_subject}:ref:refs/heads/develop",
        "${local.github_subject}:ref:refs/heads/main",
      ]
    }
  }
}

data "aws_iam_policy_document" "apply_trust" {
  for_each = local.apply_environments

  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [data.aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # Only jobs running in this GitHub Environment. The Environment's own
    # rules (allowed branch, required reviewer) are enforced before the job starts.
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["${local.github_subject}:environment:${each.value}"]
    }
  }
}

# --- Shared guardrails (explicit Deny beats any Allow) --------------------

data "aws_iam_policy_document" "guardrails" {
  # App secrets live under /brand-clothing/<env>/secrets/ and are never managed
  # by Terraform; CI must not be able to read them. Plain config parameters
  # (/brand-clothing/<env>/NAME) are Terraform-managed, so plans may read those.
  statement {
    sid    = "NoAppSecrets"
    effect = "Deny"
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
      "ssm:GetParametersByPath",
      "ssm:GetParameterHistory",
    ]
    resources = ["arn:aws:ssm:*:${local.account_id}:parameter/brand-clothing/*/secrets/*"]
  }

  # Customer data: database backups and uploaded media.
  statement {
    sid     = "NoCustomerData"
    effect  = "Deny"
    actions = ["s3:GetObject", "s3:GetObjectVersion"]
    resources = [
      "arn:aws:s3:::brand-clothing*-db-backups-wal-*/*",
      "arn:aws:s3:::brand-clothing*-media-*/*",
    ]
  }

  # The state bucket and lock table stay intact whatever a plan contains.
  statement {
    sid    = "ProtectState"
    effect = "Deny"
    actions = [
      "s3:DeleteBucket",
      "s3:DeleteBucketPolicy",
      "s3:PutBucketPolicy",
      "s3:PutBucketVersioning",
      "s3:PutLifecycleConfiguration",
      "s3:DeleteObjectVersion",
    ]
    resources = [
      aws_s3_bucket.terraform_state.arn,
      "${aws_s3_bucket.terraform_state.arn}/*",
    ]
  }

  statement {
    sid       = "ProtectLockTable"
    effect    = "Deny"
    actions   = ["dynamodb:DeleteTable", "dynamodb:UpdateTable"]
    resources = [aws_dynamodb_table.terraform_lock.arn]
  }
}

# Extra limits for the apply roles (they otherwise have AdministratorAccess).
data "aws_iam_policy_document" "apply_limits" {
  # No human-access changes from CI: users, keys, passwords, groups stay manual.
  statement {
    sid    = "NoHumanIam"
    effect = "Deny"
    actions = [
      "iam:CreateUser",
      "iam:DeleteUser",
      "iam:CreateAccessKey",
      "iam:UpdateAccessKey",
      "iam:CreateLoginProfile",
      "iam:UpdateLoginProfile",
      "iam:AttachUserPolicy",
      "iam:PutUserPolicy",
      "iam:AddUserToGroup",
      "iam:AttachGroupPolicy",
      "iam:PutGroupPolicy",
      "iam:CreateGroup",
      "iam:DeleteGroup",
    ]
    resources = ["*"]
  }

  # CI can't touch the CI roles (these three) - no widening its own rights.
  statement {
    sid       = "NoSelfEscalation"
    effect    = "Deny"
    actions   = ["iam:*"]
    resources = ["arn:aws:iam::${local.account_id}:role/brand-clothing-terraform-*"]
  }

  # No billing/account-level changes.
  statement {
    sid       = "NoAccountSettings"
    effect    = "Deny"
    actions   = ["account:*", "organizations:*", "aws-portal:*"]
    resources = ["*"]
  }
}

# --- Plan role --------------------------------------------------------------

resource "aws_iam_role" "terraform_plan" {
  name                 = "brand-clothing-terraform-plan"
  assume_role_policy   = data.aws_iam_policy_document.plan_trust.json
  max_session_duration = 3600
}

resource "aws_iam_role_policy_attachment" "plan_read_only" {
  role       = aws_iam_role.terraform_plan.name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

# Plans take the state lock, so they need to write the lock table.
data "aws_iam_policy_document" "plan_state_lock" {
  statement {
    actions   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:DeleteItem"]
    resources = [aws_dynamodb_table.terraform_lock.arn]
  }
}

resource "aws_iam_role_policy" "plan_state_lock" {
  name   = "state-lock"
  role   = aws_iam_role.terraform_plan.id
  policy = data.aws_iam_policy_document.plan_state_lock.json
}

resource "aws_iam_role_policy" "plan_guardrails" {
  name   = "guardrails"
  role   = aws_iam_role.terraform_plan.id
  policy = data.aws_iam_policy_document.guardrails.json
}

# --- Apply roles --------------------------------------------------------------

resource "aws_iam_role" "terraform_apply" {
  for_each = local.apply_environments

  name                 = "brand-clothing-terraform-apply-${each.key}"
  assume_role_policy   = data.aws_iam_policy_document.apply_trust[each.key].json
  max_session_duration = 3600
}

# Terraform creates IAM roles, EC2, S3, CloudFront, budgets... there is no
# narrower managed policy that covers all of it. The guardrails below and
# the GitHub Environment rules (branch + approval) are the limits.
resource "aws_iam_role_policy_attachment" "apply_admin" {
  for_each = aws_iam_role.terraform_apply

  role       = each.value.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

resource "aws_iam_role_policy" "apply_guardrails" {
  for_each = aws_iam_role.terraform_apply

  name   = "guardrails"
  role   = each.value.id
  policy = data.aws_iam_policy_document.guardrails.json
}

resource "aws_iam_role_policy" "apply_limits" {
  for_each = aws_iam_role.terraform_apply

  name   = "limits"
  role   = each.value.id
  policy = data.aws_iam_policy_document.apply_limits.json
}

# --- Outputs: values for the GitHub settings ---------------------------------

output "terraform_plan_role_arn" {
  description = "Repo variable TF_PLAN_ROLE_ARN."
  value       = aws_iam_role.terraform_plan.arn
}

output "terraform_apply_role_arns" {
  description = "Environment variable TF_APPLY_ROLE_ARN in infra-staging / infra-production."
  value       = { for k, r in aws_iam_role.terraform_apply : k => r.arn }
}

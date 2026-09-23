########################################################################
# GitHub Actions OIDC → AWS role, for CI to run `terraform plan`
#
# No AWS access keys stored in GitHub. GitHub mints a short-lived OIDC
# token per workflow run; this role's trust policy only accepts tokens
# whose `sub` claim identifies THIS repo (either "any branch/PR" scoped
# further below to plan-only permissions).
#
# Deliberately READ-ONLY for now: the team decided CI runs `plan` and
# posts it for review, and `apply` stays a manual step from someone's
# own machine with their own (broader) credentials, until enough trust
# is built in the pipeline to flip to auto-apply-on-merge.
########################################################################

data "tls_certificate" "github" {
  count = var.create_oidc_provider ? 1 : 0
  url   = "https://token.actions.githubusercontent.com/.well-known/openid-configuration"
}

resource "aws_iam_openid_connect_provider" "github" {
  count = var.create_oidc_provider ? 1 : 0

  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.github[0].certificates[0].sha1_fingerprint]
}

locals {
  oidc_provider_arn = var.create_oidc_provider ? aws_iam_openid_connect_provider.github[0].arn : var.existing_oidc_provider_arn
}

data "aws_iam_policy_document" "github_actions_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [local.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # Accepts tokens from: any branch push/PR build on this exact repo.
    # Tighten to specific branches (e.g. only `main` + PR events) once
    # you've confirmed the workflow's actual trigger set — see README.
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values = [
        "repo:${var.github_org}/${var.github_repo}:*",
      ]
    }
  }
}

resource "aws_iam_role" "github_actions_terraform" {
  name               = "${var.project_name}-github-actions-terraform-plan"
  assume_role_policy = data.aws_iam_policy_document.github_actions_trust.json

  tags = {
    Name = "${var.project_name}-github-actions-terraform-plan"
  }
}

# Read-only across the account — sufficient for `terraform plan` (it has
# to read every resource it manages, plus the state bucket/lock table),
# but cannot create, modify, or delete anything. This is what makes
# "plan runs in CI unattended" an acceptable risk today.
resource "aws_iam_role_policy_attachment" "read_only" {
  role       = aws_iam_role.github_actions_terraform.name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

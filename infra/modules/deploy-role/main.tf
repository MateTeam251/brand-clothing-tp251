########################################################################
# Deploy role for one environment.
#
# GitHub Actions assumes it via OIDC from a job running in the given
# GitHub Environment, then: sets IMAGE_TAG in SSM and runs
# /opt/brand-clothing/deploy.sh on that environment's instance through
# SSM Run Command. Nothing else: no ECR, no S3, no access to other envs.
########################################################################

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
}

data "aws_iam_policy_document" "trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [var.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # A job with `environment: <name>` gets sub = <repo>:environment:<name>.
    # Environment protection rules (branches, reviewers) are enforced by
    # GitHub before the job even starts.
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["${var.github_subject}:environment:${var.github_environment}"]
    }
  }
}

resource "aws_iam_role" "this" {
  name                 = var.name
  assume_role_policy   = data.aws_iam_policy_document.trust.json
  max_session_duration = 3600
}

data "aws_iam_policy_document" "deploy" {
  statement {
    sid       = "SetImageTag"
    actions   = ["ssm:PutParameter", "ssm:GetParameter"]
    resources = [
      "arn:aws:ssm:${local.region}:${local.account_id}:parameter${var.ssm_parameter_path}/IMAGE_TAG",
      "arn:aws:ssm:${local.region}:${local.account_id}:parameter${var.ssm_parameter_path}/DB_IMAGE_TAG",
    ]
  }

  # SendCommand is authorized against the document AND every target instance.
  statement {
    sid       = "RunShellScriptDocument"
    actions   = ["ssm:SendCommand"]
    resources = ["arn:aws:ssm:${local.region}::document/AWS-RunShellScript"]
  }

  statement {
    sid       = "OnlyThisEnvironmentsInstance"
    actions   = ["ssm:SendCommand"]
    resources = ["arn:aws:ec2:${local.region}:${local.account_id}:instance/*"]

    condition {
      test     = "StringEquals"
      variable = "ssm:resourceTag/Role"
      values   = [var.instance_role_tag]
    }
  }

  # Reading command status/output can't be scoped to a resource.
  statement {
    sid = "ReadCommandResults"
    actions = [
      "ssm:ListCommands",
      "ssm:ListCommandInvocations",
      "ssm:GetCommandInvocation",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "deploy" {
  name   = "deploy"
  role   = aws_iam_role.this.id
  policy = data.aws_iam_policy_document.deploy.json
}

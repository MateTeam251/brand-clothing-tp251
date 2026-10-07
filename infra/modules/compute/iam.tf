data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
  role_tag   = "${var.project_name}-app"
  ecr_prefix = coalesce(var.ecr_repository_prefix, var.project_name)
}

data "aws_iam_policy_document" "assume_ec2" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "app" {
  name               = "${var.project_name}-app-ec2-role"
  assume_role_policy = data.aws_iam_policy_document.assume_ec2.json
}

# Session Manager shell access (no SSH, no port 22).
resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.app.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

data "aws_iam_policy_document" "app" {
  statement {
    sid       = "EcrAuth"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid = "EcrPull"
    actions = [
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchCheckLayerAvailability",
    ]
    resources = ["arn:aws:ecr:${local.region}:${local.account_id}:repository/${local.ecr_prefix}-*"]
  }

  # .env is rendered from these at boot. SecureStrings use the AWS-managed
  # aws/ssm key, whose key policy already allows decryption through SSM for
  # principals in this account, so no kms:Decrypt statement is needed.
  statement {
    sid = "SsmParameters"
    actions = [
      "ssm:GetParametersByPath",
      "ssm:GetParameters",
      "ssm:GetParameter",
    ]
    resources = [
      "arn:aws:ssm:${local.region}:${local.account_id}:parameter${var.ssm_parameter_path}",
      "arn:aws:ssm:${local.region}:${local.account_id}:parameter${var.ssm_parameter_path}/*",
    ]
  }

  # ListBucket: without it a HEAD on a missing key returns 403 instead of 404,
  # and django-storages' exists() check (FILE_OVERWRITE=False) fails uploads.
  statement {
    sid       = "MediaList"
    actions   = ["s3:ListBucket"]
    resources = [var.media_bucket_arn]
  }

  statement {
    sid       = "MediaObjects"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["${var.media_bucket_arn}/*"]
  }

  # WAL-G: list/get for backup-push and restore, delete for "delete retain".
  # No s3:DeleteObjectVersion: the bucket is versioned, so a delete only adds
  # a delete marker and old versions stay recoverable.
  statement {
    sid       = "BackupsList"
    actions   = ["s3:ListBucket"]
    resources = [var.backups_bucket_arn]
  }

  statement {
    sid       = "BackupsObjects"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${var.backups_bucket_arn}/*"]
  }

  # Analyst reports (weekly cart CSVs). Read/write, no delete: re-running a
  # week overwrites its files, old ones expire via the bucket lifecycle.
  statement {
    sid       = "ReportsList"
    actions   = ["s3:ListBucket"]
    resources = [var.reports_bucket_arn]
  }

  statement {
    sid       = "ReportsObjects"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["${var.reports_bucket_arn}/*"]
  }

  # certbot: only the _acme-challenge TXT record of this instance's origin name.
  dynamic "statement" {
    for_each = var.acme == null ? [] : [var.acme]
    content {
      sid       = "AcmeChallengeRecord"
      actions   = ["route53:ChangeResourceRecordSets"]
      resources = ["arn:aws:route53:::hostedzone/${statement.value.zone_id}"]

      condition {
        test     = "ForAllValues:StringEquals"
        variable = "route53:ChangeResourceRecordSetsNormalizedRecordNames"
        values   = ["_acme-challenge.${statement.value.record_name}"]
      }

      condition {
        test     = "ForAllValues:StringEquals"
        variable = "route53:ChangeResourceRecordSetsRecordTypes"
        values   = ["TXT"]
      }
    }
  }

  dynamic "statement" {
    for_each = var.acme == null ? [] : [var.acme]
    content {
      sid       = "AcmeLookup"
      actions   = ["route53:ListHostedZones", "route53:GetChange"]
      resources = ["*"]
    }
  }

  # Scope to the domain identity once it exists (Phase 4).
  statement {
    sid       = "SesSend"
    actions   = ["ses:SendEmail", "ses:SendRawEmail"]
    resources = ["arn:aws:ses:${local.region}:${local.account_id}:identity/*"]
  }

  # user-data attaches the data volume and the EIP to the instance it runs on.
  # Both actions are authorized against two resources (volume/EIP + instance),
  # and each must be allowed by some statement.
  statement {
    sid       = "AttachOwnDataVolume"
    actions   = ["ec2:AttachVolume"]
    resources = [aws_ebs_volume.data.arn]
  }

  statement {
    sid       = "AssociateOwnEip"
    actions   = ["ec2:AssociateAddress"]
    resources = ["arn:aws:ec2:${local.region}:${local.account_id}:elastic-ip/${aws_eip.app.allocation_id}"]
  }

  statement {
    sid       = "OnlyToAppInstances"
    actions   = ["ec2:AttachVolume", "ec2:AssociateAddress"]
    resources = ["arn:aws:ec2:${local.region}:${local.account_id}:instance/*"]

    condition {
      test     = "StringEquals"
      variable = "ec2:ResourceTag/Role"
      values   = [local.role_tag]
    }
  }

  statement {
    sid       = "Describe"
    actions   = ["ec2:DescribeVolumes", "ec2:DescribeAddresses"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "app" {
  name   = "app-permissions"
  role   = aws_iam_role.app.id
  policy = data.aws_iam_policy_document.app.json
}

resource "aws_iam_instance_profile" "app" {
  name = "${var.project_name}-app-ec2-profile"
  role = aws_iam_role.app.name
}
########################################################################
# Storage module
#
# Three buckets exactly as specified in architecture-detail.md:
#   - frontend-static  : CloudFront OAC only, no direct public access
#   - media            : CloudFront OAC + app role (get/put)
#   - db-backups-wal   : app role put-only (no delete), versioned
#
# CloudFront distribution sits in front of frontend-static. Media is
# served through the same distribution via a second origin/behavior so
# product images also get CDN caching + HTTPS without a second domain.
########################################################################

locals {
  frontend_bucket_name = "${var.project_name}-frontend-static-${var.bucket_suffix}"
  media_bucket_name    = "${var.project_name}-media-${var.bucket_suffix}"
  backups_bucket_name  = "${var.project_name}-db-backups-wal-${var.bucket_suffix}"
}

########################################################################
# frontend-static
########################################################################

resource "aws_s3_bucket" "frontend" {
  bucket = local.frontend_bucket_name

  tags = {
    Name = local.frontend_bucket_name
  }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

########################################################################
# media
########################################################################

resource "aws_s3_bucket" "media" {
  bucket = local.media_bucket_name

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name = local.media_bucket_name
  }
}

resource "aws_s3_bucket_public_access_block" "media" {
  bucket = aws_s3_bucket.media.id

  block_public_acls  = true
  ignore_public_acls = true

  # TEMPORARY: allows the public-read bucket policy statement below.
  # Set both back to true (and remove TemporaryPublicRead) before go-live;
  # media should be served through CloudFront only.
  block_public_policy     = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_server_side_encryption_configuration" "media" {
  bucket = aws_s3_bucket.media.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

########################################################################
# db-backups-wal — put-only for the app role, versioned, lifecycle to
# Glacier at 90 days (see infrastructure-plan.md: the point is that a
# compromised instance can ship backups but never delete existing ones).
########################################################################

resource "aws_s3_bucket" "backups" {
  bucket = local.backups_bucket_name

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name = local.backups_bucket_name
  }
}

resource "aws_s3_bucket_public_access_block" "backups" {
  bucket = aws_s3_bucket.backups.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    id     = "glacier-after-90-days"
    status = "Enabled"

    filter {}

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    noncurrent_version_transition {
      noncurrent_days = 90
      storage_class   = "GLACIER"
    }
  }
}

# App role: put-only, no delete. Written as a data source + resource pair
# so the policy simply doesn't attach until app_iam_role_arn is set
# (compute module doesn't exist yet in this "foundation" pass).
data "aws_iam_policy_document" "backups_bucket_policy" {
  count = var.app_iam_role_arn == null ? 0 : 1

  statement {
    sid    = "AppRolePutOnly"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = [var.app_iam_role_arn]
    }

    actions = [
      "s3:PutObject",
    ]

    resources = ["${aws_s3_bucket.backups.arn}/*"]

    # Explicitly no s3:DeleteObject / s3:DeleteObjectVersion here
  }
}

resource "aws_s3_bucket_policy" "backups" {
  count  = var.app_iam_role_arn == null ? 0 : 1
  bucket = aws_s3_bucket.backups.id
  policy = data.aws_iam_policy_document.backups_bucket_policy[0].json
}

# Media bucket policy. Always exists, so CloudFront can read media even
# before the compute module (and its App-EC2-Role) exists. The app-role
# statement is added only once app_iam_role_arn is set.
data "aws_iam_policy_document" "media_bucket_policy" {
  statement {
    sid    = "CloudFrontOAC"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.media.arn}/*"]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.frontend.arn]
    }
  }

  # TEMPORARY: public read of media objects (GetObject only, no listing).
  # Remove before go-live, together with the public access block change above.
  statement {
    sid    = "TemporaryPublicRead"
    effect = "Allow"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.media.arn}/*"]
  }

  dynamic "statement" {
    for_each = var.app_iam_role_arn == null ? [] : [var.app_iam_role_arn]
    content {
      sid    = "AppRoleGetPut"
      effect = "Allow"

      principals {
        type        = "AWS"
        identifiers = [statement.value]
      }

      actions = [
        "s3:GetObject",
        "s3:PutObject",
      ]

      resources = ["${aws_s3_bucket.media.arn}/*"]
    }
  }
}

resource "aws_s3_bucket_policy" "media" {
  bucket = aws_s3_bucket.media.id
  policy = data.aws_iam_policy_document.media_bucket_policy.json

  # The policy has public statements, so S3 rejects it while the public
  # access block still blocks public policies. Apply the block change first.
  depends_on = [aws_s3_bucket_public_access_block.media]
}

########################################################################
# CloudFront — frontend-static via Origin Access Control. Media rides
# the same distribution on a second origin/behavior.
########################################################################

resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${var.project_name}-frontend-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  comment             = "${var.project_name} frontend + media"

  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "frontend-s3"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  origin {
    domain_name              = aws_s3_bucket.media.bucket_regional_domain_name
    origin_id                = "media-s3"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "frontend-s3"
    viewer_protocol_policy = "redirect-to-https"
    compress                = true

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  ordered_cache_behavior {
    path_pattern            = "/media/*"
    allowed_methods         = ["GET", "HEAD"]
    cached_methods          = ["GET", "HEAD"]
    target_origin_id        = "media-s3"
    viewer_protocol_policy  = "redirect-to-https"
    compress                = true

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  # SPA fallback: unknown paths (client-side routes) resolve to index.html.
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # No custom domain / ACM cert wired up yet — uses the default
  # *.cloudfront.net certificate until Route 53 + a real domain
  # (dns module) exist. Swap in `aliases` + `viewer_certificate.acm_certificate_arn`
  # at that point; see architecture-detail.md's DNS & TLS table.
  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "${var.project_name}-cdn"
  }
}

# Bucket policy for the frontend bucket itself — CloudFront OAC read-only,
# nothing else. (Split from media's policy above since this one never
# depends on app_iam_role_arn.)
data "aws_iam_policy_document" "frontend_bucket_policy" {
  statement {
    sid    = "CloudFrontOAC"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.frontend.arn}/*"]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.frontend.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  policy = data.aws_iam_policy_document.frontend_bucket_policy.json
}

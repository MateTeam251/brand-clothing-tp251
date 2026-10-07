########################################################################
# Storage module
#
# Three buckets exactly as specified in architecture-detail.md:
#   - frontend-static  : CloudFront OAC only, no direct public access
#   - media            : CloudFront OAC + app role (get/put)
#   - db-backups-wal   : app role put-only (no delete), versioned
#   - reports          : private analyst reports (weekly cart CSVs), app
#                        role read/write via its IAM policy
#
# CloudFront distribution sits in front of frontend-static. Media is
# served through the same distribution via a second origin/behavior so
# product images also get CDN caching + HTTPS without a second domain.
########################################################################

locals {
  frontend_bucket_name = "${var.project_name}-frontend-static-${var.bucket_suffix}"
  media_bucket_name    = "${var.project_name}-media-${var.bucket_suffix}"
  backups_bucket_name  = "${var.project_name}-db-backups-wal-${var.bucket_suffix}"
  reports_bucket_name  = "${var.project_name}-reports-${var.bucket_suffix}"
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

  # Private: the app hands out signed URLs; CloudFront reads via OAC.
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
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
  count = var.app_role_enabled ? 1 : 0

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
  count  = var.app_role_enabled ? 1 : 0
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

  dynamic "statement" {
    for_each = var.app_role_enabled ? [var.app_iam_role_arn] : []
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

  depends_on = [aws_s3_bucket_public_access_block.media]
}

########################################################################
# reports — private. Weekly cart report CSVs written by the app
# (carts.reports, prefix reports/carts/). Never public: analysts get
# their own read-only access. Old reports expire after a year.
########################################################################

resource "aws_s3_bucket" "reports" {
  bucket = local.reports_bucket_name

  tags = {
    Name = local.reports_bucket_name
  }
}

resource "aws_s3_bucket_public_access_block" "reports" {
  bucket = aws_s3_bucket.reports.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "reports" {
  bucket = aws_s3_bucket.reports.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "reports" {
  bucket = aws_s3_bucket.reports.id

  rule {
    id     = "expire-after-1-year"
    status = "Enabled"

    filter {}

    expiration {
      days = 365
    }
  }
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

# AWS-managed policies for the backend paths: never cache, forward everything
# (cookies, query, Authorization) except Host, so the origin gets its own name.
data "aws_cloudfront_cache_policy" "caching_disabled" {
  name = "Managed-CachingDisabled"
}

data "aws_cloudfront_origin_request_policy" "all_viewer_except_host" {
  name = "Managed-AllViewerExceptHostHeader"
}

# SPA routing for the frontend only: paths whose last segment has no file
# extension (/catalog, /product/12) get index.html. www.* redirects to the
# bare domain. Error-page rewrites would
# also hit /api/* and turn API 404s into 200 HTML.
resource "aws_cloudfront_function" "spa_rewrite" {
  name    = "${var.project_name}-spa-rewrite"
  runtime = "cloudfront-js-2.0"
  publish = true
  code    = <<-JS
    function handler(event) {
      var request = event.request;
      var host = request.headers.host ? request.headers.host.value : '';
      if (host.indexOf('www.') === 0) {
        return {
          statusCode: 301,
          statusDescription: 'Moved Permanently',
          headers: { location: { value: 'https://' + host.substring(4) + request.uri } },
        };
      }
      var last = request.uri.split('/').pop();
      if (last.indexOf('.') === -1) {
        request.uri = '/index.html';
      }
      return request;
    }
  JS
}

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled     = true
  aliases             = var.domain_aliases
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
    compress               = true

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.spa_rewrite.arn
    }
  }

  # Backend (nginx -> Django) over HTTPS, see api_origin_domain.
  dynamic "origin" {
    for_each = var.api_origin_domain == null ? [] : [var.api_origin_domain]
    content {
      domain_name = origin.value
      origin_id   = "api"

      custom_origin_config {
        http_port              = 80
        https_port             = 443
        origin_protocol_policy = "https-only"
        origin_ssl_protocols   = ["TLSv1.2"]
        origin_read_timeout    = 60
      }
    }
  }

  # /static/* is Django admin's CSS/JS (WhiteNoise); the frontend uses /assets/.
  dynamic "ordered_cache_behavior" {
    for_each = var.api_origin_domain == null ? [] : ["/api/*", "/static/*"]
    content {
      path_pattern             = ordered_cache_behavior.value
      allowed_methods          = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
      cached_methods           = ["GET", "HEAD"]
      target_origin_id         = "api"
      viewer_protocol_policy   = "redirect-to-https"
      compress                 = true
      cache_policy_id          = data.aws_cloudfront_cache_policy.caching_disabled.id
      origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer_except_host.id
    }
  }

  ordered_cache_behavior {
    path_pattern           = "/media/*"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "media-s3"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # Default *.cloudfront.net certificate until a domain is set.
  viewer_certificate {
    cloudfront_default_certificate = var.acm_certificate_arn == null
    acm_certificate_arn            = var.acm_certificate_arn
    ssl_support_method             = var.acm_certificate_arn == null ? null : "sni-only"
    minimum_protocol_version       = var.acm_certificate_arn == null ? "TLSv1" : "TLSv1.2_2021"
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

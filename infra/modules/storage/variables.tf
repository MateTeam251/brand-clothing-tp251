variable "project_name" {
  description = "Short name used to prefix bucket names and tags."
  type        = string
  default     = "brand-clothing"
}

variable "bucket_suffix" {
  description = "Suffix to make bucket names globally unique (e.g. your AWS account ID). Required — S3 bucket names are global."
  type        = string
}

variable "app_iam_role_arn" {
  description = <<-EOT
    ARN of the App-EC2-Role from the compute module, so its bucket
    policies (media: get/put, db-backups-wal: put-only) can be scoped to
    it. Leave null for now — this module stands alone before compute
    exists. Once compute is built, pass its role ARN here and re-apply;
    the policies below activate automatically.
  EOT
  type        = string
  default     = null
}

variable "app_role_enabled" {
  description = <<-EOT
    Turns on the app-role bucket policies. A plain bool because count and
    for_each must be known at plan time, and app_iam_role_arn isn't until
    the role is created.
  EOT
  type        = bool
  default     = false
}

variable "domain_aliases" {
  description = "Custom domain names for the CloudFront distribution. Needs acm_certificate_arn."
  type        = list(string)
  default     = []
}

variable "acm_certificate_arn" {
  description = "ACM certificate (us-east-1) covering domain_aliases. Null = default cloudfront.net certificate."
  type        = string
  default     = null
}

variable "api_origin_domain" {
  description = "Backend host name (HTTPS). Set = /api/* and /static/* go there. Null = frontend and media only."
  type        = string
  default     = null
}

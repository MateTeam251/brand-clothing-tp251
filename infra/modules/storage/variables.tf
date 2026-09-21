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
  type    = string
  default = null
}

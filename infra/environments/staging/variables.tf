variable "aws_region" {
  type    = string
  default = "eu-central-1"
}

variable "project_name" {
  description = "Prefix for staging resource names. Must differ from prod's."
  type        = string
  default     = "brand-clothing-staging"
}

variable "ecr_repository_prefix" {
  description = "Staging runs the same images as prod (built once by CI)."
  type        = string
  default     = "brand-clothing"
}

variable "bucket_suffix" {
  description = "Suffix to make S3 bucket names globally unique — use your AWS account ID."
  type        = string
}

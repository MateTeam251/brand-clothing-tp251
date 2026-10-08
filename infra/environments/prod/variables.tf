variable "aws_region" {
  type    = string
  default = "eu-central-1"
}

variable "project_name" {
  type    = string
  default = "brand-clothing"
}

variable "bucket_suffix" {
  description = "Suffix to make S3 bucket names globally unique — use your AWS account ID."
  type        = string
}

variable "budget_limit_usd" {
  description = "Monthly AWS Budget alert threshold (USD)."
  type        = number
  default     = 30
}

variable "budget_alert_email" {
  description = "Email address to notify when the budget threshold is forecast to be exceeded."
  type        = string
  sensitive   = true # plans are posted as PR comments in a public repo
}

variable "github_org" {
  type    = string
  default = "MateTeam251"
}

variable "github_repo" {
  type    = string
  default = "brand-clothing-tp251"
}

variable "create_oidc_provider" {
  description = "False if this AWS account already has a GitHub Actions OIDC provider from another project."
  type        = bool
  default     = true
}

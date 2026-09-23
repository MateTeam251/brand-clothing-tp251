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
  description = "Monthly AWS Budget alert threshold. Set below the hard $30/month cap so it's a real early warning, not a formality."
  type        = number
  default     = 27
}

variable "budget_alert_email" {
  description = "Email address to notify when the budget threshold is forecast to be exceeded."
  type        = string
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

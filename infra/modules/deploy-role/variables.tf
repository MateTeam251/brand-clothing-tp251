variable "name" {
  description = "IAM role name, e.g. brand-clothing-staging-github-deploy."
  type        = string
}

variable "oidc_provider_arn" {
  description = "GitHub Actions OIDC provider ARN (created once per account, in prod)."
  type        = string
}

variable "github_subject" {
  description = "OIDC sub prefix for the repo. This org uses the ID-based form: repo:ORG@<org id>/REPO@<repo id>."
  type        = string
}

variable "github_environment" {
  description = "GitHub Environment allowed to assume the role (staging / production). Only jobs that declare this environment get a matching sub claim."
  type        = string
}

variable "ssm_parameter_path" {
  description = "Environment's SSM path, no trailing slash. The role may only write <path>/IMAGE_TAG."
  type        = string
}

variable "instance_role_tag" {
  description = "Value of the Role tag on the environment's app instance. Run Command is limited to instances with this tag."
  type        = string
}

variable "frontend_bucket_arn" {
  description = "Frontend bucket the release workflow uploads the built site to. Null = no frontend deploy."
  type        = string
  default     = null
}

variable "cloudfront_distribution_arn" {
  description = "Distribution to invalidate after a frontend upload."
  type        = string
  default     = null
}

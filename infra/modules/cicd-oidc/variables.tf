variable "project_name" {
  type    = string
  default = "brand-clothing"
}

variable "github_org" {
  description = "GitHub org/user that owns the repo."
  type        = string
  default     = "MateTeam251"
}

variable "github_repo" {
  description = "GitHub repo name (without org prefix)."
  type        = string
  default     = "brand-clothing-tp251"
}

variable "create_oidc_provider" {
  description = <<-EOT
    Whether to create the GitHub Actions OIDC provider in this AWS
    account. There can only be ONE OIDC provider per URL per account —
    if this account already has one (e.g. from another project using
    GitHub Actions), set this to false and pass its ARN via
    existing_oidc_provider_arn instead.
  EOT
  type    = bool
  default = true
}

variable "existing_oidc_provider_arn" {
  description = "Used only when create_oidc_provider = false."
  type        = string
  default     = null
}

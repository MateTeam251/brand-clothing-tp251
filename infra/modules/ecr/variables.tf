variable "project_name" {
  type = string
}

variable "repositories" {
  description = "Short names; each becomes <project_name>-<name>."
  type        = set(string)
  default     = ["backend", "db"]
}

variable "images_to_keep" {
  type    = number
  default = 20
}

variable "oidc_provider_arn" {
  description = "GitHub Actions OIDC provider ARN (from the cicd-oidc module)."
  type        = string
}

variable "github_org" {
  type = string
}

variable "github_repo" {
  type = string
}

variable "push_branches" {
  description = "Only workflow runs on these branches can push images."
  type        = list(string)
  default     = ["develop", "main"]
}

variable "github_owner_id" {
  description = "Numeric GitHub org ID. Set when the org's OIDC sub claim includes IDs (repo:org@id/repo@id:...)."
  type        = string
  default     = null
}

variable "github_repo_id" {
  description = "Numeric GitHub repo ID, used together with github_owner_id."
  type        = string
  default     = null
}
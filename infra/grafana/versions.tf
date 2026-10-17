terraform {
  required_version = ">= 1.10" # use_lockfile

  required_providers {
    grafana = {
      source  = "grafana/grafana"
      version = "~> 4.0"
    }
  }

  # Same state bucket as the environments (backend.hcl), own key.
  backend "s3" {
    key          = "grafana/terraform.tfstate"
    encrypt      = true
    use_lockfile = true
  }
}

provider "grafana" {
  url             = var.grafana_url
  auth            = var.grafana_auth
  sm_url          = var.sm_url
  sm_access_token = var.sm_access_token
}

terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Same state bucket and lock table as prod (backend.hcl), different key.
  backend "s3" {
    key     = "staging/terraform.tfstate"
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region
}

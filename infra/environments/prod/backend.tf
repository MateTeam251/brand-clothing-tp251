terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  backend "s3" {
    # Fill these in from the outputs of infra/bootstrap.
    bucket         = "REPLACE_WITH_STATE_BUCKET_NAME"
    key            = "prod/terraform.tfstate"
    region         = "eu-central-1"
    dynamodb_table = "brand-clothing-terraform-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}

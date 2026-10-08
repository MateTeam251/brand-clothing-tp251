terraform {
  required_version = ">= 1.10" # use_lockfile

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
    key     = "prod/terraform.tfstate"
    encrypt = true

    # Lock = a .tflock file next to the state in S3 (no DynamoDB table).
    use_lockfile = true
  }
}

provider "aws" {
  region = var.aws_region
}

# CloudFront only accepts ACM certificates from us-east-1.
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

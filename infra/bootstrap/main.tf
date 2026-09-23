########################################################################
# Terraform remote state bootstrap
#
# This is the one piece of infrastructure that has to be created by hand
# (or applied once with local state) before any other module can use a
# remote backend — Terraform can't store its own state for the bucket
# that will hold its state.
#
# Run this ONCE, with local state, then never touch it again except to
# import/adjust manually. environments/prod/backend.tf points at the
# bucket + table this creates.
########################################################################

terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Deliberately local state for this config only.
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS region for the state bucket/lock table."
  type        = string
  default     = "us-east-1"
}

variable "state_bucket_name" {
  description = "Globally-unique S3 bucket name for Terraform remote state."
  type        = string
}

resource "aws_s3_bucket" "terraform_state" {
  bucket = var.state_bucket_name

  # Guard against `terraform destroy` ever taking the state bucket with it.
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "terraform_lock" {
  name         = "brand-clothing-terraform-lock"
  billing_mode = "PAY_PER_REQUEST" # a handful of locks/month — on-demand is effectively free
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}

output "state_bucket_name" {
  value = aws_s3_bucket.terraform_state.id
}

output "lock_table_name" {
  value = aws_dynamodb_table.terraform_lock.name
}

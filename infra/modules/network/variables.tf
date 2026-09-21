variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the single public subnet."
  type        = string
  default     = "10.0.1.0/24"
}

variable "availability_zone" {
  description = "AZ for the public subnet. Single-AZ is deliberate — no ALB/RDS multi-AZ requirement at this stage."
  type        = string
  default     = "us-east-1a"
}

variable "project_name" {
  description = "Short name used to prefix/tag every resource in this module."
  type        = string
  default     = "brand-clothing"
}

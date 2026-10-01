variable "project_name" {
  type = string
}

variable "subnet_id" {
  description = "Public subnet for the app instance. Its AZ is also used for the data volume."
  type        = string
}

variable "security_group_id" {
  description = "sg-app from the network module."
  type        = string
}

variable "ami_id" {
  description = <<-EOT
    Amazon Linux 2023 arm64 AMI. Pinned on purpose: a new AMI means a new
    instance, so it's bumped by PR, not whenever Amazon publishes one.
    Newest: aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64 --query Parameter.Value --output text
  EOT
  type        = string
}

variable "instance_type" {
  type    = string
  default = "t4g.small"
}

variable "instance_count" {
  description = "ASG size. 0 until user-data exists, then 1. Never more than 1: the data volume attaches to one instance only."
  type        = number
  default     = 0

  validation {
    condition     = contains([0, 1], var.instance_count)
    error_message = "instance_count must be 0 or 1."
  }
}

variable "root_volume_size" {
  description = "GiB. OS + Docker images."
  type        = number
  default     = 16
}

variable "data_volume_size" {
  description = "GiB. Postgres data on /data, survives instance replacement."
  type        = number
  default     = 20
}

variable "media_bucket_arn" {
  type = string
}

variable "backups_bucket_arn" {
  type = string
}

variable "ssm_parameter_path" {
  description = "SSM path the instance renders .env from. No trailing slash."
  type        = string
  default     = "/brand-clothing/prod"
}

variable "compose_file" {
  description = "Contents of docker-compose.prod.yml, written to the instance by user-data."
  type        = string
}

variable "nginx_conf" {
  description = "Contents of nginx/default.conf."
  type        = string
}

variable "compose_version" {
  description = "Docker Compose plugin release (AL2023 doesn't package it)."
  type        = string
  default     = "v2.39.2"
}

variable "ecr_repository_prefix" {
  description = "Prefix of the ECR repos to pull from (<prefix>-backend, <prefix>-db). Defaults to project_name; staging sets it to the prod prefix to share images."
  type        = string
  default     = null
}

variable "schedule" {
  description = "Optional working-hours schedule. Cron in the given IANA time zone, e.g. start \"0 8 * * MON-FRI\", stop \"0 20 * * MON-FRI\", \"Europe/Kyiv\". Null = always on."
  type = object({
    start_cron = string
    stop_cron  = string
    time_zone  = string
  })
  default = null
}

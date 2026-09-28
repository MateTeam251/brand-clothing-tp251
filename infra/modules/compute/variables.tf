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

variable "user_data" {
  description = "Plain-text user-data script (base64-encoded here). Null until PR 2."
  type        = string
  default     = null
}
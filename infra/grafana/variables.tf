# Moving to another Grafana Cloud stack = new url + tokens, then apply.
variable "grafana_url" {
  type    = string
  default = "https://sturdyscone1696.grafana.net"
}

variable "sm_url" {
  description = "Synthetic Monitoring API (Testing & synthetics -> Config)."
  type        = string
  default     = "https://synthetic-monitoring-api-eu-west-2.grafana.net"
}

variable "grafana_auth" {
  description = "Service account token (TF_VAR_grafana_auth)."
  type        = string
  sensitive   = true
}

variable "sm_access_token" {
  description = "Synthetic Monitoring access token (TF_VAR_sm_access_token)."
  type        = string
  sensitive   = true
}

variable "alert_email" {
  description = "Where alerts go. Secret: the repo is public (TF_VAR_alert_email)."
  type        = string
  sensitive   = true
}

# Uptime check from outside (Grafana's probes). Its alert (3 of 6 failed in 5 min,
# runbook docs/alerts.md#prod-site-down) is set in the check's Alerting step for now.

data "grafana_synthetic_monitoring_probes" "all" {}

resource "grafana_synthetic_monitoring_check" "prod_admin_login" {
  job        = "prod-admin-login"
  target     = "https://theart-theartist.com/api/admin/login/"
  enabled    = true
  frequency  = 120000 # ms
  folder_uid = "grafana-synthetic-monitoring-app"

  probes = [
    data.grafana_synthetic_monitoring_probes.all.probes.Frankfurt,
    data.grafana_synthetic_monitoring_probes.all.probes.London,
    data.grafana_synthetic_monitoring_probes.all.probes.Paris,
  ]

  settings {
    http {
      method             = "GET"
      ip_version         = "V4"
      valid_status_codes = [200]
    }
  }
}

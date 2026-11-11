resource "grafana_folder" "brand_clothing" {
  uid   = "f9fwmk"
  title = "brand-clothing"
}

# Alerts go to Slack (when the webhook is set) and always to email as a backup.
resource "grafana_contact_point" "alerts" {
  name               = "brand-clothing-alerts"
  disable_provenance = true

  dynamic "slack" {
    # nonsensitive: for_each can't use a sensitive value; only "is it set" is revealed.
    for_each = nonsensitive(var.slack_webhook_url != "") ? [1] : []
    content {
      url   = var.slack_webhook_url
      title = "{{ if eq .Status \"firing\" }}:red_circle:{{ else }}:large_green_circle:{{ end }} {{ .CommonLabels.alertname }}"
      text  = <<-EOT
        {{ range .Alerts }}*{{ .Status | toUpper }}*{{ with .Annotations.runbook_url }} · <{{ . }}|runbook>{{ end }}
        {{ end }}
      EOT
    }
  }

  email {
    addresses = [var.alert_email]
  }
}

# Singleton: the whole notification policy tree of the stack.
resource "grafana_notification_policy" "default" {
  contact_point      = grafana_contact_point.alerts.name
  group_by           = ["grafana_folder", "alertname"]
  group_wait         = "30s"
  group_interval     = "5m"
  repeat_interval    = "4h"
  disable_provenance = true
}

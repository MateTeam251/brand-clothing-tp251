resource "grafana_folder" "brand_clothing" {
  uid   = "f9fwmk"
  title = "brand-clothing"
}

resource "grafana_contact_point" "email" {
  name               = "grafana-maxmlv-email"
  disable_provenance = true # created in the UI; false would force a replacement

  email {
    addresses = [var.alert_email]
  }
}

# Singleton: the whole notification policy tree of the stack.
resource "grafana_notification_policy" "default" {
  contact_point      = grafana_contact_point.email.name
  group_by           = ["grafana_folder", "alertname"]
  group_wait         = "30s"
  group_interval     = "5m"
  repeat_interval    = "4h"
  disable_provenance = true
}

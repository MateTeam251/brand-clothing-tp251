# Adopt what was created in the UI. Remove this file after the first apply.

import {
  to = grafana_folder.brand_clothing
  id = "f9fwmk"
}

import {
  to = grafana_contact_point.email
  id = "grafana-maxmlv-email"
}

import {
  to = grafana_notification_policy.default
  id = "policy"
}

import {
  for_each = toset(["prod-backups", "prod-cert", "prod-infra"])
  to       = grafana_rule_group.this[each.key]
  id       = "f9fwmk:${each.key}"
}

import {
  to = grafana_synthetic_monitoring_check.prod_admin_login
  id = "91960"
}

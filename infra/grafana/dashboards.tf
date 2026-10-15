# Dashboards (JSON from dashboards/generate.py). Hierarchy: Overview first,
# then Requests (RED), Infrastructure (USE), Database, Logs.
resource "grafana_dashboard" "this" {
  for_each = toset(["overview", "requests", "infrastructure", "database", "logs"])

  folder      = grafana_folder.brand_clothing.uid
  config_json = file("${path.module}/dashboards/${each.key}.json")
  overwrite   = true # Requests and Logs keep the uids of the UI-made dashboards they replace
}

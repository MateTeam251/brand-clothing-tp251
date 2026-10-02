# Grafana snapshots

Exported from the Grafana Cloud stack `sturdyscone1696`. The source of truth is still Grafana;
re-export after changing a rule or dashboard there.

- `alerts/brand-clothing.yml`: alert rules, folder `brand-clothing` (groups `prod-infra`, `prod-backups`)
- `dashboards/app-requests.json`: "App - Requests" (nginx JSON logs)
- `dashboards/logs.json`: "Logs" (errors, backups, nginx 5xx, all logs with `env`/`container`/`search` filters)

Not exported:
- **Node Exporter Full**: community dashboard, re-import with Dashboards → New → Import → ID `1860`, data source `…-prom`
- **Contact points**: contain a personal email; recreate `grafana-maxmlv-email` and set it as the default policy's contact point
- **Synthetic check** `prod-admin-login`: HTTP GET `http://3.73.249.226/api/admin/login/`, 3 EU probes, every 2 min, alert at 3 of 6 failed
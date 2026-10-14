# Grafana (Terraform)

Grafana Cloud stack `sturdyscone1696`, managed with Terraform: folder, contact point,
notification policy, alert rules (`alerts.tf`), synthetic check (`synthetics.tf`).
Runbooks for every alert: `docs/alerts.md`.

Change things here, not in the UI (provisioned rules are read-only in the UI).
CI (`.github/workflows/grafana.yml`): plan on PRs, apply on merge to `main` (approval).

Secrets (GitHub): `GRAFANA_AUTH` (service account `terraform`, Admin),
`GRAFANA_SM_ACCESS_TOKEN`, `TF_BUDGET_ALERT_EMAIL` (alert email; the repo is public).

Local plan (PowerShell):

```powershell
cd infra/grafana
terraform init -backend-config="../environments/prod/backend.hcl"
$env:TF_VAR_grafana_auth    = Read-Host -MaskInput "Grafana token"
$env:TF_VAR_sm_access_token = Read-Host -MaskInput "SM token"
$env:TF_VAR_alert_email     = Read-Host "Alert email"
terraform plan
```

Moving to the customer's stack: new `grafana_url` / `sm_url` + tokens, apply, then point
Alloy's push credentials (SSM) at the new stack.

Not in Terraform (yet):
- Dashboards `dashboards/*.json` (v2 export, import by hand: Dashboards → New → Import)
- **Node Exporter Full**: community dashboard ID `1860`, data source `…-prom`
- The synthetic check's per-check alert (Alerting step of the check)

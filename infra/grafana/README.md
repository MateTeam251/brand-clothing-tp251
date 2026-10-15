# Grafana (Terraform)

Grafana Cloud stack `sturdyscone1696`, managed with Terraform: folder, contact point,
notification policy, alert rules (`alerts.tf`), synthetic checks (`synthetics.tf`: admin login, frontend).
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

Dashboards (`dashboards.tf`): Overview → Requests (RED, nginx logs), Infrastructure
(USE: server + containers), Database (Postgres), Logs. All have an `env` switch and
release markers. Edit `dashboards/generate.py`, run `python dashboards/generate.py`,
commit the script and the JSON. Tip: try a change first via Dashboards → New → Import
into a `TMP` dashboard, then put it in the script.

Not in Terraform: the synthetic check's per-check alert (Alerting step of the check).
Deep-dive server dashboard if ever needed: import community ID `1860` by hand.

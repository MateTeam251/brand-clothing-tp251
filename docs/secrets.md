# Secrets

Every secret, where it lives, and how to rotate it. Values are never in git, Terraform or chat.

## Inventory

| Secret | Where | Used by | Rotate |
|---|---|---|---|
| `SECRET_KEY` | SSM `/brand-clothing/<env>/secrets/` | Django: sessions, password-reset links, JWT signing | yearly, on handover, on leak |
| `POSTGRES_PASSWORD` | SSM (same) | `web`, `celery`, `db` | on handover, on leak |
| `PG_MONITOR_PASSWORD` | SSM (same) | Alloy (Postgres exporter, read-only role `monitor`) | on handover, on leak |
| `EMAIL_HOST_PASSWORD` | SSM (same) | Django → Resend SMTP (API key, sending only) | yearly, on handover |
| `GRAFANA_CLOUD_TOKEN` | SSM (same) | Alloy → Grafana Cloud (metrics/logs push) | yearly, on handover |
| `WAYFORPAY_SECRET_KEY` | SSM (same), when configured | payments | on handover, on leak |
| `NOVA_POSHTA_API_KEY` | SSM (same), when configured | Nova Poshta branch sync (`delivery`) | on handover, on leak |
| `GRAFANA_AUTH` | GitHub secret | Terraform `infra/grafana`, release annotations | yearly, on handover |
| `GRAFANA_SM_ACCESS_TOKEN` | GitHub secret | Terraform synthetic checks | yearly, on handover |
| `TF_BUDGET_ALERT_EMAIL` | GitHub secret | alert / budget email (not secret, just not public) | when the address changes |

No secret, nothing to rotate:
- **AWS from CI**: OIDC roles, short-lived credentials.
- **AWS from the app**: instance role (S3, SES, SSM).

Accounts (owner rotates, MFA on): AWS root, admin IAM users (access keys: yearly), Grafana Cloud, Resend, GitHub, domain registrar.

## How SSM secrets reach the app

`deploy.sh` on the instance renders `.env` from SSM on every boot and every deploy;
`docker compose up -d` then recreates only the containers whose environment changed.
So **change in SSM → redeploy the environment**:

- staging/prod redeploy: **Actions → Release → Run workflow**, `environment`, `image_tag` = the SHA currently deployed (SSM `IMAGE_TAG`).
- a release or an instance refresh does it too.

New value, never printed (PowerShell):

```powershell
function New-Secret([int]$bytes) {
    $b = New-Object byte[] $bytes
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
    [Convert]::ToBase64String($b).TrimEnd('=').Replace('+','-').Replace('/','_')
}
$v = New-Secret 48
if ($v.Length -ne 64) { throw "New-Secret failed, nothing written" }
aws ssm put-parameter --profile brand-clothing --overwrite --type SecureString --name /brand-clothing/<env>/secrets/<NAME> "--value=$v"
Remove-Variable v
```

A value someone gives you: `$v = Read-Host -MaskInput "<NAME>"`, then `if (-not $v) { throw "empty" }`, same `put-parameter`.

Always define the function and generate the value in the same paste: if `New-Secret`
fails, `$v` keeps its previous value and that would be written instead (happened once).
To wipe a wrong value from the parameter's history: `delete-parameter`, then `put-parameter` again.

## Procedures

**`SECRET_KEY`**: put a new value, redeploy. Everyone is logged out (sessions and JWTs are signed with it) and open password-reset links stop working. Do it outside busy hours.

**`EMAIL_HOST_PASSWORD`** (Resend): create a new API key (Sending access, domain only) → put it in SSM → redeploy → send a test email (password reset) → delete the old key in Resend.

**`GRAFANA_CLOUD_TOKEN`**: Grafana Cloud → Access policies → the Alloy policy → add token → SSM → redeploy → check new metrics/logs arrive (Overview dashboard) → delete the old token.

**`GRAFANA_AUTH` / `GRAFANA_SM_ACCESS_TOKEN`**: new token (service account `terraform` / Synthetic Monitoring config) → update the GitHub secret → Actions → Grafana → Run workflow (plan) passes → delete the old token.

**`PG_MONITOR_PASSWORD`**: put a new value in SSM, then on the instance:

```bash
sudo -i; cd /opt/brand-clothing
set -a; source <(grep -E '^(POSTGRES_USER|POSTGRES_DB)=' .env); set +a
PW=$(aws ssm get-parameter --region eu-central-1 --with-decryption --name /brand-clothing/<env>/secrets/PG_MONITOR_PASSWORD --query Parameter.Value --output text)
docker exec brand_clothing_db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "ALTER ROLE monitor PASSWORD '$PW'"
unset PW
```

Then redeploy (Alloy picks it up). `pg_up` is 0 in between, harmless.

**`POSTGRES_PASSWORD`** (short app downtime): the database keeps its own copy, so change both:
put the new value in SSM, then on the instance set it in Postgres the same way as above
(`ALTER ROLE "$POSTGRES_USER" PASSWORD '$PW'`), then redeploy right away. Requests fail
between the `ALTER` and the redeploy (~1 min). Never only one side.

## Log

| Date | Env | Rotated |
|---|---|---|
| 2026-10-17 | staging, prod | `SECRET_KEY`, `GRAFANA_CLOUD_TOKEN` (new Alloy token `alloy-2026-10`) |
| 2026-10-22 | staging, prod | `NOVA_POSHTA_API_KEY` added (Nova Poshta branch sync) |
| 2026-10-26 | staging | `WAYFORPAY_SECRET_KEY` added: public TEST merchant `test_merch_n1` (no real money) |

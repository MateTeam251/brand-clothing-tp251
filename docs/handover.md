# Handover (DevOps)

Start here if you take over the infrastructure. Everything below is about running it;
how it is built is in [infrastructure.md](infrastructure.md).

_Written 2026-10-19 by Max (DevOps), updated 2026-11-11 (v0.6.0). Lines marked **TODO** need an answer before the handover._

For the shop owner (plain language): [owner-guide.md](owner-guide.md).

## The system

Diagram: [devops-overview.md → Architecture](devops-overview.md#2-architecture).

| Part | What it does |
|---|---|
| CloudFront | `theart-theartist.com` (+ `www`) and `staging.theart-theartist.com`. `/` → S3 frontend (React build), `/api/*` + `/static/*` → the server (`origin.` name) |
| EC2 (Auto Scaling group of 1) | prod t4g.small, staging t4g.micro (08:00–20:00 Kyiv). Docker Compose, below |
| nginx | TLS for the origin name, rate limits, only reachable from CloudFront |
| web | Django + gunicorn (2 workers) |
| db | Postgres 16 + WAL-G → S3 backups |
| redis + celery | background jobs: emails, abandoned carts, Nova Poshta branches sync, weekly analyst reports (prod). Redis is also the cache for API rate limits |
| certbot | renews the origin certificate |
| alloy | metrics + logs → Grafana Cloud |
| S3 | frontend, media (photos, served and cached via CloudFront `/media/*`), backups, reports |

AWS account `875476618056`, region `eu-central-1` (CloudFront certificates: `us-east-1`).

## Docs

| Doc | When you need it |
|---|---|
| [infrastructure.md](infrastructure.md) | What exists in AWS, which Terraform module owns it |
| [releasing.md](releasing.md) | Releasing, rolling back, branch rules |
| [ci-cd.md](ci-cd.md) | What each GitHub Actions workflow does |
| [owner-guide.md](owner-guide.md) | Explaining the system to the shop owner |
| [alerts.md](alerts.md) | An alert arrived (Slack `#alerts` / email): one runbook per alert |
| [database-restore.md](database-restore.md) | Monthly restore drill, real restore |
| [secrets.md](secrets.md) | Where every secret lives, how to rotate it |
| [../infra/grafana/README.md](../infra/grafana/README.md) | Grafana as Terraform, dashboards generator |
| [../loadtest/README.md](../loadtest/README.md) | k6 load test and results |

## First day: access

| What | How to get it | Notes |
|---|---|---|
| AWS console + CLI | IAM user in group `Admins`, created by hand by an existing admin. Turn on MFA, create one access key, profile `brand-clothing` | Never use root. Key rotation ~90 days |
| GitHub `MateTeam251` | Org owner adds you, admin on the repo | Approves `production` / `infra-production` deploys |
| Grafana Cloud | Invite from the stack owner (the customer) | Moving to the customer's account (2026-11): stack name, `GRAFANA_URL`, tokens change, users are re-invited. Checklist below |
| Resend (email) | Invite from the account owner (the customer) | Moving to the customer's account (2026-11), new `secrets/EMAIL_HOST_PASSWORD` |
| AWS account | Owned by the customer (2026-11) | Root and billing: customer. Admins: IAM users as above |
| WayForPay | Customer's merchant account | Prod keys: Merchant login → `WAYFORPAY_MERCHANT_ACCOUNT` (`app-config.tf`), Secret Key → `secrets/WAYFORPAY_SECRET_KEY`. Staging uses the public test merchant `test_merch_n1` |
| Slack `#alerts` | Invite to the workspace | Grafana posts there via an incoming webhook (GitHub secret `GRAFANA_SLACK_WEBHOOK_URL`). **TODO:** check who owns the workspace |
| Google Analytics | Invite to the property | Measurement IDs are GitHub Environment variables `VITE_GA_MEASUREMENT_ID`. **TODO:** check who owns the property |
| Domain `theart-theartist.com` | GoDaddy account of the customer (Daria) | DNS itself is in Route 53, GoDaddy only holds the nameservers. Renews 2027-10-03 |
| Alert emails | Grafana contact point (with Slack) + AWS Budget + SES SNS topic | Address in GitHub secret `TF_BUDGET_ALERT_EMAIL` and the SNS subscription |

Tools: AWS CLI v2 + Session Manager plugin, Terraform ≥ 1.10, Python 3 (dashboards generator), k6 (optional).
Shell on a server: see the top of [alerts.md](alerts.md) (SSM Session Manager, no SSH).

Who else has access:
- **Backend devs**: IAM group `devs`, console only, view-only + shell on the app instance (tag `SessionAccess=developers`), MFA forced, no keys.
- **Analysts**: IAM group `Analysts`, can only download `reports/carts/` from the reports bucket.
- IAM users and groups are **manual** (not in Terraform).

## Routines

| When | What | Where |
|---|---|---|
| When it arrives | Alert in Slack `#alerts` (and email) → follow the runbook | [alerts.md](alerts.md) |
| Each release | Watch Actions → Release, then Grafana Overview (release marker, 5xx, p95) | [releasing.md](releasing.md) |
| Monthly | Review/merge Dependabot PRs (grouped; no major Docker bumps) | GitHub |
| Monthly | Restore drill (~15 min), add a row to "Last drills" | [database-restore.md](database-restore.md) |
| Monthly | AMI check issue (opened by `ami-check.yml`) → bump `ami_id` PR | `infra/environments/*/` |
| Monthly | AWS Billing: spend vs the $30 budget | AWS console → Billing |
| Monthly | Grafana Cloud usage (Free plan limits, below) | Grafana → Administration → Usage |
| Yearly | Rotate secrets marked "yearly" | [secrets.md](secrets.md) |
| Yearly | Domain renewal (2027-10-03, auto-renew on GoDaddy) | Customer |
| Automatic | Origin certificates renew (certbot, every 12 h check); expiry alert fires if not | `prod cert` alert |

## Numbers worth knowing

| | |
|---|---|
| Budget | $30/month (prod ~$22, staging ~$8). AWS Budget emails at 80% forecast / 100% actual |
| Capacity | Load test 2026-10-17: 100 browsing shoppers on staging, p95 162 ms, 0 errors, CPU 37%. No limit found |
| Deploy | ~3 s of 502s while `web` restarts |
| Backups | Base backup nightly 03:00 UTC, WAL at least every 5 min → max data loss ~5 min |
| Grafana Free | 10k metric series (using ~600), 50 GB logs/month (~6 MB/day), **100k synthetic checks/month (~60k, tightest)**, 3 users, 14 days retention |
| Email | Resend Free: 3,000/month, **100/day** (nginx rate limits protect it) |

## Known risks and open items

- **Shell = data access.** Anyone with Session Manager on the app instance can reach Postgres and the env vars (sudo → Docker). Accepted for a small team; options: no sudo for `ssm-user`, session logging to S3.
- **Account moves.** AWS, Grafana Cloud, WayForPay and Resend are being moved to the customer (2026-11) → checklist.
- **SES.** Production access was rejected 2026-10-11. Re-apply early November 2026, then switch back from Resend (`EMAIL_BACKEND=django_ses.SESBackend`). Domain identity, DKIM, DMARC are already in `prod/email.tf`.
- **Payments.** Staging runs on the WayForPay test merchant; prod waits for the customer's merchant keys. Payments logs are deliberately **not** sent to Grafana.
- **Celery Beat schedule is in memory**: a task due while celery restarts is skipped until its next slot (hourly/daily tasks, acceptable).
- **`/api/admin/`** is reachable from anywhere (rate-limited login only). Extra protection planned with the backend devs.
- **IAM as code.** Groups and policies are manual; codify in Terraform when convenient (users/passwords stay manual).
- **TODO:** anything else Max knows of.

## Handover checklist

- [ ] New DevOps has every access from "First day" and has done one release and one restore drill.
- [ ] Grafana: create the customer's stack, apply `infra/grafana` there, update `GRAFANA_AUTH` / `GRAFANA_SM_ACCESS_TOKEN`, new Alloy token in SSM `secrets/GRAFANA_CLOUD_TOKEN` (both envs) → redeploy, repo variable `GRAFANA_URL` (release markers), re-invite users (Free plan: 3). Steps: [../infra/grafana/README.md](../infra/grafana/README.md).
- [ ] Resend: move to a customer account (or SES, if approved), new `secrets/EMAIL_HOST_PASSWORD`.
- [ ] Alert email (`TF_BUDGET_ALERT_EMAIL`, AWS Budget, SNS subscription) → new owner's address.
- [ ] Slack: workspace owner confirmed; if the webhook changes, update `GRAFANA_SLACK_WEBHOOK_URL` and re-run the Grafana workflow on `main`.
- [ ] WayForPay prod: merchant login in `prod/app-config.tf` (PR), Secret Key in SSM `secrets/WAYFORPAY_SECRET_KEY` → release, one real test payment.
- [ ] Rotate every secret marked "on handover" in [secrets.md](secrets.md) (incl. `POSTGRES_PASSWORD`), log it there.
- [ ] Max's IAM user: delete access key, then the user. Remove Max from GitHub org admins.
- [ ] AWS root: MFA device and password with the customer. **TODO:** who holds it.
- [ ] GoDaddy: customer changed the password Max used, registrant email verified, auto-renew on.

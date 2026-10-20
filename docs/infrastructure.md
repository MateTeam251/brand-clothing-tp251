# Infrastructure inventory

What runs today. All in AWS account `875476618056`, region `eu-central-1` (CloudFront certificates in `us-east-1`),
managed by Terraform in `infra/` unless marked *manual*. Day-to-day running: [handover.md](handover.md).
Budget: ~$30/month for everything.

_Last updated: 2026-10-19_

## Environments

| | Production | Staging |
|---|---|---|
| URL | https://theart-theartist.com (+ `www.`) | https://staging.theart-theartist.com |
| Terraform | `infra/environments/prod` | `infra/environments/staging` |
| Deploys from | `main` | `develop` |
| Instance | t4g.small (2 GB), always on | t4g.micro (1 GB), daily 08:00–20:00 Kyiv |
| Public IP (EIP) | `3.73.249.226` | `18.194.165.37` |
| Origin name (CloudFront → server) | `origin.theart-theartist.com` | `origin-staging.theart-theartist.com` |
| CloudFront | `d1sjix7eute2eg.cloudfront.net` | `d1iq6r8ypyqu9.cloudfront.net` |
| VPC | own VPC, 1 public subnet | own VPC `10.1.0.0/16`, 1 public subnet |
| SSM path | `/brand-clothing/prod` | `/brand-clothing/staging` |
| Est. cost | ~$22/month | ~$8/month |

Both environments are built from the same modules and share the ECR images and the Route 53 zone.

## Request path

Diagram: [devops-overview.md → Architecture](devops-overview.md#2-architecture).

| Path | CloudFront sends it to | Caching |
|---|---|---|
| `/` (everything else) | S3 frontend bucket (SPA rewrite function → `index.html`) | yes |
| `/api/*`, `/static/*` | `https://origin.<domain>` → nginx → web → db | no |
| `/media/*` | S3 media bucket. CloudFront function `media-strip-prefix` drops `/media` (files are stored at the bucket root) | yes, up to 1 year (`Managed-CachingOptimized`; a new upload always gets a new file name) |

CloudFront sends the origin name as `Host`, so Django's `ALLOWED_HOSTS` contains the origin name.

## Compute (`modules/compute`)

| Resource | Details |
|---|---|
| Auto Scaling group | 1 instance; self-heals; replaced via instance refresh |
| Launch template | Amazon Linux 2023 arm64, AMI pinned (`ami_id`, bumped by PR after the monthly `ami-check.yml` issue), user data (gzip) installs Docker + Compose and writes `deploy.sh`. Tag `SessionAccess=developers` |
| Root volume | gp3, encrypted, 16 GB prod / 12 GB staging |
| Data volume | gp3, encrypted, 20 GB prod / 10 GB staging, mounted at `/data` (Postgres data, certificates, app logs). `prevent_destroy` |
| Elastic IP | re-attached on every boot. `prevent_destroy` |
| Swap | 1 GB swapfile |
| IAM role | SSM Session Manager, S3 media, backups and reports buckets, attach own data volume + EIP, read own SSM path, ECR pull, SES send, Route 53 TXT for `_acme-challenge.<origin>` only |
| Schedule | staging only: ASG scheduled actions start/stop |

Containers (`docker-compose.prod.yml`, memory limits in brackets):

| Container | What |
|---|---|
| `nginx` (64m) | port 443 (reachable from CloudFront only), TLS with the origin certificate, rate limits (login 10/min, register/password reset 3/min, checkout 10/min), 150 MB uploads on `/api/admin/` |
| `web` (768m) | Django + gunicorn (2 workers, timeout 60), WhiteNoise for static, runs migrations on start. DB connections reused (`CONN_MAX_AGE=60`) |
| `db` (768m) | Postgres 16 + WAL-G (custom image `db/`): base backup nightly 03:00 UTC, WAL at least every 5 min (`archive_timeout`) |
| `redis` (64m) | Celery broker only, no persistence |
| `celery` (256m) | one worker with beat: emails, weekly analyst reports (Monday) |
| `certbot` (128m) | Let's Encrypt certificate for the origin name (DNS-01 via Route 53), checks every 12 h, stored in `/data/letsencrypt` |
| `alloy` (256m) | Grafana agent: host + container (cAdvisor) + Postgres metrics, logs of web/nginx/db/celery (payments logger dropped), TLS expiry probe of nginx |

## Network (`modules/network`)

| Resource | Details |
|---|---|
| VPC + public subnet + internet gateway | no NAT gateway, no private subnets |
| Security group `app` | in: 443 from CloudFront only (AWS managed prefix list), nothing else. **No SSH** — access via SSM Session Manager |

## DNS, certificates, email (`environments/*/dns.tf`, `prod/email.tf`)

| Resource | Details |
|---|---|
| Route 53 zone `theart-theartist.com` | in prod Terraform, `prevent_destroy`. Domain registered at GoDaddy (customer), nameservers point to Route 53 |
| Records | apex + `www` A/AAAA alias → prod CloudFront; `staging.` → staging CloudFront; `origin.` / `origin-staging.` A → EIPs |
| ACM certificates (`us-east-1`) | CloudFront: apex + `www` (prod), `staging.` (staging). DNS-validated, renew automatically |
| SES | domain identity with DKIM, MAIL FROM `mail.`, DMARC `p=none`; configuration set `brand-clothing-transactional` → SNS `brand-clothing-email-alerts` + CloudWatch alarms (bounce > 3%, complaint > 0.05%). **Sandbox** (production access rejected 2026-10-11, re-apply November) |
| Resend (used now) | DKIM / `send` / `rsend` records in `prod/email.tf`. SMTP `smtp.resend.com:587`, key in `secrets/EMAIL_HOST_PASSWORD`. Account *manual* |

## Storage (`modules/storage`)

| Bucket (`<name>-875476618056`) | Use | Notes |
|---|---|---|
| `brand-clothing[-staging]-media` | uploaded product images (WebP) | private, read by CloudFront only. Django links `https://<site>/media/...` (SSM `AWS_S3_CUSTOM_DOMAIN`; unset = signed S3 links). Versioned: old versions deleted after 30 days. `prevent_destroy` |
| `brand-clothing[-staging]-frontend-static` | React build | private, served via CloudFront (default) |
| `brand-clothing[-staging]-db-backups-wal` | WAL-G backups | versioned, Glacier after 90 days, app can only write. `prevent_destroy` |
| `brand-clothing[-staging]-reports` | weekly analyst CSVs (`reports/carts/<week>/`) | private, deleted after 1 year. Analysts read via IAM group `Analysts` |

CloudFront: one distribution per environment, custom domain + ACM certificate, origin access control to S3,
security headers policy.

## Container images (`modules/ecr`, prod only)

| Repository | Tag | Retention |
|---|---|---|
| `brand-clothing-backend` | commit SHA | last 20 images, immutable tags, scan on push |
| `brand-clothing-db` | git hash of `db/` | same |

## App configuration (SSM Parameter Store)

| What | Where | Managed by |
|---|---|---|
| Non-secret config (`DEBUG`, `ALLOWED_HOSTS`, bucket names, …) | `/brand-clothing/<env>/NAME` | Terraform: `environments/<env>/app-config.tf` |
| `IMAGE_TAG`, `DB_IMAGE_TAG` | `/brand-clothing/<env>/` | release pipeline |
| Secrets | `/brand-clothing/<env>/secrets/NAME` (SecureString) | *manual*, see [secrets.md](secrets.md) |

`deploy.sh` turns everything under the path into `.env` on every boot and deploy.

## CI/CD access (IAM, OIDC)

| Role | Used by | Can |
|---|---|---|
| `brand-clothing-github-actions-ecr-push` | release build (`develop`, `main`) | push to ECR |
| `brand-clothing-staging-github-deploy` | release deploy, GitHub Environment `staging` | set image tags, run `deploy.sh` on staging |
| `brand-clothing-github-deploy-prod` | release deploy, GitHub Environment `production` | same, prod |
| `brand-clothing-terraform-plan` | `terraform.yml` PR plans | read-only, no secrets |
| `brand-clothing-terraform-apply-{staging,production}` | `terraform.yml` applies, `infra-*` Environments | apply, with guardrails (no secrets, no state deletion, no human IAM) |

GitHub OIDC provider: account-wide, in `environments/prod`. No AWS access keys in GitHub.

## Terraform state (`infra/bootstrap`, local state)

| Resource | Name |
|---|---|
| S3 state bucket | `brand-clothing-tfstate-875476618056-eu` (versioned, encrypted). Keys: staging, prod, `grafana/terraform.tfstate` |
| State lock | `<key>.tflock` file next to each state (`use_lockfile`, Terraform ≥ 1.10) |

## Monitoring (`infra/grafana`)

Grafana Cloud stack `sturdyscone1696` (Free plan), managed by Terraform, applied from `main`:
10 alert rules (runbooks in [alerts.md](alerts.md)), email contact point, 2 synthetic checks (admin login, frontend),
5 dashboards (Overview, Requests, Infrastructure, Database, Logs) with release markers. Details: `infra/grafana/README.md`.
Alloy push token: `secrets/GRAFANA_CLOUD_TOKEN`.

## Account-level

| Resource | Details |
|---|---|
| AWS Budget | `brand-clothing-monthly-cap`, $30: email at 80% forecast and 100% actual |
| IAM users / groups | *manual*: `Admins`, `Developers` (view-only + shell), `Analysts` (reports only). See [handover.md](handover.md) |
| Audit | CloudTrail event history (90 days, default). No persistent trail |

## Not in use yet

SES production sending, WayForPay (keys pending), frontend monitoring (Faro).

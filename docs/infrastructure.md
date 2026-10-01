# Infrastructure inventory

What runs today. All in AWS account `875476618056`, region `eu-central-1`, managed by Terraform in `infra/` unless marked *manual*.
Budget: ~$30/month for everything.

_Last updated: 2026-10-01_

## Environments

| | Production | Staging |
|---|---|---|
| Terraform | `infra/environments/prod` | `infra/environments/staging` |
| Deploys from | `main` | `develop` |
| Instance | t4g.small (2 GB), always on | t4g.micro (1 GB), Mon–Fri 08:00–20:00 Kyiv |
| Public IP (EIP) | `3.73.249.226` | `18.194.165.37` |
| CloudFront | `d1sjix7eute2eg.cloudfront.net` | `d1iq6r8ypyqu9.cloudfront.net` |
| VPC | own VPC, 1 public subnet | own VPC `10.1.0.0/16`, 1 public subnet |
| SSM path | `/brand-clothing/prod` | `/brand-clothing/staging` |
| Est. cost | ~$22/month | ~$8/month |

Both environments are built from the same modules and share only the ECR images.

## Compute (`modules/compute`)

| Resource | Details |
|---|---|
| Auto Scaling group | 1 instance; self-heals; replaced via instance refresh |
| Launch template | Amazon Linux 2023 arm64, AMI pinned (`ami_id`, bumped by PR), user-data installs Docker + Compose and writes `deploy.sh` |
| Root volume | gp3, encrypted, 16 GB prod / 12 GB staging |
| Data volume | gp3, encrypted, 20 GB prod / 10 GB staging, mounted at `/data` (Postgres data, app logs). `prevent_destroy` |
| Elastic IP | re-attached on every boot. `prevent_destroy` |
| Swap | 1 GB swapfile |
| IAM role | instance role: SSM Session Manager, S3 media/backups, read own SSM path, ECR pull |
| Schedule | staging only: ASG scheduled actions start/stop |

On the instance (`docker-compose.prod.yml`): **nginx** (public, port 80) → **web** (Django + gunicorn, WhiteNoise for static) → **db** (Postgres 16 + WAL-G, custom image).

## Network (`modules/network`)

| Resource | Details |
|---|---|
| VPC + public subnet + internet gateway | no NAT gateway, no private subnets |
| Security group `app` | in: 80, 443 from anywhere (IPv4/IPv6). **No SSH** — access via SSM Session Manager |

## Storage (`modules/storage`)

| Bucket (`<name>-875476618056`) | Use | Notes |
|---|---|---|
| `brand-clothing[-staging]-media` | uploaded product images | private, served via CloudFront `/media/*`. `prevent_destroy` |
| `brand-clothing[-staging]-frontend-static` | React build | private, served via CloudFront (default) |
| `brand-clothing[-staging]-db-backups-wal` | WAL-G backups | versioned, Glacier after 90 days, app can only write. `prevent_destroy` |

CloudFront: one distribution per environment, default `*.cloudfront.net` certificate (no custom domain yet), origin access control to S3.

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
| Secrets (`SECRET_KEY`, `POSTGRES_PASSWORD`) | `/brand-clothing/<env>/secrets/NAME` (SecureString) | *manual* (AWS CLI) |

`deploy.sh` turns everything under the path into `.env` on each deploy.

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
| S3 state bucket | `brand-clothing-tfstate-875476618056-eu` (versioned, encrypted) |
| DynamoDB lock table | `brand-clothing-terraform-lock` |
| CI roles | see above |

## Account-level

| Resource | Details |
|---|---|
| AWS Budget | `brand-clothing-monthly-cap`, $30: email at 80% forecast and 100% actual |
| IAM users / groups | *manual* |
| Monitoring | Grafana Cloud free tier (planned, not set up yet) |

## Not in use yet

Domain + Route 53, HTTPS certificate, SES email (console backend for now), Redis + Celery, Grafana Cloud agent.

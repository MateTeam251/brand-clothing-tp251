# Releasing

How code gets to staging and production, how to roll back, and the rules that keep it working.

| Branch | Deploys to | When |
|---|---|---|
| `develop` | staging | automatically, on every merge |
| `main` | production | automatically, on every merge (= a release) |

Both run the same `Release` workflow (`.github/workflows/release.yml`):
**test → build images → deploy → smoke check**.

## Doing a release

1. Check that `develop` is green and staging works (`/api/admin/login/` loads, the feature you're shipping works).
2. Open a PR **`develop` → `main`**. Title: `Release vX.Y.Z` (or a short summary).
3. Merge with **"Create a merge commit"**. Never squash, never rebase (see Rules).
4. Watch **Actions → Release**. The deploy job's summary shows the image tag and the result.
5. Optional: **Releases → Draft a new release**, tag `vX.Y.Z` on `main`, **Generate release notes**.

If tests or the build fail, nothing is deployed and production keeps the previous version. If the deploy or smoke check fails, roll back (below).

## Rolling back

Redeploy images that are already in ECR — no rebuild, no git changes:

1. Find the last good commit SHA: Actions → Release → the last successful run on `main` → summary → *Image tag*.
2. **Actions → Release → Run workflow**, branch **`main`** (production only accepts `main`),
   `environment: production`, `image_tag:` the full 40-character SHA.

Same for staging with branch `develop` and `environment: staging`.

Then fix forward: fix on `develop`, release again.

**Database migrations don't roll back.** The old code runs against the new schema. Keep migrations backwards compatible (add columns/tables first, remove them in a later release).

## Before a release

- **New environment variables** go into `infra/environments/<env>/app-config.tf` (non-secret) or SSM `/brand-clothing/<env>/secrets/` (secret) **before** the release that needs them. Apply, then release.
- **Migrations**: they run automatically when the `web` container starts. Check the PR for destructive ones (dropped columns, renamed fields).
- **Infra changes** (Terraform) are applied separately, not by this workflow.

## Rules

- **Merge commits only into `main`.** A squash creates a new commit that `develop` doesn't have, and the next release PR conflicts with itself.
- **Never commit or revert directly on `main`.** A revert on `main` is remembered by git: the next `develop` → `main` merge silently deletes the reverted code again. To undo a release, use the rollback above.
- **Hotfix**: branch from `develop`, PR into `develop`, check on staging, then release as usual.
- Only one deploy per environment runs at a time; a second one waits.

## What runs where

- Images: ECR `brand-clothing-backend` (tag = commit SHA) and `brand-clothing-db` (tag = hash of `db/`, rebuilt only when `db/` changes). Staging and production use the same images.
- Deploy: GitHub writes `IMAGE_TAG` / `DB_IMAGE_TAG` to SSM and runs `/opt/brand-clothing/deploy.sh` on the instance via SSM Run Command. `deploy.sh` builds `.env` from SSM, pulls the images and restarts the containers.
- Access: GitHub uses OIDC roles, one per environment, usable only from jobs in that GitHub Environment (`staging` → `develop`, `production` → `main`). No AWS keys in GitHub.

## Versions

`vMAJOR.MINOR.PATCH`: a new **minor** for features or infrastructure that changes how the site works, a **patch** for fixes, ops and docs. Tag every release on `main`. Add a row here on the branch that goes into the release.

| Version | Date | What changed |
|---|---|---|
| v0.4.4 | 2026-10-08 | Secure cookies, full Python tracebacks in Grafana (payments errors dropped whole), GitHub Actions on Node 24 |
| v0.4.3 | 2026-10-07 | Media bucket private (signed URLs), TLS-only buckets, account-wide S3 Block Public Access, CloudFront security headers (HSTS), backup versions expire after 1 year, provider lock files |
| v0.4.2 | 2026-10-07 | Server accepts HTTPS from CloudFront only (security group) |
| v0.4.1 | 2026-10-07 | nginx resolves `web` per request (502 after a redeploy) |
| v0.4.0 | 2026-10-07 | Production on theart-theartist.com: ACM certificates, Let's Encrypt origin (certbot), frontend deploy to S3/CloudFront, staging on staging.theart-theartist.com, README + license |
| v0.3.1 | 2026-10-03 | Route 53 zone for theart-theartist.com, Grafana alerts resumed |
| v0.3.0 | 2026-10-03 | Weekly cart report (Celery + Redis on prod), reports bucket, backup cron PATH fix, restore runbook, staging every day, less log noise |
| v0.2.1 | 2026-10-02 | nginx JSON access logs, WAL-G backup logging, Grafana export |
| v0.2.0 | 2026-10-01 | Monitoring (Grafana Cloud, Alloy), Terraform CI (plan on PR, apply on merge), gunicorn fix |
| v0.1.0 | 2026-10-01 | First release: staging + production, release pipeline (test → build → deploy → smoke check), SSM config and secrets |

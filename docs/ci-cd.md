# CI/CD

Two kinds of workflows: **checks** on pull requests, and the **release** pipeline on `develop` / `main`.
Release and rollback steps: [releasing.md](releasing.md).

## Workflows

| File | Runs on | What it does |
|---|---|---|
| `backend-ci.yml` | PR into `develop`/`main` (every PR, no path filter); called by `release.yml` | `manage.py check`, missing-migrations check, `pytest` with coverage report. Postgres + Redis service containers; Python version read from `Dockerfile.prod` (same as production) |
| `frontend-ci.yml` | PR into `develop`/`main`; push to `develop`/`main` touching `apps/frontend/**` | `npm run lint`, `npm run build` (includes type-check) |
| `docker-build.yml` | PR touching `apps/backend/**` or `db/**` | Builds the production images (arm64), no push |
| `release.yml` | Push (merge) to `develop` or `main`; manual | Test → build & push images → deploy backend → smoke check → Grafana release marker → build & deploy frontend |
| `terraform.yml` | PR / push touching `infra/environments/**`, `infra/modules/**`, `docker-compose.prod.yml`, `nginx/**`; manual | PR: fmt, validate, plan for staging + prod as a PR comment. Merge to `develop`: apply staging. Merge to `main`: apply prod after approval. Then instance refresh if the launch template changed |
| `grafana.yml` | PR / push touching `infra/grafana/**`; manual | PR: plan as a PR comment. Merge to `main`: apply (alerts, contact point, synthetic checks, dashboards) after approval in `infra-production` |
| `main-source.yml` | PR into `main` | Required check: PRs into `main` must come from `develop` |
| `ami-check.yml` | 1st of the month 07:00 UTC; manual | Opens an issue when a newer Amazon Linux 2023 AMI exists than the pinned `ami_id` |

**Dependabot** (`.github/dependabot.yml`): monthly, one grouped PR per ecosystem (pip, npm, Docker base images, compose images, Actions); no major Docker bumps; security fixes arrive as separate PRs right away.

All of them can also be started by hand: **Actions → workflow → Run workflow**.

## Release pipeline

```
merge to develop ──► test ──► build ──► deploy staging    ──► smoke check ──► frontend staging
merge to main    ──► test ──► build ──► deploy production ──► smoke check ──► frontend production
```

- **test**: the same `backend-ci.yml` as on PRs, on the merged code.
- **build**: arm64 images pushed to ECR. `brand-clothing-backend` is tagged with the commit SHA; `brand-clothing-db` with the git hash of `db/` and only rebuilt when `db/` changes.
- **deploy**: writes `IMAGE_TAG` / `DB_IMAGE_TAG` to SSM and runs `deploy.sh` on the instance via SSM Run Command (no SSH). The job's log shows the full `deploy.sh` output.
- **smoke check**: `/api/admin/login/` and its CSS must return 200 within 60 s.
- **Grafana marker**: a `release` annotation on all dashboards (needs repo variable `GRAFANA_URL`; failure does not fail the release).
- **frontend**: `npm run build` with `VITE_GA_MEASUREMENT_ID` from the environment, sync to the frontend bucket (`assets/` cached 1 year, the rest `no-cache`), CloudFront invalidation, then `/` and `/catalog` must return the app. Skipped with a notice if the environment has no `FRONTEND_BUCKET`.
- **Manual run** (rollback / redeploy, also after changing SSM config): pick `environment` and an existing `image_tag`; test, build and frontend are skipped.

Staging runs every day 08:00–20:00 Kyiv time. A deploy outside those hours is skipped with a warning, not an error: `IMAGE_TAG` is already updated, so the instance starts the new version on its next boot.

## Terraform pipeline

- **PR**: the read-only plan role plans both environments; each plan is one PR comment, updated on every push. Review it like code: it's exactly what will change in AWS.
- **Merge**: `develop` → apply staging (GitHub Environment `infra-staging`), `main` → apply prod (`infra-production`, needs approval). Apply roles can't read app secrets, touch the CI roles or human IAM.
- **Instance refresh**: if the running instance is on an older launch template version (user-data, compose, nginx or AMI changed), the workflow replaces it and waits for `/api/admin/login/` → 200. Staging outside working hours: skipped, the next boot uses the new version.
- Applies and app deploys share a concurrency group per environment, so they never run on the same instance at once.
- `infra/bootstrap` (state bucket, CI roles) is applied by hand only, never by CI.
- AMI is pinned (`ami_id` in each environment's `main.tf`); bump it by PR. `ami-check.yml` checks monthly and opens an issue when a newer Amazon Linux AMI exists.

## Run naming

- Checks: `<actor> - <branch> - <commit SHA>`
- Release: `Release <branch> - <SHA>`; manual: `Deploy <SHA> to <environment> (<actor>)`

## Concurrency

- Checks: a new push to the same branch/PR cancels the running check. Runs on `develop` and `main` always complete.
- Deploys: one per environment at a time. A second deploy waits; a running deploy is never cancelled.

## Access and secrets

- **No AWS keys in GitHub.** Workflows get short-lived credentials via OIDC:
  - ECR push role: only from `develop` / `main`.
  - Deploy roles: one per environment, only from jobs in the GitHub Environment `staging` (branch `develop`) or `production` (branch `main`).
- GitHub Environment variables (`staging`, `production`): `AWS_DEPLOY_ROLE_ARN`, `APP_ROLE_TAG`, `APP_URL`, `FRONTEND_BUCKET`, `CLOUDFRONT_DISTRIBUTION_ID`, `FRONTEND_URL`, `VITE_GA_MEASUREMENT_ID`. Repo variables: `AWS_REGION`, `AWS_ECR_PUSH_ROLE_ARN`, `TF_PLAN_ROLE_ARN`, `GRAFANA_URL`. Secrets: [secrets.md](secrets.md).
- App configuration lives in SSM Parameter Store (`/brand-clothing/<env>/`), managed in `infra/environments/<env>/app-config.tf`. Secrets are under `/brand-clothing/<env>/secrets/` and are never in git, Terraform or GitHub.
- Backend CI uses dummy `SECRET_KEY` / Postgres credentials for its throwaway test database. `payments` tests override `WAYFORPAY_*` via `override_settings` — no real credentials involved.

## Merge rules

- Branch protection ruleset on `develop` and `main`: PR required, required checks **Backend tests** and **Frontend lint & build** (+ **Main source branch** on `main`).
- PRs into `develop`; releases are PRs `develop` → `main`, **merge commit only** (see [releasing.md](releasing.md#rules)).
- No coverage gate: `pytest` fails only on a failing test, not on missing coverage.

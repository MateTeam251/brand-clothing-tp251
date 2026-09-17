# CI Pipeline

## Workflows

| File | Triggers on | Runs |
|---|---|---|
| `backend-ci.yml` | `apps/backend/**` | `manage.py check`, migration check, `pytest` |
| `frontend-ci.yml` | `apps/frontend/**` | `npm run lint`, `npm run build` |
| `docker-build.yml` | `apps/backend/**` | Docker image build (no push) |

## Triggers

- Push to `main` or `develop`
- Pull request into `main` or `develop`
- Manual: **Run workflow** button in the Actions tab (ignores path filters, runs on any branch)

## Run naming

`<actor> - <branch> - <commit SHA>`

## Concurrency

New push to the same branch cancels that branch's in-progress run. `main` and `develop` runs always complete.

## Merge status

Not enforced yet — branch protection isn't configured, so a red check doesn't currently block a merge.

No coverage gate. `pytest` fails only on a failing test, not on missing coverage.

## Secrets

Backend job uses dummy `SECRET_KEY`/Postgres credentials, scoped to the CI database only. `payments` tests override `WAYFORPAY_*` via `override_settings` — no real credentials involved.

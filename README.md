# The Art — The Artist

Online clothing store: Django REST backend + React frontend, running on AWS.

| | |
|---|---|
| Production | https://theart-theartist.com |
| Staging | https://staging.theart-theartist.com |

## Stack

- **Backend:** Django + Django REST Framework, PostgreSQL, Celery + Redis (background jobs), WayForPay payments
- **Frontend:** React, TypeScript, Vite, Redux Toolkit
- **Infrastructure:** AWS (EC2, S3, CloudFront, Route 53, ECR, SSM), Terraform, Docker Compose, GitHub Actions
- **Monitoring:** Grafana Cloud (metrics, logs, alerts), WAL-G backups to S3

## Repository

```
apps/backend/      Django project (API, admin, Celery tasks)
apps/frontend/     React app
db/                Postgres image with WAL-G backups
nginx/             nginx config for the servers
infra/             Terraform (bootstrap, modules, staging + prod environments), Grafana exports
docs/              CI/CD, releasing, infrastructure, database restore
docker-compose.prod.yml   what runs on the servers
```

## Local development

**Backend** (Postgres, Redis, Celery, MailHog and LocalStack included):

```bash
cd apps/backend
cp .env.example .env
docker compose -f docker-compose.dev.yml up --build
```

API on http://127.0.0.1:8000/api/, admin on http://127.0.0.1:8000/api/admin/
(create a user with `docker compose -f docker-compose.dev.yml exec web python manage.py createsuperuser`),
emails in MailHog on http://127.0.0.1:8025.

**Frontend:**

```bash
cd apps/frontend
echo VITE_API_URL=http://127.0.0.1:8000/api/ > .env.local
npm install
npm run dev
```

## Branches and deploys

- Work in a feature branch, open a PR into `develop`. Backend tests and frontend lint/build must pass.
- Merge into `develop` deploys to **staging** automatically.
- A PR `develop` → `main` (merge commit, never squash) is a **production release**.

Details: [docs/releasing.md](docs/releasing.md), [docs/ci-cd.md](docs/ci-cd.md),
[docs/infrastructure.md](docs/infrastructure.md), [docs/database-restore.md](docs/database-restore.md).

## License

[MIT](LICENSE)

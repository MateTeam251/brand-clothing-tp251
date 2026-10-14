# Alert runbooks

One section per Grafana alert (folder `brand-clothing`). Each alert's **Runbook URL** points here.
Rule definitions: `infra/grafana/alerts/brand-clothing.yml`.

**Shell on prod** (needed by most sections):

```powershell
$id = aws autoscaling describe-auto-scaling-groups --profile brand-clothing --query "AutoScalingGroups[?contains(AutoScalingGroupName,'prod')].Instances[0].InstanceId" --output text
aws ssm start-session --target $id --profile brand-clothing
```

```bash
sudo -i
cd /opt/brand-clothing
docker ps --format '{{.Names}}  {{.Status}}'
```

Logs: Grafana → Dashboards → **Logs** (`env=prod`, pick the container).

---

## prod site down

_Synthetic check `prod-admin-login` failing (`ProbeFailedExecutionsTooHigh`)._

1. Open https://theart-theartist.com/api/admin/login/ yourself. Works → probe glitch, watch for 10 min.
2. CloudFront error page (502/504) → origin problem:
   - `docker ps`: are `nginx` and `web` up? If not: `docker compose up -d`
   - `docker logs --tail 50 brand_clothing_web` / `brand_clothing_nginx`
3. No shell possible (instance gone): EC2 → Auto Scaling groups → prod. The ASG starts a new instance by itself; it reattaches the data volume (~5 min).
4. Right after a release? Roll back: `docs/releasing.md` → Rolling back.

## prod frontend down

_The shop page `https://theart-theartist.com/` failed in more than half of the checks for 10 min (synthetic check `prod-frontend`). The backend can be fine at the same time._

1. Open the site yourself (private window). Blank page or error?
2. CloudFront error (403/404/5xx) → S3 bucket or distribution: last frontend deploy in Actions (Release → `frontend (production)` job), CloudFront → Distributions → status.
3. Page loads but is broken → bad frontend build: redeploy the previous release (`docs/releasing.md` → Rolling back).

## prod 5xx errors

_More than 5 responses with status 500–504 from nginx in 5 min._

1. Logs dashboard → `container=web`: find the traceback.
2. `502/504` only → `web` restarted or was slow: `docker ps` (uptime), memory alert?
3. Bug in a new release → tell the backend dev with the traceback; roll back if it breaks checkout or login.

## prod app errors

_`ERROR`/`CRITICAL` lines from Django, Celery or gunicorn in the last 15 min that didn't become a 500 (those are **prod 5xx errors**), e.g. a failed background job (abandoned carts, weekly report) or a caught exception._

1. Logs dashboard → `container=web` / `celery`, search `ERROR`: read the line and the traceback under it.
2. Celery task failed → it retries on its next schedule; tell the backend dev with the traceback.
3. Same error every few minutes → likely a config problem (missing SSM value, S3 access): check the last release / Terraform change.

## prod not sending metrics

_No metrics from prod for 10 min. Either the instance is down or Alloy stopped._

1. Is the site up? Down → **prod site down**.
2. Site up → Alloy: `docker ps | grep alloy`, `docker logs --tail 30 brand_clothing_alloy`, then `docker compose up -d alloy`.
3. `401/403` in Alloy logs → Grafana token expired/rotated: update `/brand-clothing/prod/secrets/GRAFANA_CLOUD_TOKEN` in SSM, then refresh the instance (or rerun deploy).

## prod disk above 85%

_`/` or `/data` is almost full. Postgres stops writing when `/data` is full._

```bash
df -h / /data
du -xh --max-depth=1 /data | sort -h | tail
docker system df
```

- `/` full → old images: `docker image prune -a -f` (keeps running ones).
- `/data/postgres/pg_wal` large → WAL archiving is stuck, see **prod WAL archiving failing**.
- Real growth → increase `data_volume_size` in Terraform (EBS can grow online; then `xfs_growfs /data`).

## prod memory available below 10%

_Less than ~200 MB free on the 2 GB instance._

```bash
free -m
docker stats --no-stream
```

- One container far above usual (`web`, `celery`) → `docker compose restart <service>`, tell the backend dev (likely a leak or a heavy request).
- Keeps coming back → bigger instance (`instance_type`), or lower `mem_limit`s.

## prod backup failed

_The nightly WAL-G base backup (03:00 UTC) logged `WAL-G backup FAILED`._

1. Logs dashboard → `container=db`, search `WAL-G`: read the error line above `FAILED`.
2. Run it by hand to see it live:
   `docker exec -u postgres brand_clothing_db /usr/local/bin/wal-g-backup.sh`
3. Typical causes: S3 access denied (IAM role changed), disk full, Postgres down.
4. Until fixed, WAL archiving still protects data, but restores get slower. Fix the same day.

## prod backup missing (26h)

_No `WAL-G backup completed` for 26 h: the job didn't run at all (or the db container was down at 03:00)._

1. `docker ps`: is `brand_clothing_db` up, and since when?
2. Run the backup by hand (command above). It must end with `WAL-G backup completed`; the alert clears on the next evaluation.
3. Cron inside the db image: `docker exec brand_clothing_db cat /etc/cron.d/wal-g-backup` (see `db/scripts/crontab`).

## prod WAL archiving failing

_Postgres can't upload WAL to S3. Changes since the last successful upload are not backed up, and `pg_wal` grows until the disk fills._

```bash
docker exec brand_clothing_db psql -U "$(grep ^POSTGRES_USER= .env | cut -d= -f2)" -c "select last_archived_wal, last_archived_time, last_failed_wal, last_failed_time, failed_count from pg_stat_archiver"
docker logs --tail 50 brand_clothing_db 2>&1 | grep -i -A3 archive
```

- `AccessDenied` → IAM role / bucket policy changed (check the last Terraform apply).
- Network/S3 outage → Postgres retries by itself; check that `last_archived_time` moves again.

## Origin certificate expiry

_Let's Encrypt certificate on nginx expires in under 14 days, or nginx serves none (no data). certbot renews at 30 days, so renewal has failed for ~2 weeks._

```bash
docker logs --tail 50 brand_clothing_certbot
ls -l /data/letsencrypt/live/
```

- Route 53 / DNS error → certbot's IAM permission or the `_acme-challenge` record (`infra/modules/compute/iam.tf`).
- Fix, then force a run: `docker compose restart certbot`. nginx picks up the new cert without a reload.
- Expired already → CloudFront returns 502 for the whole site. Fix certbot first; everything else waits.

---

## Not in Grafana

- **SES bounce > 3% / complaint > 0.05%** (CloudWatch → SNS email): stop and check what's being sent (Django logs, SES console → reputation). AWS pauses sending above 5% / 0.1%. Email currently goes through Resend, so these stay quiet until SES is used again.
- **AWS budget** ($30/month, email): Cost Explorer → by service.

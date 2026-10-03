# Database restore

Prod Postgres is backed up by WAL-G to `s3://brand-clothing-db-backups-wal-875476618056/wal-g`:

- **base backup** every night at 03:00 UTC (`db/scripts/crontab`), result in Grafana: `{env="prod", container="db"} |= "WAL-G backup"`
- **WAL** (every change) continuously via `archive_command`, so a restore gets everything up to the last few seconds/minutes, not just last night

Two procedures below: the **drill** (safe, run monthly on the live prod instance) and the **real restore** (when prod data is gone or broken).

## Last drills

| Date | Type | Backup | Fetch | WAL replay | Result |
|---|---|---|---|---|---|
| 2026-10-02 | A (on prod host, throwaway container) | `base_…0D` + 4 WAL files | 3.4 s | ~2 s | passed: all 24 tables match, marker written 4 h after the backup restored |

## Drill (monthly, ~15 min, prod keeps running)

Restores the latest backup into a throwaway container on the prod instance (own folder, own port, archiving off) and compares it with prod. Prod is only read from, apart from a one-row marker table that is dropped at the end.

```powershell
aws ssm start-session --target <prod-instance-id>
```

```bash
sudo -i
cd /opt/brand-clothing
set -a; source <(grep -E '^(WALG_S3_PREFIX|AWS_REGION|POSTGRES_USER|POSTGRES_DB)=' .env); set +a
IMG=$(docker inspect brand_clothing_db --format '{{.Config.Image}}')
PSQL="docker exec brand_clothing_db psql -U $POSTGRES_USER -d $POSTGRES_DB"
Q="select table_name, (xpath('/row/c/text()', query_to_xml(format('select count(*) as c from %I', table_name), false, true, '')))[1]::text::int from information_schema.tables where table_schema='public' and table_type='BASE TABLE' order by 1"
```

**1. Snapshot prod and write a marker** (proves WAL replay, not just the base backup):

```bash
$PSQL -At -F ' ' -c "$Q" > /root/prod-counts.txt
$PSQL -c "create table restore_drill (note text, at timestamptz default now()); insert into restore_drill (note) values ('drill $(date +%F)')"
$PSQL -c "select pg_switch_wal()"
sleep 15
$PSQL -c "select last_archived_wal, last_archived_time, failed_count from pg_stat_archiver"   # time = a few seconds ago
```

**2. Fetch the latest base backup into a throwaway container:**

```bash
mkdir -p /data/restore-test && chown 999:999 /data/restore-test && chmod 700 /data/restore-test
docker run -d --name restore-test --entrypoint sleep -e WALG_S3_PREFIX="$WALG_S3_PREFIX" -e AWS_REGION="$AWS_REGION" -v /data/restore-test:/restore "$IMG" infinity
time docker exec -u postgres restore-test wal-g backup-fetch /restore LATEST
```

**3. Start it, replay WAL** — port 5433, socket only, **`archive_mode=off`** (otherwise the copy uploads its own WAL into prod's backup prefix):

```bash
docker exec -u postgres restore-test touch /restore/recovery.signal
docker exec -u postgres -d restore-test sh -c "postgres -D /restore -c port=5433 -c listen_addresses='' -c archive_mode=off -c logging_collector=off -c 'restore_command=wal-g wal-fetch %f %p' -c recovery_target_action=promote > /restore/drill.log 2>&1"
sleep 25
tail -n 25 /data/restore-test/drill.log
```

Expect `restored log file … from archive`, `last completed transaction was at log time <marker time>`, `database system is ready to accept connections`. `ERROR: … does not exist` lines are normal (that's how Postgres finds the end of the archive).

**4. Compare:**

```bash
docker exec -u postgres restore-test psql -p 5433 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select pg_is_in_recovery()" -c "select * from restore_drill"
docker exec -u postgres restore-test psql -p 5433 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -F ' ' -c "$Q" > /root/restore-counts.txt
diff <(grep -v '^restore_drill ' /root/restore-counts.txt) /root/prod-counts.txt && echo "COUNTS MATCH"
```

Pass: `f`, the marker row, `COUNTS MATCH`. Add a row to "Last drills" above.

**5. Clean up:**

```bash
docker rm -f restore-test
rm -rf /data/restore-test /root/prod-counts.txt /root/restore-counts.txt
$PSQL -c "drop table restore_drill"
docker ps --format '{{.Names}}'
```

## Real restore (prod data lost or broken)

> Not rehearsed end to end yet (that is Drill B: fresh volume). Until then, follow it carefully and keep the old data folder.

Downtime: the shop is offline from step 1 to step 5.

```bash
sudo -i
cd /opt/brand-clothing
docker compose stop web db                                      # 1. stop writers
mv /data/postgres /data/postgres.broken-$(date +%F-%H%M)        # 2. keep the old data until the restore is verified
mkdir /data/postgres && chown 999:999 /data/postgres && chmod 700 /data/postgres
docker compose run --rm --no-deps -u postgres --entrypoint wal-g db \
  backup-fetch /var/lib/postgresql/data LATEST                  # 3. base backup
touch /data/postgres/recovery.signal && chown 999:999 /data/postgres/recovery.signal
docker compose up -d db                                         # 4. replays WAL, then promotes
docker logs --tail 30 brand_clothing_db                         #    wait for "ready to accept connections"
docker compose up -d web                                        # 5. back online
```

Then:
- check the site and the data (Django admin, row counts)
- take a fresh base backup right away (the restored database runs on a new timeline):
  `docker exec -u postgres brand_clothing_db /usr/local/bin/wal-g-backup.sh`
- delete `/data/postgres.broken-*` only after a few days without problems

Restore to a point in time (e.g. just before a bad migration or a wrong `DELETE`): before step 4, add to `/data/postgres/postgresql.auto.conf`:

```
recovery_target_time = '2026-10-02 09:00:00+00'
recovery_target_action = 'promote'
```

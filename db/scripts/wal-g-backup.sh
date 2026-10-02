#!/usr/bin/env bash
set -euo pipefail

set -a
source /etc/environment
set +a

RETAIN_FULL_BACKUPS=7

log() {
  echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*"
}

# These lines reach Grafana (Loki, container="db"); the "WAL-G backup
# completed" line is what the "no backup in 26h" alert looks for, and a
# non-zero exit is logged as "WAL-G backup FAILED". Keep the wording stable.
trap 'log "WAL-G backup FAILED (exit $?)"' ERR

log "Starting base backup"
wal-g backup-push /var/lib/postgresql/data
log "Base backup completed"

log "Pruning old backups (retaining ${RETAIN_FULL_BACKUPS} full backups)"
wal-g delete retain FULL "$RETAIN_FULL_BACKUPS" --confirm
log "Retention prune completed"
log "WAL-G backup completed"

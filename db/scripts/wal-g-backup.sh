#!/usr/bin/env bash
set -euo pipefail

set -a
source /etc/environment
set +a

RETAIN_FULL_BACKUPS=7

log() {
  echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*"
}

log "Starting base backup"
wal-g backup-push /var/lib/postgresql/data
log "Base backup completed"

log "Pruning old backups (retaining ${RETAIN_FULL_BACKUPS} full backups)"
wal-g delete retain FULL "$RETAIN_FULL_BACKUPS" --confirm
log "Retention prune completed"

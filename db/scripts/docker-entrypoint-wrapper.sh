#!/bin/bash
set -e

# Cron runs jobs with a minimal environment, so the container's real
# env vars (WALG_S3_PREFIX, AWS_REGION, PG*) need to be persisted
# somewhere the cron job can source them — they don't reach it otherwise.
printenv | grep -E '^(WALG_|AWS_|PG)' > /etc/environment

cron

# Hand off to the official postgres entrypoint — still untouched,
# still doing initdb + starting the server. tini (our real PID 1)
# is what now handles zombie reaping, not this script or Postgres.
exec docker-entrypoint.sh "$@"

FROM postgres:16

ARG WALG_VERSION=v3.0.8
ARG WALG_ASSET=wal-g-pg-24.04-aarch64

ADD https://github.com/wal-g/wal-g/releases/download/${WALG_VERSION}/${WALG_ASSET} /usr/local/bin/wal-g
ADD https://github.com/wal-g/wal-g/releases/download/${WALG_VERSION}/${WALG_ASSET}.sha256 /tmp/wal-g.sha256

RUN echo "$(cut -d' ' -f1 /tmp/wal-g.sha256)  /usr/local/bin/wal-g" | sha256sum -c - \
    && chmod +x /usr/local/bin/wal-g \
    && rm /tmp/wal-g.sha256

RUN apt-get update && apt-get install -y --no-install-recommends cron tini ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY scripts/wal-g-backup.sh /usr/local/bin/wal-g-backup.sh
RUN chmod +x /usr/local/bin/wal-g-backup.sh

COPY scripts/crontab /etc/cron.d/wal-g-backup
RUN chmod 0644 /etc/cron.d/wal-g-backup \
    && crontab /etc/cron.d/wal-g-backup

COPY scripts/docker-entrypoint-wrapper.sh /usr/local/bin/docker-entrypoint-wrapper.sh
RUN chmod +x /usr/local/bin/docker-entrypoint-wrapper.sh

# tini as real PID 1 — reaps orphaned children (cron's daily job
# processes) that Postgres's postmaster wouldn't otherwise reap, since
# it only waits on children it spawned itself.
ENTRYPOINT ["tini", "--", "docker-entrypoint-wrapper.sh"]
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]

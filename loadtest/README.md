# Load test

`catalog.js` (k6) simulates shoppers browsing the catalog API: product list (paged, sorted),
collections, product details, with pauses like a person. Read-only, no login.

Install k6 on Windows: `winget install k6 --source winget`.

| Profile | Shoppers | Time | Question |
|---|---|---|---|
| `smoke` | 1 | 1 min | Does the script work? |
| `load` | up to 20 | 8 min | Is a busy day fine? (p95 < 800 ms, < 1% errors) |
| `stress` | up to 100 | 9 min | Where does it break, and what breaks first? Stops on > 1% errors. |

```powershell
k6 run -e PROFILE=smoke loadtest/catalog.js
```

Only against **staging** (08:00-20:00 Kyiv). Watch Grafana while it runs (env = staging):
Overview → Infrastructure (container CPU/memory vs limit) → Database (connections, longest
transaction) → Requests (p95, slowest paths). Write the result in the table below.

Tell the team before a run: a merge to `develop` redeploys staging mid-test (about 3 s of 502s,
and the run is not comparable).

## Results

| Date | Profile | Peak shoppers | req/s | p95 | Errors | First limit hit |
|---|---|---|---|---|---|---|
| 2026-10-17 | smoke | 1 | 0.4 | 190 ms | 0% | none |
| 2026-10-17 | load | 20 | 7 | 137 ms | 0% | none (web 0.16 cores, db 0.11, host CPU 15%) |
| 2026-10-17 | stress | 100 | 19 avg, ~70 peak | 3.1 s | 0.07% (8 × 500: `db` DNS lookup failed on a new connection) | New DB connection per request: p95 climbs past ~70 shoppers, CPU only 45% |
| 2026-10-17 | stress, after `CONN_MAX_AGE` | 100 | 24 avg, ~70 peak | 162 ms | 0% | none found (web 0.55 cores, db 0.07, host CPU 37%) |

## What we learned (2026-10-17)

- **Django opened a new DB connection per request** (`CONN_MAX_AGE` was 0): a DNS lookup of
  `db`, a TCP connect and a new Postgres process every time. At ~70 req/s Docker DNS sometimes
  failed (500s) and requests queued behind the 2 gunicorn workers (p95 3 s). `CONN_MAX_AGE=60`
  + `CONN_HEALTH_CHECKS` fixed both: 0 errors, p95 3.1 s → 162 ms, db CPU 0.25 → 0.07 cores.
- **100 shoppers is not the limit any more.** Staging (t4g.micro) stayed at 37% CPU. Not pushed
  further: long runs use up its CPU credits. Prod (t4g.small) has more room.
- **A deploy gives ~3 s of 502s** (`web` restarts and runs migrations). Fine at this size;
  zero-downtime would need two `web` containers.
- If p95 grows in the future, check first: Infrastructure → web CPU near 1 core = more gunicorn
  workers (or threads); Database → many short connections = connection reuse broken.

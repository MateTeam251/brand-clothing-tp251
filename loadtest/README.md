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

## Results

| Date | Profile | Peak shoppers | req/s | p95 | Errors | First limit hit |
|---|---|---|---|---|---|---|
| 2026-10-17 | smoke | 1 | 0.4 | 190 ms | 0% | none |
| 2026-10-17 | load | 20 | 7 | 137 ms | 0% | none (web 0.16 cores, db 0.11, host CPU 15%) |
| 2026-10-17 | stress | 100 | 19 avg, ~70 peak | 3.1 s | 0.07% (8 × 500: `db` DNS lookup failed on a new connection; fixed by `CONN_MAX_AGE`) | 2 gunicorn workers: p95 climbs past ~70 shoppers / ~40 req/s, CPU only 45% |

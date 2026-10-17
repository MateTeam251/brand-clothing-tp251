#!/usr/bin/env python3
"""Generates the Grafana dashboards in this folder (no dependencies).

Edit here, run `python generate.py`, commit the script and the JSON.
Terraform (../dashboards.tf) uploads the JSON files."""
import json
import os

OUT = os.path.dirname(os.path.abspath(__file__))
PROM={"type":"prometheus","uid":"grafanacloud-prom"}
LOKI={"type":"loki","uid":"grafanacloud-logs"}
TAGS=["brand-clothing"]
_id=[0]
def nid():
    _id[0]+=1; return _id[0]
def tgt(expr, ds=PROM, legend=None, instant=False, ref="A"):
    t={"refId":ref,"datasource":ds,"expr":expr,"editorMode":"code"}
    if legend: t["legendFormat"]=legend
    if ds is PROM:
        t["range"]=not instant; t["instant"]=instant
    else:
        t["queryType"]="instant" if instant else "range"
    return t
def thresholds(steps):
    return {"mode":"absolute","steps":[{"color":c,"value":v} for v,c in steps]}
def ts(title, targets, x, y, w=12, h=8, unit="short", desc="", min=None, max=None, steps=None, stack=False, ds=PROM):
    d={"id":nid(),"type":"timeseries","title":title,"description":desc,"datasource":ds,
       "gridPos":{"x":x,"y":y,"w":w,"h":h},"targets":targets,
       "fieldConfig":{"defaults":{"unit":unit,"custom":{"drawStyle":"line","lineWidth":2,"fillOpacity":10,"showPoints":"never","spanNulls":True,"stacking":{"mode":"normal" if stack else "none"}}},"overrides":[]},
       "options":{"legend":{"displayMode":"list","placement":"bottom","showLegend":True},"tooltip":{"mode":"multi","sort":"desc"}}}
    if min is not None: d["fieldConfig"]["defaults"]["min"]=min
    if max is not None: d["fieldConfig"]["defaults"]["max"]=max
    if steps:
        d["fieldConfig"]["defaults"]["thresholds"]=thresholds(steps)
        d["fieldConfig"]["defaults"]["custom"]["thresholdsStyle"]={"mode":"dashed"}
    return d
def stat(title, targets, x, y, w=4, h=4, unit="short", desc="", steps=None, ds=PROM, decimals=None, mappings=None, link=None):
    d={"id":nid(),"type":"stat","title":title,"description":desc,"datasource":ds,
       "gridPos":{"x":x,"y":y,"w":w,"h":h},"targets":targets,
       "fieldConfig":{"defaults":{"unit":unit,"color":{"mode":"thresholds"},"thresholds":thresholds(steps or [(None,"green")])},"overrides":[]},
       "options":{"reduceOptions":{"calcs":["lastNotNull"],"fields":"","values":False},"colorMode":"background","graphMode":"area","textMode":"value","justifyMode":"center"}}
    if decimals is not None: d["fieldConfig"]["defaults"]["decimals"]=decimals
    if mappings: d["fieldConfig"]["defaults"]["mappings"]=mappings
    if link: d["fieldConfig"]["defaults"]["links"]=[{"title":"Details","url":link}]
    return d
def table(title, targets, x, y, w=12, h=8, unit="short", desc="", ds=PROM, names=None, sort=None):
    for t in targets:
        t["format"]="table"
    return {"id":nid(),"type":"table","title":title,"description":desc,"datasource":ds,
       "gridPos":{"x":x,"y":y,"w":w,"h":h},"targets":targets,
       "fieldConfig":{"defaults":{"unit":unit},"overrides":[]},
       "transformations":[{"id":"merge","options":{}},{"id":"organize","options":{"excludeByName":{"Time":True},"renameByName":names or {}}}],
       "options":{"showHeader":True,"sortBy":[{"displayName":sort,"desc":True}] if sort else []}}
def logs(title, expr, x, y, w=24, h=10, desc=""):
    return {"id":nid(),"type":"logs","title":title,"description":desc,"datasource":LOKI,
       "gridPos":{"x":x,"y":y,"w":w,"h":h},"targets":[tgt(expr,LOKI)],
       "options":{"showTime":True,"wrapLogMessage":True,"sortOrder":"Descending","enableLogDetails":True,"dedupStrategy":"none"}}
def row(title, y, collapsed=False, panels=None):
    r={"id":nid(),"type":"row","title":title,"collapsed":collapsed,"gridPos":{"x":0,"y":y,"w":24,"h":1},"panels":panels or []}
    return r
def text(content, x, y, w=24, h=3):
    return {"id":nid(),"type":"text","title":"","gridPos":{"x":x,"y":y,"w":w,"h":h},"options":{"mode":"markdown","content":content}}
ENV_VAR={"name":"env","label":"Environment","type":"custom","query":"prod,staging","current":{"text":"prod","value":"prod"},"options":[{"text":"prod","value":"prod","selected":True},{"text":"staging","value":"staging","selected":False}],"hide":0}
def dashboard(uid, title, desc, panels, extra_vars=(), time="now-6h"):
    _id[0]=0
    return {"uid":uid,"title":title,"description":desc,"tags":TAGS,"timezone":"browser","editable":True,
      "schemaVersion":39,"time":{"from":time,"to":"now"},"refresh":"1m","graphTooltip":1,
      "templating":{"list":[ENV_VAR,*extra_vars]},
      "annotations":{"list":[
        {"builtIn":1,"datasource":{"type":"grafana","uid":"-- Grafana --"},"enable":True,"hide":True,"iconColor":"rgba(0, 211, 255, 1)","name":"Annotations & Alerts","type":"dashboard"},
        {"datasource":{"type":"grafana","uid":"-- Grafana --"},"enable":True,"iconColor":"purple","name":"Releases","target":{"type":"tags","tags":["release","$env"],"matchAny":False,"limit":100}}]},
      "links":[{"title":"Dashboards","type":"dashboards","tags":TAGS,"asDropdown":False,"includeVars":True,"keepTime":True}],
      "panels":panels}
def save(path, d):
    with open(path,'w') as f: json.dump(d,f,indent=2); f.write("\n")

N='{env="$env", container="nginx"} | json | __error__=""'
E='$env'
APP_ERR='{env="$env", container=~"web|celery"} |~ `\\] (ERROR|CRITICAL):|: (ERROR|CRITICAL)/|\\[(ERROR|CRITICAL)\\]` !~ `^\\[django\\.request\\]`'
DB='datname!~"template.*|postgres"'
U={"overview":"bc-overview","requests":"29f68f91-62df-4030-8a08-fa587443572c","infra":"bc-infrastructure","db":"bc-database","logs":"c3a239e1-4f08-4164-a391-0150119cca2c"}
def link(k): return f"/d/{U[k]}?var-env=$env&${{__url_time_range}}"
up_map=[{"type":"value","options":{"0":{"text":"DOWN","color":"red"},"1":{"text":"UP","color":"green"}}}]

# ---------- Overview ----------
p=[]; y=0
p.append(text("**Start here.** Status, then the golden signals (traffic, errors, latency, saturation). Each panel's title link opens the detail dashboard. Purple lines = releases. Synthetic checks run against **prod** only.",0,y,h=2)); y+=2
p.append(stat("Admin / backend (prod)",[tgt('sum(increase(probe_all_success_sum{job="prod-admin-login"}[10m])) / sum(increase(probe_all_success_count{job="prod-admin-login"}[10m]))')],0,y,unit="percentunit",decimals=0,
  desc="Share of successful synthetic checks of /api/admin/login/ in the last 10 min (3 EU probes).",steps=[(None,"red"),(0.5,"orange"),(0.99,"green")]))
p.append(stat("Shop frontend (prod)",[tgt('sum(increase(probe_all_success_sum{job="prod-frontend"}[10m])) / sum(increase(probe_all_success_count{job="prod-frontend"}[10m]))')],4,y,unit="percentunit",decimals=0,
  desc="Share of successful synthetic checks of the shop page in the last 10 min.",steps=[(None,"red"),(0.5,"orange"),(0.99,"green")]))
p.append(stat("Database",[tgt(f'max(pg_up{{env="{E}"}})')],8,y,desc="Postgres exporter can connect.",mappings=up_map,steps=[(None,"red"),(1,"green")],link=link("db")))
p.append(stat("Origin certificate",[tgt(f'(min(probe_ssl_earliest_cert_expiry{{job="integrations/blackbox/origin_cert", env="{E}"}}) - time()) / 86400')],12,y,unit="d",decimals=0,
  desc="Days until the Let's Encrypt certificate on nginx expires. certbot renews at 30.",steps=[(None,"red"),(14,"orange"),(30,"green")]))
p.append(stat("Memory available",[tgt(f'100 * node_memory_MemAvailable_bytes{{env="{E}"}} / node_memory_MemTotal_bytes{{env="{E}"}}')],16,y,unit="percent",decimals=0,
  desc="Whole server. Alert below 10%.",steps=[(None,"red"),(10,"orange"),(25,"green")],link=link("infra")))
p.append(stat("Disk used (max)",[tgt(f'max(100 * (1 - node_filesystem_avail_bytes{{env="{E}", mountpoint=~"/|/data"}} / node_filesystem_size_bytes{{env="{E}", mountpoint=~"/|/data"}}))')],20,y,unit="percent",decimals=0,
  desc="Fullest of / and /data. Alert above 85%.",steps=[(None,"green"),(70,"orange"),(85,"red")],link=link("infra")))
y+=4
p.append(ts("Traffic: requests/s",[tgt(f'sum(rate({N} [$__auto]))',LOKI,"requests/s")],0,y,w=8,unit="reqps",ds=LOKI,min=0,desc="All requests reaching nginx (API + admin). Details: Requests dashboard."))
p.append(ts("Errors: 5xx %",[tgt(f'100 * (sum(rate({N} | status >= 500 [$__auto])) or vector(0)) / sum(rate({N} [$__auto]))',LOKI,"5xx %")],8,y,w=8,unit="percent",ds=LOKI,min=0,steps=[(None,"green"),(1,"orange"),(5,"red")],desc="Share of responses with status 500-599."))
p.append(ts("Latency: p95",[tgt(f'quantile_over_time(0.95, {N} | unwrap request_time [$__auto]) by (env)',LOKI,"p95")],16,y,w=8,unit="s",ds=LOKI,min=0,steps=[(None,"green"),(1,"orange"),(3,"red")],desc="95% of requests were faster than this (nginx request_time)."))
y+=8
p.append(ts("Saturation: memory per container",[tgt(f'sum by (container) (container_memory_working_set_bytes{{env="{E}"}})',PROM,"{{container}}")],0,y,unit="bytes",min=0,desc="Working set per container. Limits: Infrastructure dashboard."))
p.append(ts("Saturation: CPU per container",[tgt(f'sum by (container) (rate(container_cpu_usage_seconds_total{{env="{E}"}}[$__rate_interval]))',PROM,"{{container}}")],12,y,unit="cores",min=0,desc="CPU cores used per container (2 vCPU on the server)."))
save(f"{OUT}/overview.json",dashboard(U["overview"],"Overview","Start here: status and golden signals of the shop.",p))

# ---------- Requests (RED) ----------
p=[]; y=0
p.append(stat("Requests/s",[tgt(f'sum(rate({N} [$__auto]))',LOKI)],0,y,w=6,unit="reqps",ds=LOKI,decimals=2))
p.append(stat("5xx %",[tgt(f'100 * (sum(rate({N} | status >= 500 [$__auto])) or vector(0)) / sum(rate({N} [$__auto]))',LOKI)],6,y,w=6,unit="percent",ds=LOKI,decimals=2,steps=[(None,"green"),(1,"orange"),(5,"red")]))
p.append(stat("p95 latency",[tgt(f'quantile_over_time(0.95, {N} | unwrap request_time [$__auto]) by (env)',LOKI)],12,y,w=6,unit="s",ds=LOKI,decimals=2,steps=[(None,"green"),(1,"orange"),(3,"red")]))
p.append(stat("429 rate-limited (range)",[tgt(f'sum(count_over_time({N} | status = 429 [$__range]))',LOKI,instant=True)],18,y,w=6,ds=LOKI,steps=[(None,"green"),(1,"orange")],desc="Requests blocked by nginx rate limits (login, registration, password reset, checkout) in the selected time range."))
y+=4
p.append(row("Rate",y)); y+=1
p.append(ts("Requests/s by status class",[tgt(f'sum by (class) (rate({N} | label_format class=`{{{{ substr 0 1 .status }}}}xx` [$__auto]))',LOKI,"{{class}}")],0,y,w=24,unit="reqps",ds=LOKI,min=0,desc="2xx ok, 3xx redirects, 4xx client errors (incl. 401/404/429), 5xx server errors."))
y+=8
p.append(row("Errors",y)); y+=1
p.append(ts("5xx and 429 per minute",[tgt(f'sum(count_over_time({N} | status >= 500 [1m])) or vector(0)',LOKI,"5xx",ref="A"),tgt(f'sum(count_over_time({N} | status = 429 [1m])) or vector(0)',LOKI,"429 rate limited",ref="B")],0,y,unit="short",ds=LOKI,min=0))
p.append(table("Paths with most 4xx/5xx",[tgt(f'topk(10, sum by (path, status) (count_over_time({N} | status >= 400 [$__range])))',LOKI,instant=True)],12,y,ds=LOKI,desc="In the selected time range.",names={"Value #A":"Requests"},sort="Requests"))
y+=8
p.append(row("Duration",y)); y+=1
p.append(ts("Response time p50 / p95 / p99",[tgt(f'quantile_over_time({q}, {N} | unwrap request_time [$__auto]) by (env)',LOKI,lbl,ref=r) for q,lbl,r in [("0.5","p50","A"),("0.95","p95","B"),("0.99","p99","C")]],0,y,unit="s",ds=LOKI,min=0,steps=[(None,"green"),(1,"orange"),(3,"red")]))
p.append(ts("nginx total vs Django (p95)",[tgt(f'quantile_over_time(0.95, {N} | unwrap request_time [$__auto]) by (env)',LOKI,"total (nginx)",ref="A"),tgt(f'quantile_over_time(0.95, {N} | upstream_time != "" | unwrap upstream_time [$__auto]) by (env)',LOKI,"Django (upstream)",ref="B")],12,y,unit="s",ds=LOKI,min=0,desc="If both lines move together, the time is spent in Django/DB. A gap = nginx/network/client upload."))
y+=8
p.append(table("Slowest paths (p95)",[tgt(f'topk(10, quantile_over_time(0.95, {N} | unwrap request_time [$__range]) by (path))',LOKI,instant=True)],0,y,unit="s",ds=LOKI,names={"Value #A":"p95"},sort="p95",desc="95% of requests to this path were faster than this, in the selected time range."))
p.append(table("Busiest paths",[tgt(f'topk(10, sum by (path) (count_over_time({N} [$__range])))',LOKI,instant=True)],12,y,ds=LOKI,names={"Value #A":"Requests"},sort="Requests",desc="Request count per path in the selected time range."))
save(f"{OUT}/requests.json",dashboard(U["requests"],"Requests","RED view of the backend from nginx access logs: rate, errors, duration.",p))

# ---------- Infrastructure (USE) ----------
p=[]; y=0
p.append(row("Server",y)); y+=1
p.append(ts("CPU used",[tgt(f'100 * (1 - avg(rate(node_cpu_seconds_total{{env="{E}", mode="idle"}}[$__rate_interval])))',PROM,"CPU %")],0,y,w=8,unit="percent",min=0,max=100,steps=[(None,"green"),(80,"orange"),(95,"red")]))
p.append(ts("Memory",[tgt(f'node_memory_MemTotal_bytes{{env="{E}"}} - node_memory_MemAvailable_bytes{{env="{E}"}}',PROM,"used",ref="A"),tgt(f'node_memory_MemTotal_bytes{{env="{E}"}}',PROM,"total",ref="B")],8,y,w=8,unit="bytes",min=0))
p.append(ts("Disk used",[tgt(f'100 * (1 - node_filesystem_avail_bytes{{env="{E}", mountpoint=~"/|/data"}} / node_filesystem_size_bytes{{env="{E}", mountpoint=~"/|/data"}})',PROM,"{{mountpoint}}")],16,y,w=8,unit="percent",min=0,max=100,steps=[(None,"green"),(70,"orange"),(85,"red")],desc="/ = system + Docker images, /data = Postgres, certificates, app logs."))
y+=8
p.append(ts("Load (1 min) per CPU",[tgt(f'sum(node_load1{{env="{E}"}}) / count(node_cpu_seconds_total{{env="{E}", mode="idle"}})',PROM,"load / cpu")],0,y,w=8,unit="short",min=0,steps=[(None,"green"),(1,"orange"),(2,"red")],desc="Above 1 = more work queued than CPUs."))
p.append(ts("Disk busy",[tgt(f'100 * rate(node_disk_io_time_seconds_total{{env="{E}"}}[$__rate_interval])',PROM,"{{device}}")],8,y,w=8,unit="percent",min=0,max=100,desc="Share of time each EBS volume was busy."))
p.append(ts("Network",[tgt(f'sum(rate(node_network_receive_bytes_total{{env="{E}", device!~"lo|veth.*|docker.*|br-.*"}}[$__rate_interval]))',PROM,"in",ref="A"),tgt(f'-sum(rate(node_network_transmit_bytes_total{{env="{E}", device!~"lo|veth.*|docker.*|br-.*"}}[$__rate_interval]))',PROM,"out",ref="B")],16,y,w=8,unit="Bps",desc="In above zero, out below."))
y+=8
p.append(row("Containers",y)); y+=1
p.append(ts("Memory used / limit",[tgt(f'100 * sum by (container) (container_memory_working_set_bytes{{env="{E}"}}) / sum by (container) (container_spec_memory_limit_bytes{{env="{E}"}} > 0)',PROM,"{{container}}")],0,y,unit="percent",min=0,max=100,steps=[(None,"green"),(80,"orange"),(95,"red")],desc="Near 100% the container gets OOM-killed and restarts. Limits: docker-compose.prod.yml / SSM *_MEM_LIMIT."))
p.append(ts("Memory used",[tgt(f'sum by (container) (container_memory_working_set_bytes{{env="{E}"}})',PROM,"{{container}}")],12,y,unit="bytes",min=0))
y+=8
p.append(ts("CPU per container",[tgt(f'sum by (container) (rate(container_cpu_usage_seconds_total{{env="{E}"}}[$__rate_interval]))',PROM,"{{container}}")],0,y,unit="cores",min=0))
p.append(table("Restarts and OOM kills (range)",[tgt(f'sum by (container) (changes(container_start_time_seconds{{env="{E}"}}[$__range]))',PROM,"{{container}}",instant=True,ref="A"),tgt(f'sum by (container) (increase(container_oom_events_total{{env="{E}"}}[$__range]))',PROM,"{{container}}",instant=True,ref="B")],12,y,desc="In the selected time range. Restarts are normal during deploys; OOM kills should stay 0.",names={"Value #A":"Restarts","Value #B":"OOM kills"},sort="Restarts"))
save(f"{OUT}/infrastructure.json",dashboard(U["infra"],"Infrastructure","USE view: the server and every container (CPU, memory, disk, network).",p))

# ---------- Database ----------
p=[]; y=0
p.append(stat("Postgres",[tgt(f'max(pg_up{{env="{E}"}})')],0,y,w=4,mappings=up_map,steps=[(None,"red"),(1,"green")]))
p.append(stat("Database size",[tgt(f'sum(pg_database_size_bytes{{env="{E}", {DB}}})')],4,y,w=5,unit="bytes"))
p.append(stat("Connections",[tgt(f'sum(pg_stat_activity_count{{env="{E}", {DB}}})')],9,y,w=5,desc="Postgres default max_connections = 100.",steps=[(None,"green"),(60,"orange"),(90,"red")]))
p.append(stat("Cache hit ratio",[tgt(f'sum(rate(pg_stat_database_blks_hit{{env="{E}", {DB}}}[$__range])) / (sum(rate(pg_stat_database_blks_hit{{env="{E}", {DB}}}[$__range])) + sum(rate(pg_stat_database_blks_read{{env="{E}", {DB}}}[$__range])))',instant=True)],14,y,w=5,unit="percentunit",decimals=1,desc="Reads served from memory. Healthy: above 99%.",steps=[(None,"red"),(0.9,"orange"),(0.99,"green")]))
p.append(stat("Last WAL archived",[tgt(f'max(pg_stat_archiver_last_archive_age{{env="{E}"}})')],19,y,w=5,unit="s",desc="Time since the last WAL file reached S3. Grows when idle (a file closes every few minutes or at 16 MB); hours = archiving is stuck.",steps=[(None,"green"),(3600,"orange"),(10800,"red")]))
y+=4
p.append(ts("Connections by state",[tgt(f'sum by (state) (pg_stat_activity_count{{env="{E}", {DB}}})',PROM,"{{state}}")],0,y,unit="short",min=0,desc="active = running a query, idle = open but waiting, idle in transaction = holding locks (should be ~0)."))
p.append(ts("Transactions/s",[tgt(f'sum(rate(pg_stat_database_xact_commit{{env="{E}", {DB}}}[$__rate_interval]))',PROM,"commits",ref="A"),tgt(f'sum(rate(pg_stat_database_xact_rollback{{env="{E}", {DB}}}[$__rate_interval]))',PROM,"rollbacks",ref="B")],12,y,unit="ops",min=0))
y+=8
p.append(ts("Rows/s",[tgt(f'sum(rate(pg_stat_database_tup_{k}{{env="{E}", {DB}}}[$__rate_interval]))',PROM,k,ref=chr(65+i)) for i,k in enumerate(["fetched","inserted","updated","deleted"])],0,y,unit="ops",min=0))
p.append(ts("Deadlocks, WAL archive failures",[tgt(f'sum(increase(pg_stat_database_deadlocks{{env="{E}", {DB}}}[$__rate_interval]))',PROM,"deadlocks",ref="A"),tgt(f'sum(increase(pg_stat_archiver_failed_count{{env="{E}"}}[$__rate_interval]))',PROM,"archive failures",ref="B")],12,y,unit="short",min=0,steps=[(None,"green"),(1,"red")],desc="Both should stay at 0."))
y+=8
p.append(ts("Database size",[tgt(f'sum by (datname) (pg_database_size_bytes{{env="{E}", {DB}}})',PROM,"{{datname}}")],0,y,unit="bytes",min=0))
p.append(logs("Backups (WAL-G)",'{env="$env", container="db"} |= "WAL-G backup"',12,y,w=12,h=8,desc="Nightly base backup at 03:00 UTC (prod; staging is off at night)."))
y+=8
p.append(ts("Longest open transaction",[tgt(f'max(pg_stat_activity_max_tx_duration{{env="{E}", {DB}}})',PROM,"longest")],0,y,unit="s",min=0,steps=[(None,"green"),(60,"orange"),(300,"red")],desc="A query or transaction running for minutes holds locks and blocks others (and vacuum). Normally under a second."))
p.append(table("Largest tables",[tgt(f'topk(10, sum by (relname) (pg_stat_user_tables_table_size_bytes{{env="{E}"}} + pg_stat_user_tables_index_size_bytes{{env="{E}"}}))',PROM,instant=True)],12,y,unit="bytes",desc="Table + index size. Shows which tables grow.",names={"Value #A":"Size","relname":"table"},sort="Size"))
save(f"{OUT}/database.json",dashboard(U["db"],"Database","Postgres health: connections, throughput, cache, size, WAL archiving, backups.",p,time="now-24h"))

# ---------- Logs ----------
cont={"name":"container","label":"Container","type":"custom","query":"web,celery,nginx,db,redis,certbot","multi":True,"includeAll":True,"allValue":".+",
      "current":{"text":["All"],"value":["$__all"]},"options":[],"hide":0}
search={"name":"search","label":"Search","type":"textbox","query":"","current":{"text":"","value":""},"hide":0}
p=[]; y=0
p.append(ts("Log lines per minute",[tgt('sum by (container) (count_over_time({env="$env", container=~"$container"} [1m]))',LOKI,"{{container}}")],0,y,unit="short",ds=LOKI,min=0))
p.append(ts("App errors per minute",[tgt(f'sum by (container) (count_over_time({APP_ERR} [1m]))',LOKI,"{{container}}")],12,y,unit="short",ds=LOKI,min=0,steps=[(None,"green"),(1,"red")],desc="Same filter as the 'prod app errors' alert (ERROR/CRITICAL from Django, Celery, gunicorn; 500s excluded)."))
y+=8
p.append(logs("Errors (web, celery)",APP_ERR,0,y,h=10))
y+=10
p.append(logs("All logs (container + search)",'{env="$env", container=~"$container"} |= "$search"',0,y,h=14))
y+=14
p.append(logs("nginx 5xx",f'{N} | status >= 500',0,y,w=12,h=8))
p.append(logs("Backups (WAL-G)",'{env="$env", container="db"} |= "WAL-G backup"',12,y,w=12,h=8))
save(f"{OUT}/logs.json",dashboard(U["logs"],"Logs","Search and errors across all containers.",p,extra_vars=(cont,search)))
print("done")

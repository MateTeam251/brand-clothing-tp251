# Alert rules, folder brand-clothing. Runbooks: docs/alerts.md (anchor per rule).
# The synthetic check's alert is created by the Synthetic Monitoring app itself.

locals {
  runbook = "https://github.com/MateTeam251/brand-clothing-tp251/blob/main/docs/alerts.md"

  rule_groups = {
    prod-backups = {
      interval = 600
      rules = [
        {
          name    = "prod backup failed"
          source  = "logs"
          expr    = "count_over_time({env=\"prod\", container=\"db\"} |= \"WAL-G backup FAILED\" [1h])"
          op      = "gt"
          value   = 0
          for     = null
          no_data = "OK"
          anchor  = "prod-backup-failed"
        },
        {
          name    = "prod WAL archiving failing"
          source  = "logs"
          expr    = "count_over_time({env=\"prod\", container=\"db\"} |= \"archive command failed\" [15m])"
          op      = "gt"
          value   = 0
          for     = "10m"
          no_data = "OK"
          anchor  = "prod-wal-archiving-failing"
        },
        {
          # No data = no backup at all, so that alerts too.
          name    = "prod backup missing (26h)"
          source  = "logs"
          expr    = "count_over_time({env=\"prod\", container=\"db\"} |= \"WAL-G backup completed\" [26h])"
          op      = "lt"
          value   = 1
          for     = "10m"
          no_data = "Alerting"
          anchor  = "prod-backup-missing-26h"
        },
      ]
    }

    prod-cert = {
      interval = 3600
      rules = [
        {
          # Days left. No data = nginx serves no certificate.
          name    = "Origin certificate expiry"
          source  = "prom"
          expr    = "(min(last_over_time(probe_ssl_earliest_cert_expiry{job=\"integrations/blackbox/origin_cert\", env=\"prod\"}[15m])) - time()) / 86400"
          op      = "lt"
          value   = 14
          for     = "1h"
          no_data = "Alerting"
          anchor  = "origin-certificate-expiry"
          paused  = true # until the release with the Alloy check reaches prod
        },
      ]
    }

    prod-infra = {
      interval = 60
      rules = [
        {
          name    = "prod disk above 85%"
          source  = "prom"
          expr    = "100 * (1 - node_filesystem_avail_bytes{env=\"prod\", mountpoint=~\"/|/data\"} / node_filesystem_size_bytes{env=\"prod\", mountpoint=~\"/|/data\"})"
          op      = "gt"
          value   = 85
          for     = "10m"
          no_data = "OK"
          anchor  = "prod-disk-above-85"
        },
        {
          name    = "prod memory available below 10%"
          source  = "prom"
          expr    = "100 * node_memory_MemAvailable_bytes{env=\"prod\"} / node_memory_MemTotal_bytes{env=\"prod\"}"
          op      = "lt"
          value   = 10
          for     = "10m"
          no_data = "OK"
          anchor  = "prod-memory-available-below-10"
        },
        {
          name    = "prod not sending metrics"
          source  = "prom"
          expr    = "absent_over_time(up{env=\"prod\"}[10m])"
          op      = "gt"
          value   = 0
          for     = "5m"
          no_data = "OK"
          anchor  = "prod-not-sending-metrics"
        },
        {
          name    = "prod 5xx errors"
          source  = "logs"
          expr    = "sum(count_over_time({env=\"prod\", container=\"nginx\"} | json | __error__=\"\" | status >= 500 [5m]))"
          op      = "gt"
          value   = 5
          for     = "5m"
          no_data = "OK"
          anchor  = "prod-5xx-errors"
        },
      ]
    }
  }

  datasources = {
    logs = { uid = "grafanacloud-logs", type = "loki" }
    prom = { uid = "grafanacloud-prom", type = "prometheus" }
  }

  # Extra model fields per data source (as Grafana saves them).
  query_extra = {
    logs = { queryType = "instant", datasource = { uid = "grafanacloud-logs", type = "loki" } }
    prom = { range = false, legendFormat = "__auto" }
  }
}

resource "grafana_rule_group" "this" {
  # Keys only: the groups have different shapes, so not a plain map.
  for_each = toset(keys(local.rule_groups))

  name               = each.key
  folder_uid         = grafana_folder.brand_clothing.uid
  interval_seconds   = local.rule_groups[each.key].interval
  disable_provenance = true # created in the UI; false would force a replacement

  dynamic "rule" {
    for_each = local.rule_groups[each.key].rules
    content {
      name           = rule.value.name
      condition      = "C"
      for            = rule.value.for
      no_data_state  = rule.value.no_data
      exec_err_state = "Error"
      is_paused      = try(rule.value.paused, false)

      annotations = {
        runbook_url = "${local.runbook}#${rule.value.anchor}"
      }

      # A: the query
      data {
        ref_id         = "A"
        query_type     = rule.value.source == "logs" ? "instant" : null
        datasource_uid = local.datasources[rule.value.source].uid

        relative_time_range {
          from = 600
          to   = 0
        }

        model = jsonencode(merge(
          {
            refId         = "A"
            expr          = rule.value.expr
            editorMode    = "code"
            instant       = true
            intervalMs    = 1000
            maxDataPoints = 43200
          },
          local.query_extra[rule.value.source]
        ))
      }

      # C: threshold on A
      data {
        ref_id         = "C"
        query_type     = "expression"
        datasource_uid = "__expr__"

        relative_time_range {
          from = 0
          to   = 0
        }

        model = jsonencode({
          refId         = "C"
          type          = "threshold"
          expression    = "A"
          datasource    = { type = "__expr__", uid = "__expr__" }
          intervalMs    = 1000
          maxDataPoints = 43200

          conditions = [{
            type      = "query"
            evaluator = { type = rule.value.op, params = [rule.value.value] }
            operator  = { type = "and" }
            query     = { params = ["C"] }
            reducer   = { type = "last", params = [] }
          }]
        })
      }

      notification_settings {
        contact_point = grafana_contact_point.email.name
      }
    }
  }
}

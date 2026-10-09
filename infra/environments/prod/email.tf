# Amazon SES: the domain identity is per account + region, so staging and
# prod both send through this one (the app role may use identity/*).

resource "aws_sesv2_email_identity" "domain" {
  email_identity = aws_route53_zone.main.name

  # Every message from this domain goes through the configuration set below.
  configuration_set_name = aws_sesv2_configuration_set.main.configuration_set_name
}

# Easy DKIM: three CNAMEs, SES signs every message.
resource "aws_route53_record" "ses_dkim" {
  count = 3

  zone_id = aws_route53_zone.main.zone_id
  name    = "${aws_sesv2_email_identity.domain.dkim_signing_attributes[0].tokens[count.index]}._domainkey.${aws_route53_zone.main.name}"
  type    = "CNAME"
  ttl     = 1800
  records = ["${aws_sesv2_email_identity.domain.dkim_signing_attributes[0].tokens[count.index]}.dkim.amazonses.com"]
}

# Bounces come back to mail.<domain>, so SPF passes for our own domain.
resource "aws_sesv2_email_identity_mail_from_attributes" "domain" {
  email_identity         = aws_sesv2_email_identity.domain.email_identity
  mail_from_domain       = "mail.${aws_route53_zone.main.name}"
  behavior_on_mx_failure = "USE_DEFAULT_VALUE"
}

resource "aws_route53_record" "ses_mail_from_mx" {
  zone_id = aws_route53_zone.main.zone_id
  name    = aws_sesv2_email_identity_mail_from_attributes.domain.mail_from_domain
  type    = "MX"
  ttl     = 1800
  records = ["10 feedback-smtp.${var.aws_region}.amazonses.com"]
}

resource "aws_route53_record" "ses_mail_from_spf" {
  zone_id = aws_route53_zone.main.zone_id
  name    = aws_sesv2_email_identity_mail_from_attributes.domain.mail_from_domain
  type    = "TXT"
  ttl     = 1800
  records = ["v=spf1 include:amazonses.com ~all"]
}

# Monitor only for now (p=none); Gmail and Yahoo expect a DMARC record.
resource "aws_route53_record" "dmarc" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "_dmarc.${aws_route53_zone.main.name}"
  type    = "TXT"
  ttl     = 1800
  records = ["v=DMARC1; p=none"]
}

# --- Bounces and complaints ------------------------------------------------

resource "aws_sesv2_configuration_set" "main" {
  configuration_set_name = "${var.project_name}-transactional"

  reputation_options {
    reputation_metrics_enabled = true
  }

  # SES stops sending to these addresses by itself.
  suppression_options {
    suppressed_reasons = ["BOUNCE", "COMPLAINT"]
  }
}

# One topic for both: each bounce/complaint from SES, and the rate alarms.
resource "aws_sns_topic" "email_alerts" {
  name = "${var.project_name}-email-alerts"
}

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "email_alerts" {
  statement {
    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.email_alerts.arn]

    principals {
      type        = "Service"
      identifiers = ["ses.amazonaws.com", "cloudwatch.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_sns_topic_policy" "email_alerts" {
  arn    = aws_sns_topic.email_alerts.arn
  policy = data.aws_iam_policy_document.email_alerts.json
}

# Needs a one-time click on the confirmation email AWS sends.
resource "aws_sns_topic_subscription" "email_alerts" {
  topic_arn = aws_sns_topic.email_alerts.arn
  protocol  = "email"
  endpoint  = var.budget_alert_email
}

resource "aws_sesv2_configuration_set_event_destination" "bounces" {
  configuration_set_name = aws_sesv2_configuration_set.main.configuration_set_name
  event_destination_name = "bounces-complaints"

  event_destination {
    enabled              = true
    matching_event_types = ["BOUNCE", "COMPLAINT", "REJECT"]

    sns_destination {
      topic_arn = aws_sns_topic.email_alerts.arn
    }
  }

  depends_on = [aws_sns_topic_policy.email_alerts]
}

# Account-wide rates. AWS reviews an account at 5% bounces / 0.1% complaints,
# so warn well before that.
resource "aws_cloudwatch_metric_alarm" "ses_bounce_rate" {
  alarm_name          = "${var.project_name}-ses-bounce-rate"
  namespace           = "AWS/SES"
  metric_name         = "Reputation.BounceRate"
  statistic           = "Maximum"
  period              = 3600
  evaluation_periods  = 1
  comparison_operator = "GreaterThanThreshold"
  threshold           = 0.03
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.email_alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "ses_complaint_rate" {
  alarm_name          = "${var.project_name}-ses-complaint-rate"
  namespace           = "AWS/SES"
  metric_name         = "Reputation.ComplaintRate"
  statistic           = "Maximum"
  period              = 3600
  evaluation_periods  = 1
  comparison_operator = "GreaterThanThreshold"
  threshold           = 0.0005
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.email_alerts.arn]
}

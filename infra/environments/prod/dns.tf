# Shared by both environments; staging finds it by name. Registered at
# GoDaddy, which points to the name servers in output "name_servers".
resource "aws_route53_zone" "main" {
  name = "theart-theartist.com"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_acm_certificate" "site" {
  provider                  = aws.us_east_1
  domain_name               = "theart-theartist.com"
  subject_alternative_names = ["www.theart-theartist.com"]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "cert_validation" {
  for_each = { for o in aws_acm_certificate.site.domain_validation_options : o.domain_name => o }

  zone_id         = aws_route53_zone.main.zone_id
  name            = each.value.resource_record_name
  type            = each.value.resource_record_type
  records         = [each.value.resource_record_value]
  ttl             = 300
  allow_overwrite = true
}

resource "aws_acm_certificate_validation" "site" {
  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.site.arn
  validation_record_fqdns = [for r in aws_route53_record.cert_validation : r.fqdn]
}

# CloudFront's origin for /api/*. Not for visitors.
locals {
  site_host   = "theart-theartist.com"
  origin_host = "origin.theart-theartist.com"
}

resource "aws_route53_record" "origin" {
  zone_id = aws_route53_zone.main.zone_id
  name    = local.origin_host
  type    = "A"
  ttl     = 300
  records = [module.compute.app_public_ip]
}

resource "aws_route53_record" "site" {
  for_each = {
    apex_a    = { name = local.site_host, type = "A" }
    apex_aaaa = { name = local.site_host, type = "AAAA" }
    www_a     = { name = "www.${local.site_host}", type = "A" }
    www_aaaa  = { name = "www.${local.site_host}", type = "AAAA" }
  }

  zone_id = aws_route53_zone.main.zone_id
  name    = each.value.name
  type    = each.value.type

  alias {
    name                   = module.storage.cloudfront_domain_name
    zone_id                = module.storage.cloudfront_hosted_zone_id
    evaluate_target_health = false
  }
}

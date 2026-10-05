# The zone itself is managed in prod.
data "aws_route53_zone" "main" {
  name = "theart-theartist.com"
}

resource "aws_acm_certificate" "site" {
  provider          = aws.us_east_1
  domain_name       = "staging.theart-theartist.com"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "cert_validation" {
  for_each = { for o in aws_acm_certificate.site.domain_validation_options : o.domain_name => o }

  zone_id         = data.aws_route53_zone.main.zone_id
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

# Non-secret app env vars. deploy.sh turns every param under
# /brand-clothing/prod/ into .env on the next deploy.
# Not here: secrets (…/secrets/*, by hand) and IMAGE_TAG / DB_IMAGE_TAG (pipeline).

locals {
  app_config = {
    DEBUG                   = "False"
    ALLOWED_HOSTS           = module.compute.app_public_ip
    SITE_URL                = "http://${module.compute.app_public_ip}"
    CORS_ALLOWED_ORIGINS    = "https://${module.storage.cloudfront_domain_name}"
    EMAIL_BACKEND           = "django.core.mail.backends.console.EmailBackend"
    POSTGRES_DB             = "brand_clothing_db"
    POSTGRES_USER           = "brand_clothing"
    POSTGRES_HOST           = "db"
    POSTGRES_PORT           = "5432"
    USE_LOCALSTACK          = "False"
    AWS_REGION              = "eu-central-1"
    AWS_S3_REGION_NAME      = "eu-central-1"
    AWS_STORAGE_BUCKET_NAME = module.storage.media_bucket_name
    WALG_S3_PREFIX          = "s3://${module.storage.backups_bucket_name}/wal-g"
    ECR_REGISTRY            = "875476618056.dkr.ecr.eu-central-1.amazonaws.com"

    # Weekly cart report (carts.reports). Private bucket, not the media one.
    ANALYTICS_REPORTS_BUCKET = module.storage.reports_bucket_name
    ANALYTICS_REPORTS_PREFIX = "reports/carts"

    # Name CloudFront uses for the backend (dns.tf); certbot gets its certificate.
    ORIGIN_HOST = local.origin_host

    # Starts the redis + celery services in docker-compose.prod.yml.
    COMPOSE_PROFILES = "celery"

    # Grafana Cloud (Alloy container). Not secret; the token is in secrets/.
    DEPLOY_ENV        = "prod"
    GRAFANA_PROM_URL  = "https://prometheus-prod-65-prod-eu-west-2.grafana.net/api/prom/push"
    GRAFANA_PROM_USER = "3626625"
    GRAFANA_LOKI_URL  = "https://logs-prod-012.grafana.net/loki/api/v1/push"
    GRAFANA_LOKI_USER = "1808980"
  }
}

resource "aws_ssm_parameter" "app_config" {
  for_each = local.app_config

  name  = "/brand-clothing/prod/${each.key}"
  type  = "String"
  value = each.value
}

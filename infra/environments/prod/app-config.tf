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
  }
}

resource "aws_ssm_parameter" "app_config" {
  for_each = local.app_config

  name  = "/brand-clothing/prod/${each.key}"
  type  = "String"
  value = each.value
}

# Adopt the params created by hand (one-time; delete this block after apply).
import {
  for_each = { for k, v in local.app_config : k => v if k != "EMAIL_BACKEND" } # EMAIL_BACKEND is new in prod
  to       = aws_ssm_parameter.app_config[each.key]
  id       = "/brand-clothing/prod/${each.key}"
}

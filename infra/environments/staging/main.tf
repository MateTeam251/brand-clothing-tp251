########################################################################
# staging environment
#
# Same modules as prod, fully separate resources: own VPC, buckets, IAM
# role, SSM path (/brand-clothing/staging) and state. Shares only the ECR
# images. Smaller instance, running on working hours only.
#
# Not here on purpose: cicd-oidc, ecr and the budget (account-wide, in prod).
########################################################################

module "network" {
  source = "../../modules/network"

  project_name       = var.project_name
  vpc_cidr           = "10.1.0.0/16" # different from prod, in case the VPCs ever need peering
  public_subnet_cidr = "10.1.1.0/24"
}

module "storage" {
  source = "../../modules/storage"

  project_name  = var.project_name
  bucket_suffix = var.bucket_suffix

  app_role_enabled = true
  app_iam_role_arn = module.compute.app_role_arn
}

module "compute" {
  source = "../../modules/compute"

  project_name          = var.project_name
  ecr_repository_prefix = var.ecr_repository_prefix
  subnet_id             = module.network.public_subnet_id
  security_group_id     = module.network.app_security_group_id
  media_bucket_arn      = module.storage.media_bucket_arn
  backups_bucket_arn    = module.storage.backups_bucket_arn
  ssm_parameter_path    = "/brand-clothing/staging"

  instance_type    = "t4g.micro"
  root_volume_size = 12
  data_volume_size = 10

  # Same compose + nginx as prod. Memory limits come from SSM
  # (WEB_MEM_LIMIT / DB_MEM_LIMIT) to fit 1 GB.
  compose_file = file("${path.root}/../../../docker-compose.prod.yml")
  nginx_conf   = file("${path.root}/../../../nginx/default.conf")

  instance_count = 1

  # Weekdays 08:00-20:00 Kyiv time. Outside that the ASG is at 0.
  schedule = {
    start_cron = "0 8 * * MON-FRI"
    stop_cron  = "0 20 * * MON-FRI"
    time_zone  = "Europe/Kyiv"
  }
}

# The GitHub OIDC provider is account-wide and managed in environments/prod.
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

module "deploy_role" {
  source = "../../modules/deploy-role"

  name               = "${var.project_name}-github-deploy"
  oidc_provider_arn  = data.aws_iam_openid_connect_provider.github.arn
  github_subject     = "repo:MateTeam251@327962530/brand-clothing-tp251@1350646589"
  github_environment = "staging"
  ssm_parameter_path = "/brand-clothing/staging"
  instance_role_tag  = module.compute.role_tag
}

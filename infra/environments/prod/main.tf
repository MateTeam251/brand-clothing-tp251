########################################################################
# prod environment — foundation pass
#
# What this wires up today: AWS Budget alert, network module, storage
# module. Deliberately NOT included yet: compute (app EC2), monitoring
# (second EC2), database (WAL-archiving user-data), dns (Route 53).
# Those land as their own modules once this foundation is reviewed —
# see infra/README.md for the sequencing this follows.
########################################################################

module "network" {
  source = "../../modules/network"

  project_name = var.project_name
}

module "storage" {
  source = "../../modules/storage"

  project_name  = var.project_name
  bucket_suffix = var.bucket_suffix

  app_role_enabled = true
  app_iam_role_arn = module.compute.app_role_arn
}

module "cicd_oidc" {
  source = "../../modules/cicd-oidc"

  project_name = var.project_name
  github_org   = var.github_org
  github_repo  = var.github_repo

  # First apply in a fresh AWS account: leave this true. If this AWS
  # account already has a GitHub OIDC provider from another project,
  # set create_oidc_provider = false and pass its ARN via
  # existing_oidc_provider_arn instead — see modules/cicd-oidc/variables.tf.
  create_oidc_provider = var.create_oidc_provider
}

module "ecr" {
  source = "../../modules/ecr"

  project_name      = var.project_name
  github_org        = var.github_org
  github_repo       = var.github_repo
  oidc_provider_arn = module.cicd_oidc.oidc_provider_arn

  # The org's OIDC tokens carry numeric IDs in the sub claim
  # (repo:MateTeam251@<org id>/brand-clothing-tp251@<repo id>:ref:...).
  # Not secret - GitHub exposes both IDs publicly.
  github_owner_id = "327962530"
  github_repo_id  = "1350646589"
}

module "compute" {
  source = "../../modules/compute"

  project_name       = var.project_name
  subnet_id          = module.network.public_subnet_id
  security_group_id  = module.network.app_security_group_id
  media_bucket_arn   = module.storage.media_bucket_arn
  backups_bucket_arn = module.storage.backups_bucket_arn

  # 0 until user-data lands
  instance_count = 0
}

########################################################################
# Budget alert — sequencing step 1 in infrastructure-plan.md, done here
# in Terraform rather than by hand so it's version-controlled and
# reviewable like everything else.
########################################################################

resource "aws_budgets_budget" "monthly_cap" {
  name         = "${var.project_name}-monthly-cap"
  budget_type  = "COST"
  limit_amount = tostring(var.budget_limit_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.budget_alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_alert_email]
  }
}

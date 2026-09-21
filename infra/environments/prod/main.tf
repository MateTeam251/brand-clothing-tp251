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

  # app_iam_role_arn intentionally left unset (null) — the compute
  # module that creates App-EC2-Role doesn't exist yet in this pass.
  # Once it does, pass its ARN here and re-apply; the bucket policies
  # in the storage module activate automatically.
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

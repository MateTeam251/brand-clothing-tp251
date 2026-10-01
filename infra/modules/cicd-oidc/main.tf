########################################################################
# GitHub Actions OIDC provider (account-wide, one per account).
#
# GitHub mints a short-lived OIDC token per workflow run; AWS roles trust
# this provider instead of storing access keys in GitHub. The roles
# themselves live elsewhere: ECR push (modules/ecr), deploy
# (modules/deploy-role), Terraform plan/apply (infra/bootstrap).
########################################################################

data "tls_certificate" "github" {
  count = var.create_oidc_provider ? 1 : 0
  url   = "https://token.actions.githubusercontent.com/.well-known/openid-configuration"
}

resource "aws_iam_openid_connect_provider" "github" {
  count = var.create_oidc_provider ? 1 : 0

  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.github[0].certificates[0].sha1_fingerprint]
}

locals {
  oidc_provider_arn = var.create_oidc_provider ? aws_iam_openid_connect_provider.github[0].arn : var.existing_oidc_provider_arn
}

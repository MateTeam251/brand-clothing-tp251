output "github_actions_role_arn" {
  description = "Put this in the GitHub repo/environment variable AWS_ROLE_ARN — the workflow assumes this role via OIDC."
  value       = aws_iam_role.github_actions_terraform.arn
}

output "oidc_provider_arn" {
  value = local.oidc_provider_arn
}

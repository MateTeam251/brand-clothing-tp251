output "vpc_id" {
  value = module.network.vpc_id
}

output "public_subnet_id" {
  value = module.network.public_subnet_id
}

output "app_security_group_id" {
  value = module.network.app_security_group_id
}

output "monitoring_security_group_id" {
  value = module.network.monitoring_security_group_id
}

output "frontend_bucket_name" {
  value = module.storage.frontend_bucket_name
}

output "media_bucket_name" {
  value = module.storage.media_bucket_name
}

output "backups_bucket_name" {
  value = module.storage.backups_bucket_name
}

output "github_actions_role_arn" {
  description = "Set this as the AWS_ROLE_ARN GitHub Environment variable."
  value       = module.cicd_oidc.github_actions_role_arn
}

output "cloudfront_domain_name" {
  description = "Point your DNS (or just visit directly for now) at this — the *.cloudfront.net URL until Route 53 is set up."
  value       = module.storage.cloudfront_domain_name
}

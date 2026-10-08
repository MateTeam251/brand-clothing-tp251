output "app_public_ip" {
  value = module.compute.app_public_ip
}

output "asg_name" {
  value = module.compute.asg_name
}

output "media_bucket_name" {
  value = module.storage.media_bucket_name
}

output "backups_bucket_name" {
  value = module.storage.backups_bucket_name
}

output "frontend_bucket_name" {
  value = module.storage.frontend_bucket_name
}

output "cloudfront_domain_name" {
  value = module.storage.cloudfront_domain_name
}

output "deploy_role_arn" {
  description = "GitHub Environment \"staging\" -> variable AWS_DEPLOY_ROLE_ARN."
  value       = module.deploy_role.role_arn
}

output "cloudfront_distribution_id" {
  value = module.storage.cloudfront_distribution_id
}

output "site_url" {
  value = "https://${local.site_host}"
}

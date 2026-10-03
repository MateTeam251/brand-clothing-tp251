output "asg_name" {
  value = module.compute.asg_name
}

output "vpc_id" {
  value = module.network.vpc_id
}

output "public_subnet_id" {
  value = module.network.public_subnet_id
}

output "app_security_group_id" {
  value = module.network.app_security_group_id
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

output "cloudfront_domain_name" {
  description = "Point your DNS (or just visit directly for now) at this — the *.cloudfront.net URL until Route 53 is set up."
  value       = module.storage.cloudfront_domain_name
}

output "ecr_repository_urls" {
  value = module.ecr.repository_urls
}

output "ecr_push_role_arn" {
  value = module.ecr.push_role_arn
}

output "app_public_ip" {
  value = module.compute.app_public_ip
}

output "deploy_role_arn" {
  description = "GitHub Environment \"production\" -> variable AWS_DEPLOY_ROLE_ARN."
  value       = module.deploy_role.role_arn
}

output "name_servers" {
  value = aws_route53_zone.main.name_servers
}

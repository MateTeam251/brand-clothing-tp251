output "repository_urls" {
  value = { for k, r in aws_ecr_repository.this : k => r.repository_url }
}

output "repository_arns" {
  value = { for k, r in aws_ecr_repository.this : k => r.arn }
}

output "push_role_arn" {
  description = "Set as the AWS_ECR_PUSH_ROLE_ARN variable in GitHub."
  value       = aws_iam_role.push.arn
}
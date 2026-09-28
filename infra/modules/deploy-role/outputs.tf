output "role_arn" {
  description = "Set as the AWS_DEPLOY_ROLE_ARN variable of the matching GitHub Environment."
  value       = aws_iam_role.this.arn
}

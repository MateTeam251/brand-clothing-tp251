output "app_role_arn" {
  value = aws_iam_role.app.arn
}

output "app_public_ip" {
  description = "Elastic IP. DNS A record target."
  value       = aws_eip.app.public_ip
}

output "eip_allocation_id" {
  value = aws_eip.app.allocation_id
}

output "data_volume_id" {
  value = aws_ebs_volume.data.id
}

output "asg_name" {
  value = aws_autoscaling_group.app.name
}
output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_id" {
  value = aws_subnet.public.id
}

output "app_security_group_id" {
  description = "sg-app — attach to the app EC2 instance in the compute module."
  value       = aws_security_group.app.id
}

output "monitoring_security_group_id" {
  description = "sg-monitoring — attach to the monitoring EC2 instance in the monitoring module."
  value       = aws_security_group.monitoring.id
}

data "aws_subnet" "app" {
  id = var.subnet_id
}

resource "aws_eip" "app" {
  domain = "vpc"

  tags = {
    Name = "${var.project_name}-app-eip"
  }

  # DNS will point here; a new address means a DNS change.
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_ebs_volume" "data" {
  availability_zone = data.aws_subnet.app.availability_zone
  size              = var.data_volume_size
  type              = "gp3"
  encrypted         = true

  tags = {
    Name = "${var.project_name}-app-data"
  }

  # Holds the Postgres data directory.
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_launch_template" "app" {
  name_prefix            = "${var.project_name}-app-"
  image_id               = var.ami_id
  instance_type          = var.instance_type
  vpc_security_group_ids = [var.security_group_id]
  user_data = base64encode(templatefile("${path.module}/user-data.sh.tftpl", {
    region             = local.region
    data_volume_id     = aws_ebs_volume.data.id
    eip_allocation_id  = aws_eip.app.allocation_id
    ssm_parameter_path = var.ssm_parameter_path
    ecr_registry       = "${local.account_id}.dkr.ecr.${local.region}.amazonaws.com"
    compose_version    = var.compose_version
    compose_file       = var.compose_file
    nginx_conf         = var.nginx_conf
  }))
  update_default_version = true

  iam_instance_profile {
    arn = aws_iam_instance_profile.app.arn
  }

  # IMDSv2 only. Hop limit 2 so containers (WAL-G, django-ses, boto3) can
  # reach the instance role credentials through the Docker bridge.
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
    instance_metadata_tags      = "enabled"
  }

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size           = var.root_volume_size
      volume_type           = "gp3"
      encrypted             = true
      delete_on_termination = true
    }
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name          = "${var.project_name}-app"
      Role          = local.role_tag
      SessionAccess = "developers" # devs' Session Manager policy matches this tag
    }
  }

  tag_specifications {
    resource_type = "volume"
    tags = {
      Name = "${var.project_name}-app-root"
    }
  }
}

# Self-healing single instance: if it dies, the ASG launches a replacement,
# and user-data re-attaches the data volume and the EIP.
resource "aws_autoscaling_group" "app" {
  name = "${var.project_name}-app"
  # With a schedule the ASG may sit at 0 overnight, so min is 0 and the
  # scheduled actions own desired_capacity.
  min_size                  = var.schedule == null ? var.instance_count : 0
  max_size                  = var.instance_count
  desired_capacity          = var.instance_count
  vpc_zone_identifier       = [var.subnet_id]
  health_check_type         = "EC2"
  health_check_grace_period = 300

  launch_template {
    id      = aws_launch_template.app.id
    version = aws_launch_template.app.latest_version
  }

  # Scheduled actions change desired_capacity; don't fight them on every apply.
  lifecycle {
    ignore_changes = [desired_capacity]
  }
}

# Optional working-hours schedule (staging). The data volume and EIP stay;
# the morning boot re-runs user-data and re-attaches both.
resource "aws_autoscaling_schedule" "start" {
  count = var.schedule == null ? 0 : 1

  scheduled_action_name  = "start-working-hours"
  autoscaling_group_name = aws_autoscaling_group.app.name
  recurrence             = var.schedule.start_cron
  time_zone              = var.schedule.time_zone
  min_size               = 0
  max_size               = var.instance_count
  desired_capacity       = var.instance_count
}

resource "aws_autoscaling_schedule" "stop" {
  count = var.schedule == null ? 0 : 1

  scheduled_action_name  = "stop-after-hours"
  autoscaling_group_name = aws_autoscaling_group.app.name
  recurrence             = var.schedule.stop_cron
  time_zone              = var.schedule.time_zone
  min_size               = 0
  max_size               = var.instance_count
  desired_capacity       = 0
}
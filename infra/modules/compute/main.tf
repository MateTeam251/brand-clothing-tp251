data "aws_subnet" "app" {
  id = var.subnet_id
}

# Latest Amazon Linux 2023 arm64 AMI. A new AMI only updates the launch
# template; the running instance is untouched until it's replaced.
data "aws_ssm_parameter" "al2023_arm64" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
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
  image_id               = nonsensitive(data.aws_ssm_parameter.al2023_arm64.value)
  instance_type          = var.instance_type
  vpc_security_group_ids = [var.security_group_id]
  user_data              = var.user_data == null ? null : base64encode(var.user_data)
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
  name                      = "${var.project_name}-app"
  min_size                  = var.instance_count
  max_size                  = var.instance_count
  desired_capacity          = var.instance_count
  vpc_zone_identifier       = [var.subnet_id]
  health_check_type         = "EC2"
  health_check_grace_period = 300

  launch_template {
    id      = aws_launch_template.app.id
    version = aws_launch_template.app.latest_version
  }
}
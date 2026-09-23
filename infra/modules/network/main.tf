########################################################################
# Network module
########################################################################

resource "aws_vpc" "main" {
  cidr_block                       = var.vpc_cidr
  enable_dns_support               = true
  enable_dns_hostnames             = true
  assign_generated_ipv6_cidr_block = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

resource "aws_subnet" "public" {
  vpc_id                          = aws_vpc.main.id
  cidr_block                      = var.public_subnet_cidr
  ipv6_cidr_block                 = cidrsubnet(aws_vpc.main.ipv6_cidr_block, 8, 1)
  availability_zone               = var.availability_zone
  map_public_ip_on_launch         = true
  assign_ipv6_address_on_creation = true

  tags = {
    Name = "${var.project_name}-public-subnet"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  route {
    ipv6_cidr_block = "::/0"
    gateway_id      = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

########################################################################
# Security groups
########################################################################

resource "aws_security_group" "app" {
  name        = "${var.project_name}-sg-app"
  description = "App EC2 instance: public HTTPS/HTTP in, exporter ports scoped to monitoring SG only, no SSH."
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-sg-app"
  }
}

resource "aws_security_group" "monitoring" {
  name        = "${var.project_name}-sg-monitoring"
  description = "Monitoring EC2 instance: Loki reachable from app SG only, Grafana/Prometheus reachable via SSM port-forward only (no public ingress rule)."
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-sg-monitoring"
  }
}

# --- sg-app ingress ---------------------------------------------------

resource "aws_vpc_security_group_ingress_rule" "app_https_v4" {
  security_group_id = aws_security_group.app.id
  description       = "HTTPS from the internet"
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "app_https_v6" {
  security_group_id = aws_security_group.app.id
  description       = "HTTPS from the internet (IPv6)"
  cidr_ipv6         = "::/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "app_http_v4" {
  security_group_id = aws_security_group.app.id
  description       = "HTTP - ACME challenge + redirect to HTTPS"
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "app_http_v6" {
  security_group_id = aws_security_group.app.id
  description       = "HTTP - ACME challenge + redirect to HTTPS (IPv6)"
  cidr_ipv6         = "::/0"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "app_exporters_from_monitoring" {
  for_each = toset(["9100", "9187", "8080"]) # node_exporter, postgres_exporter, cAdvisor

  security_group_id            = aws_security_group.app.id
  description                   = "Exporter scrape (port ${each.value}) - monitoring instance only"
  referenced_security_group_id = aws_security_group.monitoring.id
  from_port                     = tonumber(each.value)
  to_port                       = tonumber(each.value)
  ip_protocol                   = "tcp"
}

# No ingress rule for port 22 anywhere in this module — deliberate.
# Instance access is SSM Session Manager only (App-EC2-Role /
# Monitoring-EC2-Role both carry AmazonSSMManagedInstanceCore in the
# compute module, which isn't part of this "foundation" pass).

# --- sg-app egress ------------------------------------------------------

resource "aws_vpc_security_group_egress_rule" "app_egress_v4" {
  security_group_id = aws_security_group.app.id
  description       = "All outbound - ECR, S3, SSM, OS updates, ACME"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_vpc_security_group_egress_rule" "app_egress_v6" {
  security_group_id = aws_security_group.app.id
  description       = "All outbound (IPv6)"
  cidr_ipv6         = "::/0"
  ip_protocol       = "-1"
}

# --- sg-monitoring ingress ----------------------------------------------

resource "aws_vpc_security_group_ingress_rule" "monitoring_loki_from_app" {
  security_group_id            = aws_security_group.monitoring.id
  description                   = "promtail (app instance) to Loki"
  referenced_security_group_id = aws_security_group.app.id
  from_port                     = 3100
  to_port                       = 3100
  ip_protocol                   = "tcp"
}

# No ingress rule for 3000 (Grafana), 9090 (Prometheus) or 22 (SSH).
# Grafana/Prometheus are reached only via `aws ssm start-session` port
# forwarding from an operator's machine — never exposed to the internet
# or even to the VPC at large.

# --- sg-monitoring egress -------------------------------------------------

resource "aws_vpc_security_group_egress_rule" "monitoring_egress_v4" {
  security_group_id = aws_security_group.monitoring.id
  description       = "All outbound - updates, container pulls, Telegram alert API, SSM"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_vpc_security_group_egress_rule" "monitoring_egress_v6" {
  security_group_id = aws_security_group.monitoring.id
  description       = "All outbound (IPv6)"
  cidr_ipv6         = "::/0"
  ip_protocol       = "-1"
}

# Shared by both environments; staging finds it by name. Registered at
# GoDaddy, which points to the name servers in output "name_servers".
resource "aws_route53_zone" "main" {
  name = "theart-theartist.com"

  lifecycle {
    prevent_destroy = true
  }
}

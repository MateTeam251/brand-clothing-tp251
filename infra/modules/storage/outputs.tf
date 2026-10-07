output "frontend_bucket_name" {
  value = aws_s3_bucket.frontend.id
}

output "media_bucket_name" {
  value = aws_s3_bucket.media.id
}

output "backups_bucket_name" {
  value = aws_s3_bucket.backups.id
}

output "backups_bucket_arn" {
  value = aws_s3_bucket.backups.arn
}

output "media_bucket_arn" {
  value = aws_s3_bucket.media.arn
}

output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.frontend.domain_name
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.frontend.id
}

output "reports_bucket_name" {
  value = aws_s3_bucket.reports.id
}

output "reports_bucket_arn" {
  value = aws_s3_bucket.reports.arn
}

output "cloudfront_hosted_zone_id" {
  value = aws_cloudfront_distribution.frontend.hosted_zone_id
}

output "frontend_bucket_arn" {
  value = aws_s3_bucket.frontend.arn
}

output "cloudfront_distribution_arn" {
  value = aws_cloudfront_distribution.frontend.arn
}

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

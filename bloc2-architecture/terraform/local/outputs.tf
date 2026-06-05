output "buckets" {
  description = "Buckets gérés par Terraform"
  value       = sort([for b in minio_s3_bucket.this : b.bucket])
}

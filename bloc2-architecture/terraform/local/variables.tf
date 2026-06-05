variable "minio_server" {
  description = "MinIO endpoint host:port"
  type        = string
}
variable "minio_user" {
  description = "MinIO access key"
  type        = string
}
variable "minio_password" {
  description = "MinIO secret key"
  type        = string
  sensitive   = true
}

output "vpc" { value = google_compute_network.vpc.name }
output "gke_cluster" { value = google_container_cluster.gke.name }
output "sql_instance" { value = google_sql_database_instance.postgres.name }
output "gcs_buckets" { value = sort([for b in google_storage_bucket.this : b.name]) }

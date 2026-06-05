locals {
  gcs_buckets = ["miroir-products", "miroir-models", "miroir-raw", "miroir-artifacts"]
}

resource "google_storage_bucket" "this" {
  for_each                    = toset(local.gcs_buckets)
  name                        = "${var.project_id}-${each.value}"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false
}

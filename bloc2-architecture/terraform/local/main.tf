locals {
  buckets = ["miroir-products", "miroir-models", "miroir-raw", "miroir-artifacts"]
}

resource "minio_s3_bucket" "this" {
  for_each = toset(local.buckets)
  bucket   = each.value
}

import {
  to = minio_s3_bucket.this["miroir-products"]
  id = "miroir-products"
}

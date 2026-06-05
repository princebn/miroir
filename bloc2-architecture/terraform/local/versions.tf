terraform {
  required_version = ">= 1.5"
  required_providers {
    minio = {
      source  = "aminueza/minio"
      version = ">= 2.0"
    }
  }
}

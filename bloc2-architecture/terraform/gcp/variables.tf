variable "project_id" {
  type = string
}
variable "region" {
  type    = string
  default = "europe-west1"
}
variable "zone" {
  type    = string
  default = "europe-west1-b"
}
variable "db_password" {
  type      = string
  sensitive = true
}
variable "gke_machine_type" {
  type    = string
  default = "e2-standard-4"
}
variable "gke_node_count" {
  type    = number
  default = 2
}

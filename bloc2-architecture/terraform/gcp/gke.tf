resource "google_container_cluster" "gke" {
  name                     = "miroir-gke"
  location                 = var.region
  remove_default_node_pool = true
  initial_node_count       = 1
  network                  = google_compute_network.vpc.id
  subnetwork               = google_compute_subnetwork.subnet.id
  deletion_protection      = false
}

resource "google_container_node_pool" "primary" {
  name       = "miroir-pool"
  cluster    = google_container_cluster.gke.id
  location   = var.region
  node_count = var.gke_node_count
  node_config {
    machine_type = var.gke_machine_type
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
}

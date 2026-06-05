resource "google_sql_database_instance" "postgres" {
  name                = "miroir-postgres"
  database_version    = "POSTGRES_16"
  region              = var.region
  deletion_protection = false
  settings {
    tier = "db-custom-2-7680"
  }
}

resource "google_sql_database" "miroir" {
  name     = "miroir"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "app" {
  name     = "miroir"
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

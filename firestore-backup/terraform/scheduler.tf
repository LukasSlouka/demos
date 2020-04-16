resource "google_app_engine_application" "app" {
  project = var.project_id
  location_id = var.region
}


resource "google_cloud_scheduler_job" "firebase_backup_job" {
  name = "backup-firestore"
  description = "Performs periodic firestore backup"
  schedule = "0 0 * * *"
  time_zone = "Europe/Prague"
  attempt_deadline = "320s"

  http_target {
    http_method = "GET"
    uri = "https://${var.region}-${var.project_id}.cloudfunctions.net/backup_firestore"

    oidc_token {
      service_account_email = google_service_account.service_account_scheduler.email
    }
  }
}

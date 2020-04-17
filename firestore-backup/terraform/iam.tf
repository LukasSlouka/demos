// Cloud scheduler service account and roles
resource "google_service_account" "service_account_scheduler" {
  account_id = "scheduler-sa"
}

resource "google_service_account_key" "service_account_scheduler" {
  service_account_id = google_service_account.service_account_scheduler.name
}

resource "google_project_iam_member" "scheduler_sa_cloud_functions_developer_role" {
  role = "roles/cloudfunctions.invoker"
  member = "serviceAccount:${google_service_account.service_account_scheduler.email}"
  depends_on = [
    google_service_account_key.service_account_scheduler,
  ]
}

resource "google_project_iam_member" "scheduler_sa_cloud_scheduler_admin_role" {
  role = "roles/cloudscheduler.admin"
  member = "serviceAccount:${google_service_account.service_account_scheduler.email}"
  depends_on = [
    google_service_account_key.service_account_scheduler,
  ]
}

// Cloud build roles
resource "google_project_iam_member" "cloudbuild_cloud_functions_admin_role" {
  role = "roles/cloudfunctions.admin"
  member = "serviceAccount:${var.project_number}@cloudbuild.gserviceaccount.com"
  depends_on = [
    google_cloudbuild_trigger.deploy_firestore_backup_cf,
  ]
}

resource "google_project_iam_member" "cloudbuild_cloud_functions_developer_role" {
  role = "roles/cloudfunctions.developer"
  member = "serviceAccount:${var.project_number}@cloudbuild.gserviceaccount.com"
  depends_on = [
    google_cloudbuild_trigger.deploy_firestore_backup_cf,
  ]
}

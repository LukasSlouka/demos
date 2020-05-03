// Cloud scheduler service account and roles
resource "google_service_account" "task_api_service_account" {
  account_id = "tasks-sa"
}

resource "google_service_account_key" "task_api_service_account" {
  service_account_id = google_service_account.task_api_service_account.name
}

resource "google_project_iam_member" "task_api_sa_cloud_tasks_deleter" {
  role = "roles/cloudtasks.taskDeleter"
  member = "serviceAccount:${google_service_account.task_api_service_account.email}"
  depends_on = [
    google_service_account_key.task_api_service_account,
  ]
}

resource "google_project_iam_member" "task_api_sa_cloud_tasks_enqueuer" {
  role = "roles/cloudtasks.enqueuer"
  member = "serviceAccount:${google_service_account.task_api_service_account.email}"
  depends_on = [
    google_service_account_key.task_api_service_account,
  ]
}

resource "google_project_iam_member" "task_api_sa_cloud_function_invoker" {
  role = "roles/cloudfunctions.invoker"
  member = "serviceAccount:${google_service_account.task_api_service_account.email}"
  depends_on = [
    google_service_account_key.task_api_service_account,
  ]
}

// Cloud build roles
resource "google_project_iam_member" "cloudbuild_cloud_functions_admin_role" {
  role = "roles/cloudfunctions.admin"
  member = "serviceAccount:${var.project_number}@cloudbuild.gserviceaccount.com"
  depends_on = [
    google_cloudbuild_trigger.deploy_calendar_api_cf,
    google_cloudbuild_trigger.deploy_calendar_notification_cf,
  ]
}

resource "google_project_iam_member" "cloudbuild_cloud_functions_developer_role" {
  role = "roles/cloudfunctions.developer"
  member = "serviceAccount:${var.project_number}@cloudbuild.gserviceaccount.com"
  depends_on = [
    google_cloudbuild_trigger.deploy_calendar_api_cf,
    google_cloudbuild_trigger.deploy_calendar_notification_cf,
  ]
}

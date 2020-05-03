resource "google_cloud_tasks_queue" "slack_notifications" {
  name = "slack-notifications-queue"
  location = var.region
  depends_on = [
    google_project_service.cloudtasks
  ]
}

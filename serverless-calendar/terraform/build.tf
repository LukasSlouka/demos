resource "google_cloudbuild_trigger" "deploy_calendar_api_cf" {
  name = "deploy-calendar-api"
  description = "Deploys calendar API cloud function"
  filename = "serverless-calendar/api/cloudbuild.yaml"
  trigger_template {
    branch_name = "^master$"
    repo_name = var.build_github_repository
  }
  included_files = [
    "serverless-calendar/api/build/**",
    "serverless-calendar/api/main.py",
    "serverless-calendar/api/requirements.txt",
  ]
  substitutions = {
    _SERVICE_ACCOUNT_EMAIL = google_service_account.task_api_service_account.email
    _EVENT_CALLBACK_URL = "https://${var.region}-${var.project_id}.cloudfunctions.net/calendar_event_callback"
    _QUEUE_NAME = google_cloud_tasks_queue.slack_notifications.name
    _REGION = var.region
  }
}

resource "google_cloudbuild_trigger" "deploy_calendar_notification_cf" {
  name = "deploy-calendar-notification"
  description = "Deploys calendar event notification cloud function"
  filename = "serverless-calendar/event/cloudbuild.yaml"
  trigger_template {
    branch_name = "^master$"
    repo_name = var.build_github_repository
  }
  included_files = [
    "serverless-calendar/event/build/**",
    "serverless-calendar/event/main.py",
    "serverless-calendar/event/requirements.txt",
  ]
  substitutions = {
    _SLACK_API_TOKEN = var.slack_api_token
    _SLACK_CHANNEL = var.slack_notification_channel
    _SERVICE_ACCOUNT_EMAIL = google_service_account.task_api_service_account.email
    _EVENT_CALLBACK_URL = "https://${var.region}-${var.project_id}.cloudfunctions.net/calendar_event_callback"
    _QUEUE_NAME = google_cloud_tasks_queue.slack_notifications.name
    _REGION = var.region
  }
}

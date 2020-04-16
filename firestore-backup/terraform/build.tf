resource "google_cloudbuild_trigger" "deploy_firestore_backup_cf" {
  name = "deploy-fs-backup-cf"
  description = "Deploys firestore backup cloud function"
  filename = "firestore-backup/build/cloudbuild.yaml"
  trigger_template {
    branch_name = "^master$"
    repo_name = var.build_github_repository
  }
  included_files = [
    "firestore-backup/build/**",
    "firestore-backup/main.py",
    "firestore-backup/requirements.txt",
  ]
  substitutions = {
    _SLACK_API_TOKEN = var.slack_api_token
    _SLACK_CHANNEL = var.slack_notification_channel
    _BUCKET_NAME = google_storage_bucket.backup_bucket.name
    _REGION = var.region
  }
}

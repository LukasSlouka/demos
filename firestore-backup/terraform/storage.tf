resource "google_storage_bucket" "backup_bucket" {
  name = "fs-backups-${var.project_number}"
  location = var.region

  lifecycle_rule {
    action {
      type = "SetStorageClass"
      storage_class = "NEARLINE"
    }
    condition {
      age = 10
    }
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 60
      matches_storage_class = [
        "NEARLINE"
      ]
    }
  }
}

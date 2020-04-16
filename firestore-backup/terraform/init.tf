// Replace all placeholders in this file and store it as `init.tf` file

terraform {
  backend "gcs" {
    // replace with your globally unique bucket name
    bucket = "lukass-sandbox-tf-states"
    prefix = "firebase-backup"
  }
}

provider "google" {
  credentials = file("default_service_account.json")
  project = var.project_id
  region = var.region
}

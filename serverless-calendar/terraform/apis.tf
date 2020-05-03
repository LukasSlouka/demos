resource "google_project_service" "iam" {
  project = var.project_id
  service = "iam.googleapis.com"
  disable_dependent_services = true
}

resource "google_project_service" "service-management" {
  project = var.project_id
  service = "servicemanagement.googleapis.com"
  disable_dependent_services = true
}

resource "google_project_service" "cloudbuild" {
  project = var.project_id
  service = "cloudbuild.googleapis.com"
  disable_dependent_services = true
}

resource "google_project_service" "firestore" {
  project = var.project_id
  service = "firestore.googleapis.com"
  disable_dependent_services = true
}

resource "google_project_service" "service_control" {
  project = var.project_id
  service = "servicecontrol.googleapis.com"
  disable_dependent_services = true
}

resource "google_project_service" "cloudtasks" {
  project = var.project_id
  service = "cloudtasks.googleapis.com"
  disable_dependent_services = true
}

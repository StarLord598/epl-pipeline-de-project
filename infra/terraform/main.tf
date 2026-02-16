terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# --- BigQuery Datasets (Medallion Architecture) ---

resource "google_bigquery_dataset" "raw" {
  dataset_id    = "epl_raw"
  friendly_name = "EPL Raw (Bronze)"
  description   = "Raw ingested data from football APIs"
  location      = var.bq_location
}

resource "google_bigquery_dataset" "staging" {
  dataset_id    = "epl_staging"
  friendly_name = "EPL Staging (Silver)"
  description   = "Cleaned and deduplicated data (dbt views)"
  location      = var.bq_location
}

resource "google_bigquery_dataset" "mart" {
  dataset_id    = "epl_mart"
  friendly_name = "EPL Mart (Gold)"
  description   = "Business-ready tables for dashboard"
  location      = var.bq_location
}

# --- BigQuery Tables (Bronze Layer) ---

resource "google_bigquery_table" "fixtures" {
  dataset_id = google_bigquery_dataset.raw.dataset_id
  table_id   = "fixtures"

  time_partitioning {
    type  = "DAY"
    field = "ingested_at"
  }

  schema = file("schemas/fixtures.json")
}

resource "google_bigquery_table" "standings" {
  dataset_id = google_bigquery_dataset.raw.dataset_id
  table_id   = "standings"

  time_partitioning {
    type  = "DAY"
    field = "ingested_at"
  }

  schema = file("schemas/standings.json")
}

resource "google_bigquery_table" "top_scorers" {
  dataset_id = google_bigquery_dataset.raw.dataset_id
  table_id   = "top_scorers"

  time_partitioning {
    type  = "DAY"
    field = "ingested_at"
  }

  schema = file("schemas/top_scorers.json")
}

# --- Service Account for Airflow ---

resource "google_service_account" "airflow" {
  account_id   = "epl-pipeline-airflow"
  display_name = "EPL Pipeline Airflow"
}

resource "google_project_iam_member" "airflow_bq_admin" {
  project = var.project_id
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.airflow.email}"
}

resource "google_project_iam_member" "airflow_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.airflow.email}"
}

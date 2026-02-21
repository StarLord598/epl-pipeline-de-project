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

# ── BigQuery Datasets (Medallion Architecture) ─────────────────────────────────

resource "google_bigquery_dataset" "raw" {
  dataset_id    = "epl_raw"
  friendly_name = "EPL Raw (Bronze)"
  description   = "Raw ingested data from football APIs"
  location      = var.bq_location

  labels = {
    env     = "production"
    project = "epl-pipeline"
    layer   = "raw"
  }
}

resource "google_bigquery_dataset" "staging" {
  dataset_id    = "epl_staging"
  friendly_name = "EPL Staging (Silver)"
  description   = "Cleaned and deduplicated data (dbt views)"
  location      = var.bq_location

  labels = {
    env     = "production"
    project = "epl-pipeline"
    layer   = "staging"
  }
}

resource "google_bigquery_dataset" "mart" {
  dataset_id    = "epl_mart"
  friendly_name = "EPL Mart (Gold)"
  description   = "Business-ready tables for dashboard consumption"
  location      = var.bq_location

  labels = {
    env     = "production"
    project = "epl-pipeline"
    layer   = "mart"
  }
}

# ── BigQuery Tables (Bronze Layer) ─────────────────────────────────────────────

resource "google_bigquery_table" "matches" {
  dataset_id          = google_bigquery_dataset.raw.dataset_id
  table_id            = "matches"
  description         = "Raw EPL match results from football-data.co.uk"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "ingested_at"
  }

  clustering = ["season_id", "competition_id"]

  schema = file("schemas/matches.json")
}

resource "google_bigquery_table" "events" {
  dataset_id          = google_bigquery_dataset.raw.dataset_id
  table_id            = "events"
  description         = "Raw match events from StatsBomb Open Data"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "ingested_at"
  }

  clustering = ["match_id", "event_type"]

  schema = file("schemas/events.json")
}

resource "google_bigquery_table" "lineups" {
  dataset_id          = google_bigquery_dataset.raw.dataset_id
  table_id            = "lineups"
  description         = "Raw match lineups from StatsBomb Open Data"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "ingested_at"
  }

  schema = file("schemas/lineups.json")
}

resource "google_bigquery_table" "fixtures" {
  dataset_id          = google_bigquery_dataset.raw.dataset_id
  table_id            = "fixtures"
  description         = "Raw fixtures from football-data.org API"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "ingested_at"
  }

  schema = file("schemas/fixtures.json")
}

resource "google_bigquery_table" "standings" {
  dataset_id          = google_bigquery_dataset.raw.dataset_id
  table_id            = "standings"
  description         = "Raw standings from football-data.org API"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "ingested_at"
  }

  schema = file("schemas/standings.json")
}

resource "google_bigquery_table" "top_scorers" {
  dataset_id          = google_bigquery_dataset.raw.dataset_id
  table_id            = "top_scorers"
  description         = "Top scorers — known stats for 2023-24 season"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "ingested_at"
  }

  schema = file("schemas/top_scorers.json")
}

# ── Service Account for Pipeline + Airflow ─────────────────────────────────────

resource "google_service_account" "epl_pipeline" {
  account_id   = "epl-pipeline-sa"
  display_name = "EPL Pipeline Service Account"
  description  = "Used by Airflow, dbt, and pipeline scripts to access BigQuery"
}

resource "google_project_iam_member" "bq_admin" {
  project = var.project_id
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.epl_pipeline.email}"
}

resource "google_project_iam_member" "bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.epl_pipeline.email}"
}

resource "google_project_iam_member" "bq_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.epl_pipeline.email}"
}

# ── Service Account Key ─────────────────────────────────────────────────────────

resource "google_service_account_key" "epl_pipeline_key" {
  service_account_id = google_service_account.epl_pipeline.name
}

resource "local_file" "sa_key" {
  content  = base64decode(google_service_account_key.epl_pipeline_key.private_key)
  filename = "${path.root}/../../keys/epl-pipeline-sa.json"

  file_permission = "0600"
}

# ── Outputs ─────────────────────────────────────────────────────────────────────

output "project_id" {
  value       = var.project_id
  description = "GCP Project ID"
}

output "service_account_email" {
  value       = google_service_account.epl_pipeline.email
  description = "Service account email for pipeline"
}

output "bq_raw_dataset" {
  value       = google_bigquery_dataset.raw.dataset_id
  description = "BigQuery raw dataset ID"
}

output "bq_staging_dataset" {
  value       = google_bigquery_dataset.staging.dataset_id
  description = "BigQuery staging dataset ID"
}

output "bq_mart_dataset" {
  value       = google_bigquery_dataset.mart.dataset_id
  description = "BigQuery mart dataset ID"
}

output "sa_key_path" {
  value       = local_file.sa_key.filename
  description = "Path to service account key file"
  sensitive   = true
}

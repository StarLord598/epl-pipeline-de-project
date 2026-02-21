# ============================================================================
# EPL Analytics Pipeline — Makefile
# ============================================================================
# One-command interface for the entire pipeline.
#
# Quick start:
#   make setup       → install dependencies
#   make run         → full pipeline (ingest → transform → export)
#   make test        → run all tests (dbt + data quality)
#   make dashboard   → start the Next.js dashboard
#   make airflow-up  → start Airflow + Postgres in Docker
#   make all         → setup + run + test
# ============================================================================

.PHONY: all setup run test clean dashboard airflow-up airflow-down \
        ingest transform export lint ci docs help

SHELL := /bin/bash
VENV := venv313
PY := $(VENV)/bin/python3
DBT := cd dbt && EPL_DB_PATH=../data/epl_pipeline.duckdb DBT_TARGET=local
DB := data/epl_pipeline.duckdb

# Colors
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
NC     := \033[0m

# ── Help ─────────────────────────────────────────────────────────────────────

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-18s$(NC) %s\n", $$1, $$2}'

# ── Setup ────────────────────────────────────────────────────────────────────

setup: ## Install Python + Node dependencies
	@echo "$(GREEN)▸ Creating Python venv…$(NC)"
	python3 -m venv $(VENV)
	$(PY) -m pip install --upgrade pip -q
	$(PY) -m pip install -r requirements.txt -q
	@echo "$(GREEN)▸ Installing dashboard dependencies…$(NC)"
	cd dashboard && npm install --silent
	@echo "$(GREEN)✓ Setup complete$(NC)"

# ── Pipeline ─────────────────────────────────────────────────────────────────

all: setup run test ## Full pipeline: setup → run → test

run: ingest transform export ## Run full pipeline (ingest → dbt → export)
	@echo "$(GREEN)✓ Pipeline complete$(NC)"

ingest: ## Ingest data from all sources
	@echo "$(GREEN)▸ Ingesting StatsBomb events…$(NC)"
	$(PY) scripts/ingest_data.py
	@echo "$(GREEN)▸ Ingesting 2023-24 full season…$(NC)"
	$(PY) scripts/ingest_full_season.py

transform: ## Run dbt models (staging → mart)
	@echo "$(GREEN)▸ Running dbt…$(NC)"
	$(DBT) dbt deps --profiles-dir . -q
	$(DBT) dbt run --profiles-dir .
	@echo "$(GREEN)✓ dbt models built$(NC)"

export: ## Export DuckDB → dashboard JSON
	@echo "$(GREEN)▸ Exporting dashboard JSON…$(NC)"
	$(PY) scripts/export_json.py
	$(PY) scripts/export_live_json.py
	@echo "$(GREEN)✓ JSON exported to dashboard/public/data/$(NC)"

# ── Testing ──────────────────────────────────────────────────────────────────

test: test-dbt test-quality ## Run all tests
	@echo "$(GREEN)✓ All tests passed$(NC)"

test-dbt: ## Run dbt tests (19 assertions)
	@echo "$(GREEN)▸ Running dbt tests…$(NC)"
	$(DBT) dbt test --profiles-dir .

test-quality: ## Run data quality checks
	@echo "$(GREEN)▸ Running data quality checks…$(NC)"
	$(PY) scripts/data_quality_checks.py

test-freshness: ## Check source freshness (dbt source freshness)
	$(DBT) dbt source freshness --profiles-dir .

# ── Dashboard ────────────────────────────────────────────────────────────────

dashboard: ## Start Next.js dashboard (localhost:3000)
	@echo "$(GREEN)▸ Starting dashboard…$(NC)"
	cd dashboard && npm run dev

dashboard-build: ## Build dashboard for production
	cd dashboard && npm run build

# ── Airflow (Docker) ─────────────────────────────────────────────────────────

airflow-up: ## Start Airflow + Postgres via Docker Compose
	@echo "$(GREEN)▸ Starting Airflow…$(NC)"
	docker compose build
	docker compose up airflow-init
	docker compose up -d airflow-webserver airflow-scheduler
	@echo "$(GREEN)✓ Airflow UI: http://localhost:8080 (admin/admin)$(NC)"

airflow-down: ## Stop Airflow containers
	docker compose down

airflow-logs: ## Tail Airflow scheduler logs
	docker compose logs -f airflow-scheduler

# ── Code Quality ─────────────────────────────────────────────────────────────

lint: ## Lint Python + dbt
	@echo "$(GREEN)▸ Linting…$(NC)"
	$(PY) -m py_compile scripts/ingest_data.py
	$(PY) -m py_compile scripts/ingest_full_season.py
	$(PY) -m py_compile scripts/export_json.py
	$(DBT) dbt parse --profiles-dir . --no-partial-parse
	@echo "$(GREEN)✓ Lint passed$(NC)"

# ── Documentation ────────────────────────────────────────────────────────────

docs: ## Generate dbt docs (opens in browser)
	$(DBT) dbt docs generate --profiles-dir .
	@echo "$(GREEN)▸ Opening dbt docs…$(NC)"
	$(DBT) dbt docs serve --profiles-dir . --port 8001

# ── CI (mirrors GitHub Actions) ──────────────────────────────────────────────

ci: lint test-dbt test-quality ## Run full CI suite locally
	@echo "$(GREEN)✓ CI passed$(NC)"

# ── Cleanup ──────────────────────────────────────────────────────────────────

clean: ## Remove generated files (keeps raw data)
	rm -rf dbt/target dbt/dbt_packages dbt/logs
	rm -rf dashboard/.next
	@echo "$(YELLOW)▸ Cleaned build artifacts$(NC)"

nuke: ## Full reset (removes database + all generated files)
	@echo "$(RED)⚠ This will delete the database!$(NC)"
	@read -p "Continue? [y/N] " yn; [ "$$yn" = "y" ] && \
		rm -f $(DB) && rm -rf data/json/* && \
		echo "$(RED)✓ Nuked$(NC)" || echo "Cancelled"

.PHONY: help install report parse-event copy-report update-latest lint format clean

# === Configuration ===
ETL_DIST = etl/dist/events
DOCS_DIR = docs

# === Help ===
help:		## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# === ETL Commands ===
etl-install:		## Install Python dependencies
	cd etl && uv sync

etl-add:		## Add Python package: make etl-add PKG=requests
	cd etl && uv add $(PKG)

etl-lint:		## Lint Python code
	cd etl && uv run ruff check .
	cd etl && uv run ruff format --check .

etl-format:		## Format Python code
	cd etl && uv run ruff format .

etl-clean:		## Remove Python venv and locks
	cd etl && rm -rf .venv uv.lock

etl-parse:		## Parse event: make etl-parse HTML_FILE=etl/context/2026-02.html EVENT_ID=2026-02
	cd etl && uv run scripts/parse_event.py $(HTML_FILE) $(EVENT_ID)

# === Report Commands ===
copy-report:		## Copy generated report to docs: make copy-report EVENT_ID=2026-02
	@mkdir -p $(DOCS_DIR)/reports/$(EVENT_ID)
	@cp $(ETL_DIST)/$(EVENT_ID)-report.html $(DOCS_DIR)/reports/$(EVENT_ID)/index.html
	@echo "Report copied to $(DOCS_DIR)/reports/$(EVENT_ID)/index.html"

update-latest:		## Update docs/index.html to point to latest report: make update-latest EVENT_ID=2026-02
	@echo "Updating $(DOCS_DIR)/index.html to point to $(EVENT_ID)..."
	@sed -i '' 's|url=reports/[^/]*|url=reports/$(EVENT_ID)|' $(DOCS_DIR)/index.html
	@sed -i '' 's|href="reports/[^/]*|href="reports/$(EVENT_ID)|' $(DOCS_DIR)/index.html
	@echo "Redirect updated to reports/$(EVENT_ID)/"

report: etl-parse copy-report update-latest		## Full workflow: parse → copy → update redirect (HTML_FILE and EVENT_ID required)

# === Convenience Commands (aliases) ===
install: etl-install		## Install dependencies (alias)
parse-event: etl-parse		## Parse event (alias)
lint: etl-lint			## Lint code (alias)
format: etl-format		## Format code (alias)
clean: etl-clean		## Clean artifacts (alias)

# === Default target ===
.DEFAULT_GOAL := help

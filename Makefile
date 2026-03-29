.PHONY: help install report report-auto parse-event analyze-event render-report copy-report update-latest lint format clean etl-finalize etl-finalize-with-overrides

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

etl-analyze:		## Analyze event: make etl-analyze EVENT_ID=2026-02
	cd etl && uv run scripts/analyze_event.py $(EVENT_ID)

etl-render:		## Render report: make etl-render EVENT_ID=2026-02
	cd etl && uv run scripts/render_report.py $(EVENT_ID)

etl-finalize:		## Finalize analysis (auto → final, no overrides): make etl-finalize EVENT_ID=2026-02
	cd etl && uv run scripts/finalize_analysis.py $(EVENT_ID)

etl-finalize-with-overrides:		## Finalize with archetype overrides: make etl-finalize-with-overrides EVENT_ID=2026-02
	cd etl && uv run scripts/finalize_analysis.py $(EVENT_ID) --override-config etl/config/archetypes.json

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

report: etl-parse etl-analyze etl-finalize-with-overrides etl-render copy-report update-latest		## Full workflow with archetype overrides: parse → analyze → finalize → render → copy → update redirect (HTML_FILE and EVENT_ID required)

report-auto: etl-parse etl-analyze etl-finalize etl-render copy-report update-latest		## Full workflow without overrides: parse → analyze → finalize → render → copy → update redirect (HTML_FILE and EVENT_ID required)

# === Convenience Commands (aliases) ===
install: etl-install		## Install dependencies (alias)
parse-event: etl-parse		## Parse event (alias)
analyze-event: etl-analyze	## Analyze event (alias)
render-report: etl-render	## Render report (alias)
lint: etl-lint			## Lint code (alias)
format: etl-format		## Format code (alias)
clean: etl-clean		## Clean artifacts (alias)

# === Default target ===
.DEFAULT_GOAL := help

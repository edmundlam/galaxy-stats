.PHONY: help install dev build parse-event

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

etl-parse:		## Parse event: make etl-parse HTML_FILE=context/2026-02.html EVENT_ID=2026-02
	cd etl && uv run scripts/parse_event.py $(HTML_FILE) $(EVENT_ID)

# === Frontend Commands ===
frontend-install:	## Install Node dependencies
	cd frontend && npm install

frontend-add:		## Add Node package: make frontend-add PKG=vue
	cd frontend && npm add $(PKG)

frontend-dev:		## Start dev server
	cd frontend && npm run dev

frontend-build:		## Build for production
	cd frontend && npm run build

frontend-preview:	## Preview production build
	cd frontend && npm run preview

frontend-clean:		## Remove frontend build artifacts
	cd frontend && rm -rf node_modules .astro dist

# === Convenience Commands (aliases) ===
install: etl-install frontend-install		## Install all dependencies
dev: frontend-dev				## Start dev server (alias)
build: frontend-build				## Build for production (alias)
parse-event: etl-parse				## Parse event (alias)
lint: etl-lint					## Lint code (alias)
format: etl-format				## Format code (alias)
clean: etl-clean frontend-clean		## Clean all artifacts

# === Default target ===
.DEFAULT_GOAL := help

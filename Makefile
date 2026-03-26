.PHONY: install run test lint clean parse-event help

install:
	uv sync
	uv run pre-commit install

#run:
#	uv run python src/main.py
#
#test:
#	uv run pytest

lint:
	uv run ruff check --fix
	uv run ruff format

parse-event:
	@if [ -z "$(HTML_FILE)" ] || [ -z "$(EVENT_ID)" ]; then \
		echo "Usage: make parse-event HTML_FILE=context/2026-02.html EVENT_ID=2026-02"; \
		exit 1; \
	fi
	uv run python scripts/parse_event.py $(HTML_FILE) $(EVENT_ID)

clean:
	rm -rf .venv

help:
	@echo "Available targets:"
	@echo "  install      - Install dependencies and set up pre-commit hooks"
	@echo "  lint         - Run linter and formatter (ruff)"
	@echo "  parse-event  - Parse event HTML (usage: make parse-event HTML_FILE=... EVENT_ID=...)"
	@echo "  clean        - Remove virtual environment"
	@echo "  help         - Show this help message"

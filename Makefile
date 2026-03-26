.PHONY: install run test lint clean help

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

clean:
	rm -rf .venv

help:
	@echo "Available targets:"
	@echo "  install  - Install dependencies and create virtual environment"
	@echo "  run      - Run the bot"
	@echo "  test     - Run all tests"
	@echo "  lint     - Run linter and format checker"
	@echo "  clean    - Remove virtual environment"
	@echo "  help     - Show this help message"

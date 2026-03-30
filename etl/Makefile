.PHONY: help install report parse analyze render finalize lint format clean

# === Redirect to Root Makefile ===
#
# All project commands should be run from the repository root.
# This Makefile provides helpful reminders and redirects.
#
# Usage from root:
#   make install              # Install dependencies
#   make report HTML_FILE=context/2026-03.html EVENT_ID=2026-03
#   make etl-parse HTML_FILE=context/2026-03.html EVENT_ID=2026-03
#   make help                 # Show all commands
#
# Or from etl/ directory:
#   cd .. && make help

help:		## Show this help message
	@echo ""
	@echo "  ⚠️  Run make commands from the repository root, not from etl/"
	@echo ""
	@echo "  Change to root directory:"
	@echo "    cd .."
	@echo ""
	@echo "  Then run:"
	@echo "    make help              # Show all available commands"
	@echo "    make install           # Install Python dependencies"
	@echo "    make report ...        # Generate full report"
	@echo ""
	@echo "  Quick start:"
	@echo "    cd .. && make help"

# All other targets redirect to help
install report parse analyze render finalize lint format clean: help
	@echo "❌ Please run this command from the repository root: cd .. && make $@"
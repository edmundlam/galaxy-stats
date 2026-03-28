# Galaxy Stats

Meta analysis reports for "Once Upon a Galaxy" tournaments

## Structure

- **`etl/`**: Python scripts that parse event HTML into JSON reports
- **`docs/`**: Static HTML reports (served by GitHub Pages)
- **`Makefile`**: Root-level build automation

## Quick Start

```bash
# Install Python dependencies
make install

# Process event data and generate report
make report HTML=etl/context/2026-02.html EVENT_ID=2026-02
```

## Workflow

1. **Parse event HTML** → Generates report HTML:
   ```bash
   make parse-event HTML=etl/context/2026-02.html EVENT_ID=2026-02
   ```
   Output: `etl/dist/events/2026-02-report.html`

2. **Copy to docs** → Copies report to docs folder:
   ```bash
   make copy-report EVENT_ID=2026-02
   ```
   Result: `docs/reports/2026-02/index.html`

3. **Update redirect** → Points root to latest report:
   ```bash
   make update-latest EVENT_ID=2026-02
   ```

4. **Deploy** → Push to GitHub, auto-deploys via GitHub Pages

**Or do all three in one command:**
```bash
make report HTML=etl/context/2026-02.html EVENT_ID=2026-02
```

## Available Commands

Run `make help` to see all available commands, or use:

```bash
# ETL
make etl-install          # Install Python deps
make etl-parse            # Parse event HTML
make etl-lint             # Lint Python code
make etl-format           # Format Python code
make etl-add PKG=requests # Add Python package

# Reports
make report               # Full workflow: parse → copy → update redirect
make copy-report          # Copy generated report to docs/
make update-latest        # Update docs/index.html redirect to latest
```

## Development

For ETL work, you can work directly in the `etl/` directory:
```bash
cd etl
uv add requests                                # Add Python package
uv run scripts/parse_event.py context/2026-02.html 2026-02
```

## Project Overview

Galaxy Stats processes tournament statistics from galaxy.fun HTML files and generates standalone interactive HTML reports. Reports are static files requiring no build step and are served directly via GitHub Pages.

- **Python**: Event HTML parsing and report generation
- **HTML/CSS/JS**: Standalone interactive reports with embedded data

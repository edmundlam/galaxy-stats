# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Galaxy Stats generates standalone HTML reports for "Once Upon a Galaxy" tournament statistics. The project consists of:
- **Python ETL**: Parses event HTML from galaxy.fun into interactive HTML reports
- **Static HTML**: Self-contained reports with embedded CSS/JS (no build step required)
- **GitHub Pages**: Serves the `docs/` folder directly

## Development Commands

### Report Generation (via Makefile)

```bash
# Full workflow: parse event HTML → generate report → copy to docs → update redirect
make report HTML=etl/context/2026-02.html EVENT_ID=2026-02

# Individual steps
make parse-event HTML=etl/context/2026-02.html EVENT_ID=2026-02
make copy-report EVENT_ID=2026-02
make update-latest EVENT_ID=2026-02
```

### Python Tooling (via Makefile)

```bash
# Install Python dependencies
make install

# Run linter and formatter
make lint

# Format code
make format

# Remove virtual environment
make clean

# Show all available commands
make help
```

### Adding Python Dependencies

```bash
# From the etl/ directory
uv add <package>           # Runtime dependency
uv add <package> --dev     # Development dependency
```

## Architecture

### Directory Structure

```
galaxy-stats/
├── etl/                    # Python ETL pipeline
│   ├── scripts/
│   │   └── parse_event.py # Main parser script
│   ├── context/           # Source HTML files from galaxy.fun
│   └── dist/              # Generated reports (temporary)
│       └── events/
│           └── 2026-02-report.html
├── docs/                   # Static HTML reports (served by GitHub Pages)
│   ├── index.html         # Redirects to latest report
│   └── reports/
│       └── 2026-02/
│           └── index.html
└── Makefile               # Build automation
```

### Data Pipeline

Event HTML files are processed by `etl/scripts/parse_event.py`:

**Input:**
- Event HTML from galaxy.fun (stored in `etl/context/`)

**Output:**
- Standalone HTML report at `etl/dist/events/<event-id>-report.html`

**Workflow:**
1. Parser extracts tournament data (players, captains, decks)
2. Generates HTML report with embedded JSON data
3. Report is copied to `docs/reports/<event-id>/index.html`
4. Root redirect is updated to point to latest report

### Report Structure

Each report is a single, self-contained HTML file with:
- **Embedded CSS**: Dark theme with custom typography (Playfair Display, IBM Plex)
- **Embedded JSON**: Tournament data in a `DATA` constant
- **Interactive JavaScript**: Tab navigation, animated charts, toggle views
- **No external dependencies**: Works offline, no build step required

**Report Sections:**
- **Top Cards**: Bar chart showing card popularity across all winning decks
- **Card Archetypes**: Clustered cards (Treasures, Candy, Mage, Pirates, Animals, Fringe)
- **Captain Analysis**: Signature cards (lift) and best 12 picks per captain

### Parser Details

**Usage:**
```bash
# From repo root
make parse-event HTML=etl/context/2026-02.html EVENT_ID=2026-02

# Or from etl/ directory
uv run scripts/parse_event.py context/2026-02.html 2026-02
```

**What it extracts:**
- Event metadata (name, date, total champion count)
- Player records (username, captain card, deck cards)
- Card co-occurrence statistics for clustering
- Lift calculations for captain-card associations

## Adding New Reports

1. **Download event HTML** from galaxy.fun → save to `etl/context/2026-03.html`
2. **Generate report**:
   ```bash
   make report HTML=etl/context/2026-03.html EVENT_ID=2026-03
   ```
3. **Verify locally**: Open `docs/reports/2026-03/index.html` in browser
4. **Commit and push**: GitHub Pages will auto-deploy

The root `docs/index.html` will automatically redirect to your new report.

## Styling and Design

Reports use a consistent dark theme:
- **Background**: `#0d0f14` (deep blue-black)
- **Accent**: `#c8a96e` (gold for treasures/highlights)
- **Typography**: Playfair Display (headers), IBM Plex Mono (data), IBM Plex Sans (body)
- **Color coding**: Each archetype has a unique color (gold, pink, purple, blue, green, gray)

Modifications to report styling should be made in the parser's HTML template generation.
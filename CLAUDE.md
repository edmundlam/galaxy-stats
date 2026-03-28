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
# Full workflow: parse → analyze → render → copy → update redirect (5 steps)
make report HTML_FILE=context/2026-03.html EVENT_ID=2026-03

# Individual steps (run these if debugging)
make etl-parse HTML_FILE=context/2026-03.html EVENT_ID=2026-03
make etl-analyze EVENT_ID=2026-03
make etl-render EVENT_ID=2026-03
make copy-report EVENT_ID=2026-03
make update-latest EVENT_ID=2026-03
```

**Important:** Use `HTML_FILE=context/2026-03.html` (relative to etl/ directory), NOT `etl/context/2026-03.html`

### Python Tooling (via Makefile)

```bash
# Install Python dependencies (includes numpy, scipy for analysis)
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

**Dependencies:** The pipeline uses:
- `beautifulsoup4` - HTML parsing (Stage 1)
- `numpy` - Matrix operations (Stage 2)
- `scipy` - Hierarchical clustering (Stage 2)

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
│   │   ├── parse_event.py      # Step 1: Parse HTML → JSON (players, decks)
│   │   ├── analyze_event.py    # Step 2: Analyze JSON (clustering, lift, best12)
│   │   └── render_report.py    # Step 3: Render HTML from analysis
│   ├── context/               # Source HTML files from galaxy.fun
│   └── dist/                  # Intermediate analysis + final report
│       └── events/
│           ├── 2026-03.json           # Parsed event data
│           ├── 2026-03-analysis.json  # Analysis with clusters/lift
│           └── 2026-03-report.html    # Final HTML report
├── docs/                   # Static HTML reports (served by GitHub Pages)
│   ├── index.html         # Redirects to latest report
│   └── reports/
│       └── 2026-03/
│           └── index.html
└── Makefile               # Build automation
```

### Data Pipeline

Event HTML files are processed through a **3-stage ETL pipeline**:

**Stage 1: Parse** (`parse_event.py`)
- **Input:** Event HTML from galaxy.fun (stored in `etl/context/`)
- **Output:** `etl/dist/events/<event-id>.json` (raw event data)
- **What it does:** Extracts players, captains, decks, and card references

**Stage 2: Analyze** (`analyze_event.py`)
- **Input:** `etl/dist/events/<event-id>.json`
- **Output:** `etl/dist/events/<event-id>-analysis.json` (with clusters, lift, best12)
- **What it does:**
  - Hierarchical clustering (scipy) to group cards by co-occurrence
  - Lift calculations for captain-card associations
  - Best 12 analysis per captain
  - Auto-generates cluster labels from most frequent card

**Stage 3: Render** (`render_report.py`)
- **Input:** `etl/dist/events/<event-id>-analysis.json`
- **Output:** `etl/dist/events/<event-id>-report.html` (standalone HTML)
- **What it does:** Generates self-contained HTML with embedded CSS/JS/data

**Stages 4-5: Deploy**
- **Copy:** Moves report to `docs/reports/<event-id>/index.html`
- **Update:** Updates root `docs/index.html` redirect to latest event

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

### ETL Scripts Details

**parse_event.py (Stage 1)**
```bash
# From repo root
make etl-parse HTML_FILE=context/2026-03.html EVENT_ID=2026-03

# Or from etl/ directory
uv run scripts/parse_event.py context/2026-03.html 2026-03
```
Extracts: Event metadata, players, captains, decks, card references

**analyze_event.py (Stage 2)**
```bash
# From repo root
make etl-analyze EVENT_ID=2026-03

# Or from etl/ directory
uv run scripts/analyze_event.py 2026-03
```
Generates: Hierarchical clusters (6 by default), lift analysis, best12 per captain
Flags: `--clusters N` to adjust cluster count (default: 6)

**render_report.py (Stage 3)**
```bash
# From repo root
make etl-render EVENT_ID=2026-03

# Or from etl/ directory
uv run scripts/render_report.py 2026-03
```
Generates: Standalone HTML report with embedded CSS/JS/data

**Important:** The `analyze_event.py` script auto-generates cluster labels. If labels need adjustment:
1. Edit `etl/dist/events/<event-id>-analysis.json`
2. Re-run step 3: `make etl-render EVENT_ID=<event-id>`

## Adding New Reports

1. **Download event HTML** from galaxy.fun → save to `etl/context/2026-04.html`
2. **Generate report** (runs all 5 steps):
   ```bash
   make report HTML_FILE=context/2026-04.html EVENT_ID=2026-04
   ```
3. **Verify locally**: Open `docs/reports/2026-04/index.html` in browser
4. **Review cluster labels**: If auto-generated names need adjustment:
   - Edit `etl/dist/events/2026-04-analysis.json`
   - Re-run: `make etl-render EVENT_ID=2026-04`
   - Re-copy: `make copy-report EVENT_ID=2026-04`
5. **Commit and push**: GitHub Pages will auto-deploy

The root `docs/index.html` will automatically redirect to your new report.

## Styling and Design

Reports use a consistent dark theme:
- **Background**: `#0d0f14` (deep blue-black)
- **Accent**: `#c8a96e` (gold for treasures/highlights)
- **Typography**: Playfair Display (headers), IBM Plex Mono (data), IBM Plex Sans (body)
- **Color coding**: Each archetype has a unique color (gold, pink, purple, blue, green, gray)

Modifications to report styling should be made in `render_report.py`'s HTML template.

## Troubleshooting

**Issue:** Report renders with no CSS/styling
- **Cause:** Template has double braces `{{` instead of single `{`
- **Fix:** Check `render_report.py` template uses single braces for CSS/JS
- **Verification:** View page source and check `<style>` section has valid CSS

**Issue:** "File not found" error when parsing
- **Cause:** Incorrect HTML path (Makefile runs from `etl/` directory)
- **Fix:** Use `HTML_FILE=context/2026-03.html` NOT `HTML_FILE=etl/context/2026-03.html`

**Issue:** Placeholders like `{EVENT_NAME}` not replaced in output
- **Cause:** The `.replace()` line in `render_report.py` has wrong brace escaping
- **Fix:** Should be `f"{{{key}}}"` (triple braces) NOT `f"{{key}}"` (double)

**Issue:** Cluster names don't make sense
- **Cause:** Auto-generated labels are based on most frequent card in each cluster
- **Fix:** Manually edit cluster labels in `etl/dist/events/<event-id>-analysis.json` and re-render

**Issue:** Wrong event data showing in report
- **Cause:** Analysis JSON from previous run
- **Fix:** Delete `etl/dist/events/<event-id>-analysis.json` and re-run `make etl-analyze`
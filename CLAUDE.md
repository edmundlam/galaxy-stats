# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Galaxy Stats generates standalone HTML reports for "Once Upon a Galaxy" tournament statistics. The project consists of:
- **Python ETL**: Parses event HTML from galaxy.fun into interactive HTML reports
- **Static HTML**: Self-contained reports with embedded CSS/JS (no build step required)
- **GitHub Pages**: Serves the `docs/` folder directly

**Deployed site:** https://edmundlam.github.io/galaxy-stats

## Development Commands

**⚠️ CRITICAL:** Always run Makefile commands from the **repository root**, never from the `etl/` directory. The `etl/` folder has its own Makefile that will redirect you if you forget.

### Report Generation (via Makefile)

```bash
# Full workflow with archetype overrides: parse → analyze → finalize → render → copy → update (6 steps)
make report HTML_FILE=context/2026-03.html EVENT_ID=2026-03

# Full workflow without overrides (auto-generated clusters)
make report-auto HTML_FILE=context/2026-03.html EVENT_ID=2026-03

# Individual steps (run these if debugging)
make etl-parse HTML_FILE=context/2026-03.html EVENT_ID=2026-03
make etl-analyze EVENT_ID=2026-03
make etl-finalize-with-overrides EVENT_ID=2026-03  # or: make etl-finalize (no overrides)
make etl-render EVENT_ID=2026-03
make copy-report EVENT_ID=2026-03
make update-latest EVENT_ID=2026-03
```

**Important:** Use `HTML_FILE=context/2026-03.html` (relative to etl/ directory), NOT `etl/context/2026-03.html`

### Captain Pages (via Makefile)

```bash
# Regenerate all captain pages + sitemap (standalone; not part of make report)
make captains

# Render captain pages only (no sitemap)
make etl-render-captains
```

Captain pages aggregate winning decks across **all** events from `etl/dist/events/*/analysis.json` into `docs/captains/index.html` plus one `docs/captains/<slug>/index.html` per captain. Run `make captains` after any report change so the new month appears.

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

## SEO

Reports include automated SEO features:
- **`robots.txt`**: Allows all crawlers + references sitemap
- **`sitemap.xml`**: Auto-generated via `make generate-sitemap`
- **Meta tags**: Unique titles, descriptions, canonical links in each report

The sitemap is automatically updated during `make report` and `make report-auto`.

## Architecture

### Directory Structure

```
galaxy-stats/
├── etl/                    # Python ETL pipeline
│   ├── scripts/
│   │   ├── parse_event.py         # Step 1: Parse HTML → JSON (players, decks)
│   │   ├── analyze_event.py       # Step 2: Analyze JSON (clustering, lift, best12)
│   │   ├── finalize_analysis.py   # Step 3: Apply archetype overrides
│   │   └── render_report.py       # Step 4: Render HTML from analysis
│   ├── config/
│   │   └── archetypes.json        # Archetype override mappings
│   ├── context/                   # Source HTML files from galaxy.fun
│   └── dist/                      # Intermediate analysis + final report
│       └── events/
│           └── 2026-03/                   # Event-specific subdirectory
│               ├── event.json             # Parsed event data
│               ├── auto-analysis.json     # Auto-generated analysis
│               ├── analysis.json          # Final analysis (with overrides)
│               └── report.html            # Final HTML report
├── docs/                   # Static HTML reports (served by GitHub Pages)
│   ├── index.html         # Landing page: reports table + quick links
│   ├── about.html         # Methodology/technical details
│   ├── assets/            # Shared CSS/JS for reports + captain pages
│   ├── captains/          # Per-captain stats across all events
│   │   ├── index.html     # All-captains index with month filter
│   │   └── <slug>/index.html
│   └── reports/
│       └── 2026-03/
│           └── index.html
└── Makefile               # Build automation
```

### Data Pipeline

Event HTML files are processed through a **6-stage ETL pipeline**:

**Stage 1: Parse** (`parse_event.py`)
- **Input:** Event HTML from galaxy.fun (stored in `etl/context/`)
- **Output:** `etl/dist/events/<event-id>/event.json` (raw event data)
- **What it does:** Extracts players, captains, decks, and card references

**Stage 2: Analyze** (`analyze_event.py`)
- **Input:** `etl/dist/events/<event-id>/event.json`
- **Output:** `etl/dist/events/<event-id>/auto-analysis.json` (with clusters, lift, best12)
- **What it does:**
  - Hierarchical clustering (scipy) to group cards by co-occurrence
  - Lift calculations for captain-card associations
  - Best 12 analysis per captain
  - Auto-generates cluster labels from most frequent card

**Stage 3: Finalize** (`finalize_analysis.py`)
- **Input:** `etl/dist/events/<event-id>/auto-analysis.json`
- **Output:** `etl/dist/events/<event-id>/analysis.json` (with archetype overrides applied)
- **What it does:** Reassigns player archetypes based on `etl/config/archetypes.json` overrides
- **Two modes:** `etl-finalize` (no overrides) or `etl-finalize-with-overrides` (uses config)

**Stage 4: Render** (`render_report.py`)
- **Input:** `etl/dist/events/<event-id>/analysis.json`
- **Output:** `etl/dist/events/<event-id>/report.html` (standalone HTML)
- **What it does:** Generates self-contained HTML with embedded CSS/JS/data

**Stages 5-6: Deploy**
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
- **Card Archetypes**: Clustered cards (Treasures, Candy, Mage, Pirates, Animals, Toys)
- **Captain Analysis**: Signature cards (lift) and best 12 picks per captain

### ETL Scripts Details

See `.claude/reference/etl-scripts.md` for detailed script usage, flags, and adjusting archetype assignments.

## Adding New Reports

1. **Download event HTML** from galaxy.fun → save to `etl/context/2026-04.html`
2. **Generate report** (runs all 6 steps):
   - With archetype overrides: `make report HTML_FILE=context/2026-04.html EVENT_ID=2026-04`
   - Without overrides (auto-generated): `make report-auto HTML_FILE=context/2026-04.html EVENT_ID=2026-04`
3. **Verify locally**: Open `docs/reports/2026-04/index.html` in browser
4. **Review archetype assignments** (optional):
   - Check auto-generated clusters in `etl/dist/events/2026-04/auto-analysis.json`
   - Update `etl/config/archetypes.json` to add overrides
   - Re-run: `make etl-finalize-with-overrides EVENT_ID=2026-04` → `make etl-render EVENT_ID=2026-04` → `make copy-report EVENT_ID=2026-04`
5. **Regenerate captain pages**: `make captains` — `make report` does not refresh them, so the new month won't appear on captain pages without this. Month rows there link to the new report only once it's published in `docs/reports/`.
6. **Commit and push**: GitHub Pages will auto-deploy

The root `docs/index.html` will automatically redirect to your new report.

## Styling and Design

Reports use a consistent dark theme:
- **Background**: `#0d0f14` (deep blue-black)
- **Accent**: `#c8a96e` (gold for treasures/highlights)
- **Typography**: Playfair Display (headers), IBM Plex Mono (data), IBM Plex Sans (body)
- **Color coding**: Each archetype has a unique color (gold, pink, purple, blue, green, gray)

Modifications to report styling should be made in `render_report.py`'s HTML template.

## Skills

Project-specific skills are in `.claude/skills/`:
- `reddit-post` — Generate tournament meta posts for Reddit from analysis JSON

## Troubleshooting

See `.claude/reference/troubleshooting.md` for common issues and fixes.

## Agent skills

### Issue tracker

Issues and specs live as GitHub issues (using `gh` CLI). See `.claude/reference/issue-tracker.md`.

### Triage labels

Uses the five canonical triage roles: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. See `.claude/reference/triage-labels.md`.

### Domain docs

Single-context repo with `CONTEXT.md` and `docs/adr/` at the root. See `.claude/reference/domain.md`.


## Important Reminders:

- When running Makefile commands, ensure you are in the root directory of the repository (not inside `etl/`) to avoid path issues.
- When updating python files, remember to run `make lint` and `make format` to maintain code quality and consistency.
- ALWAYS use the `AskUserQuestion` tool when asking questions to the user.
- Do not commit unless asked to by the user.
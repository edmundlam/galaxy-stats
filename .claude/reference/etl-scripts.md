# ETL Scripts Reference

Detailed documentation for each ETL pipeline stage.

## parse_event.py (Stage 1)

**Purpose:** Extracts event data from HTML into structured JSON

```bash
# From repo root
make etl-parse HTML_FILE=context/2026-03.html EVENT_ID=2026-03

# Or from etl/ directory
uv run scripts/parse_event.py context/2026-03.html 2026-03
```

**Extracts:**
- Event metadata (name, date, location)
- Players (name, captain, deck)
- Captains (name, win rate)
- Decks (card lists)
- Card references (unique cards across all decks)

**Output:** `etl/dist/events/<event-id>/event.json`

---

## analyze_event.py (Stage 2)

**Purpose:** Analyze event data to generate clusters, lift, and best12

```bash
# From repo root
make etl-analyze EVENT_ID=2026-03

# Or from etl/ directory
uv run scripts/analyze_event.py 2026-03
```

**Generates:**
- Hierarchical clusters (6 by default) grouping cards by co-occurrence
- Lift analysis for captain-card associations
- Best 12 picks per captain

**Output:** `etl/dist/events/<event-id>/auto-analysis.json`

**Flags:**
- `--clusters N` - Adjust cluster count (default: 6)

---

## finalize_analysis.py (Stage 3)

**Purpose:** Apply archetype overrides from config

```bash
# From repo root (with overrides)
make etl-finalize-with-overrides EVENT_ID=2026-03

# Without overrides (auto-generated only)
make etl-finalize EVENT_ID=2026-03

# From etl/ directory
uv run scripts/finalize_analysis.py 2026-03 --override-config etl/config/archetypes.json
```

**What it does:**
- Reads auto-analysis.json
- Applies archetype mappings from `etl/config/archetypes.json`
- Reassigns player deck archetypes based on card composition

**Output:** `etl/dist/events/<event-id>/analysis.json`

**Two modes:**
- `etl-finalize` - No overrides, uses auto-generated clusters only
- `etl-finalize-with-overrides` - Applies `etl/config/archetypes.json` mappings

---

## render_report.py (Stage 4)

**Purpose:** Generate standalone HTML report

```bash
# From repo root
make etl-render EVENT_ID=2026-03

# Or from etl/ directory
uv run scripts/render_report.py 2026-03
```

**Generates:**
- Self-contained HTML with embedded CSS/JS/data
- Dark theme styling
- Interactive charts and tab navigation
- SEO meta tags (title, description, canonical)

**Output:** `etl/dist/events/<event-id>/report.html`

---

## render_captains.py (standalone)

**Purpose:** Generate per-captain stats pages aggregating winning decks across all events

```bash
# From repo root (renders pages + regenerates sitemap)
make captains

# Render only, no sitemap
make etl-render-captains

# From etl/ directory
uv run scripts/render_captains.py
```

**Reads:** every `etl/dist/events/*/analysis.json` + `etl/dist/captains.json` (captain name map)

**Generates:**
- `docs/captains/index.html` — all-captains table (months/winning decks), month filter chips defaulting to the last 2 months
- `docs/captains/<slug>/index.html` — one page per captain: Best Cards table (recomputed client-side from checked months; "Show 12 more" extends past the top 12, `ASSET_VERSION` in `render_captains.py` cache-busts `docs/assets/captains.js`) and full decklists

**Behavior notes:**
- Every captain in `captains.json` gets a page, even with no winning decks (empty state)
- Decklist month cells link to `../../reports/<event-id>/` only when that report exists in `docs/reports/`
- Not part of the 6-stage report pipeline — run `make captains` after adding or re-rendering reports

---

## Adjusting Archetype Assignments

To modify cluster assignments after analysis:

1. Edit `etl/config/archetypes.json` to add/modify card → archetype mappings
2. Re-run finalize: `make etl-finalize-with-overrides EVENT_ID=<event-id>`
3. Re-run render: `make etl-render EVENT_ID=<event-id>`
4. Re-copy: `make copy-report EVENT_ID=<event-id>`

# Captain Pages — Design Spec

**Date:** 2026-08-28
**Status:** Approved design, pending implementation plan

## Overview

One static HTML page per captain, aggregating that captain's data across all monthly
tournament reports. Slug = `etl/dist/captains.json` key with underscores replaced by
dashes. This is the "for now" version: each page embeds the captain's raw deck data
per month and renders two sortable/filterable tables. A refinement pass will iterate
on presentation.

## Goals

- `docs/captains/<slug>/index.html` for **all** captains in `captains.json` (93 today),
  including an empty state for captains with no recorded winning decks (8 today).
- `docs/captains/index.html` listing all captains with links (sortable table).
- Standalone `make captains` build target. Not wired into `make report`.
- Captain pages included in `sitemap.xml`.

## Non-goals (deferred to refinement pass)

- Links from monthly reports or the main page to captain pages.
- Signature/lift UI — and the signature data itself (see `context/TODO.md` for the
  future approach).
- Any per-captain narrative content or images.

## Data model

New script `etl/scripts/render_captains.py` reads every `etl/dist/events/*/analysis.json`
plus `etl/dist/captains.json` and builds, per captain:

```json
{
  "slug": "galileo-galilei",
  "name": "Galileo Galilei",
  "months": [
    {
      "id": "2026-08",
      "date": "2026-08-21",
      "event": "August Monthly",
      "players": [{ "username": "adub", "archetype": "Treasures", "deck": ["...", "..."] }]
    }
  ]
}
```

- `months` sorted chronologically ascending by `id`.
- `date` is the real event date from `analysis.json`'s `event.date` (no first-of-month
  normalization needed).
- Only `players` (decks) are copied from the event's `analysis.json`. Derived per-month
  fields are NOT embedded: `best12` is recomputed client-side from decks, and
  `signature` (lift) is excluded entirely — it needs event-wide base rates and is
  deferred to a future pass (see `context/TODO.md`). Deck card values in
  `analysis.json` are already display names — no `cards.json` lookup needed.
- If an analysis slug is missing from `captains.json`, still generate a page with
  `name` falling back to the slug (same fallback as `analyze_event.py`).

## Pages

### Per-captain page — `docs/captains/<slug>/index.html`

Self-contained HTML (embedded CSS/JS/data, no external dependencies, works offline),
styled like the existing reports: dark theme `#0d0f14`, gold accent `#c8a96e`,
Playfair Display / IBM Plex. Unique meta title, description, and canonical URL
(`https://edmundlam.github.io/galaxy-stats/captains/<slug>/`).

Content, in order:

1. **Header** — captain display name, total winning decks, months appeared.
2. **Month selector** — one checkbox chip per month the captain has data for, all
   checked by default. Drives the Best 12 table only.
3. **Best 12 table** — computed client-side from the raw decks of the selected
   months: count deck frequency per card across all selected months' decks, sort by
   freq descending, take top 12. Columns: Card | Freq | % (of selected decks).
   This matches `analyze_event.py` semantics (`calculate_captain_stats`): recomputing
   from raw decks is exact for any month subset; precomputed per-month best12 tables
   are NOT merged.
4. **Decklists table** — one row per winning deck across all months (not affected by
   the month selector). Columns: Month | Player | Archetype | Deck (12 cards).
   Sortable columns; single text filter box matching player, archetype, month, or any
   card name.
5. **Raw JSON** — collapsed `<details>` block containing the full pretty-printed
   page payload (captain + months + decks as defined above).

Empty state: header renders with "No winning decks recorded yet." and no tables.

### Index page — `docs/captains/index.html`

Sortable table: Captain (link) | Months (count) | Total winning decks. Rows sorted by
decks descending initially. Same theme; canonical
`https://edmundlam.github.io/galaxy-stats/captains/`.

## Implementation notes

- Embed data as `<script type="application/json" id="captain-data">`; escape `</`
  as `<\/` inside the serialized JSON so card names can't terminate the script tag.
- Slugs contain only `[a-z0-9-]` after conversion (keys are snake_case ASCII today);
  no URL-encoding required.
- Stale-page cleanup is out of scope: captain data only accumulates, and
  `make captains` regenerates the full set each run.

## Build & SEO

- `Makefile` target `captains`: runs `render_captains.py` over all events and writes
  `docs/captains/**`. Standalone; not added to `report`/`report-auto`.
- `generate_sitemap.py` extended to include `/captains/` and each `/captains/<slug>/`
  URL (same lastmod-from-mtime logic as reports). Still invoked via
  `make generate-sitemap`.
- Generated pages are committed (same as `docs/reports/**`).

## Files changed

| File | Change |
| --- | --- |
| `etl/scripts/render_captains.py` | New — aggregation + page rendering |
| `etl/tests/test_render_captains.py` | New — unit tests |
| `etl/scripts/generate_sitemap.py` | Include captains URLs |
| `Makefile` | Add `captains` target |
| `context/TODO.md` | New — deferred signature/lift approach (no code) |
| `docs/captains/**` | Generated, committed |

## Testing (TDD)

pytest (`etl/tests/`, framework already configured). Tests for:

1. **Slug conversion** — `galileo_galilei` → `galileo-galilei`; every current
   `captains.json` key round-trips to a filesystem-safe slug.
2. **Aggregation** — grouping across multiple events; month ordering ascending;
   `players` pass through unchanged; captain with no events yields empty `months`.
3. **Best 12 parity** — a Python mirror of the client-side algorithm (count → sort
   desc → top 12) reproduces `analyze_event.py`'s `best12` for a real single-month
   fixture, pinning the contract the JS must match.
4. **Rendering** — captain page contains the escaped JSON payload, decklist rows for
   every player, and the empty-state string for a captain with no data; index page
   links every captain.

Run via `cd etl && uv run pytest` plus `make lint`.
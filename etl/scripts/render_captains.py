#!/usr/bin/env python3
"""Render per-captain pages aggregating winning decks across all monthly reports.

Reads every etl/dist/events/*/analysis.json plus etl/dist/captains.json and writes
docs/captains/index.html plus docs/captains/<slug>/index.html for all captains,
including those with no recorded winning decks (empty state).

Output:
    - docs/captains/index.html - index of all captains
    - docs/captains/<slug>/index.html - one page per captain
"""

import argparse
import json
import sys
from html import escape
from pathlib import Path

BASE_URL = "https://edmundlam.github.io/galaxy-stats"
ASSET_VERSION = "2"
FONTS_HREF = (
    "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900"
    "&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500&display=swap"
)

# Extra CSS on top of the shared report stylesheet: tables and month chips.
EXTRA_CSS = """
  main { max-width: 1100px; }
  .data-table { width:100%; border-collapse:collapse; font-family:'IBM Plex Mono',monospace; font-size:11px; }
  .data-table th { text-align:left; font-size:10px; letter-spacing:2px; text-transform:uppercase;
                   color:var(--muted); padding:8px 10px; border-bottom:2px solid var(--border);
                   cursor:pointer; user-select:none; white-space:nowrap; }
  .data-table th:hover { color:var(--text); }
  .data-table th.no-sort { cursor:default; }
  .data-table th.no-sort:hover { color:var(--muted); }
  .data-table td { padding:7px 10px; border-bottom:1px solid var(--border); vertical-align:top; }
  .data-table tbody tr:hover { background:var(--surface); }
  .data-table td.num, .data-table th.num { text-align:right; }
  .month-chip { display:inline-flex; align-items:center; gap:6px; font-family:'IBM Plex Mono',monospace;
                font-size:10px; letter-spacing:1px; text-transform:uppercase; color:var(--muted);
                background:var(--surface2); border:1px solid var(--border); border-radius:2px;
                padding:5px 10px; cursor:pointer; transition:all 0.15s; }
  .month-chip:has(input:checked) { color:var(--accent); border-color:rgba(200,169,110,0.4);
                                   background:rgba(200,169,110,0.08); }
  .month-chip input { accent-color:var(--accent); margin:0; cursor:pointer; }
  a { color:var(--accent); text-decoration:none; }
  a:hover { text-decoration:underline; text-underline-offset:3px; }
  .empty-note { font-family:'IBM Plex Mono',monospace; font-size:12px; color:var(--muted);
                padding:12px 16px; border-left:2px solid var(--border); }
"""

# Shared client JS: sortable table headers ([data-sort] cells, numeric via td.num)
# and deck-list filtering (#deck-filter hides rows whose text doesn't match).
TABLE_JS = """
function sortTable(th) {
  const table = th.closest('table'), tbody = table.querySelector('tbody');
  const idx = Array.from(th.parentNode.children).indexOf(th);
  const dir = th.dataset.dir === 'asc' ? -1 : 1;
  table.querySelectorAll('th').forEach(h => h.removeAttribute('data-dir'));
  th.dataset.dir = dir === 1 ? 'asc' : 'desc';
  const rows = Array.from(tbody.rows);
  rows.sort((a, b) => {
    const av = a.cells[idx].dataset.v ?? a.cells[idx].textContent.trim();
    const bv = b.cells[idx].dataset.v ?? b.cells[idx].textContent.trim();
    const an = parseFloat(av), bn = parseFloat(bv);
    const cmp = (!isNaN(an) && !isNaN(bn) && /^[-\\d.]/.test(av) && /^[-\\d.]/.test(bv))
      ? an - bn : av.localeCompare(bv);
    return cmp * dir;
  });
  rows.forEach(r => tbody.appendChild(r));
}
document.querySelectorAll('th[data-sort]').forEach(th =>
  th.addEventListener('click', () => sortTable(th)));
const deckFilter = document.getElementById('deck-filter');
if (deckFilter) {
  deckFilter.addEventListener('input', () => {
    const q = deckFilter.value.toLowerCase();
    document.querySelectorAll('#deck-table tbody tr').forEach(tr => {
      tr.style.display = tr.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  });
}
"""

# Client JS for the Best 12 table: recompute from raw decks of the checked months.
# Mirrors etl/scripts/analyze_event.py calculate_captain_stats: presence-count per
# card, sort by freq desc with alphabetical tie-break, take top 12.
BEST12_JS = """
const CAPTAIN = JSON.parse(document.getElementById('captain-data').textContent);
function best12(decks) {
  const counts = {};
  decks.forEach(deck => new Set(deck).forEach(card => counts[card] = (counts[card] || 0) + 1));
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1))
    .slice(0, 12);
}
function renderBest12() {
  const selected = Array.from(document.querySelectorAll('#month-filter input:checked'))
    .map(cb => cb.dataset.month);
  const decks = CAPTAIN.months.filter(m => selected.includes(m.id)).flatMap(m => m.players.map(p => p.deck));
  const tbody = document.querySelector('#best12-table tbody');
  tbody.innerHTML = '';
  best12(decks).forEach(([card, freq]) => {
    const tr = document.createElement('tr');
    const tdCard = document.createElement('td');
    tdCard.textContent = card;
    const tdFreq = document.createElement('td');
    tdFreq.className = 'num';
    tdFreq.textContent = freq;
    const tdPct = document.createElement('td');
    tdPct.className = 'num';
    tdPct.textContent = decks.length ? Math.round(freq / decks.length * 100) + '%' : '-';
    tr.append(tdCard, tdFreq, tdPct);
    tbody.appendChild(tr);
  });
  document.querySelector('#best12-count').textContent = decks.length;
}
"""


# Client JS for the index page: rebuild the captain table from the checked month
# chips. Rows with no decks in the selection are hidden unless every month is
# checked (which restores the full all-time view, matching the static fallback).
INDEX_JS = """
const INDEX = JSON.parse(document.getElementById('captains-data').textContent);
function renderIndex() {
  const boxes = Array.from(document.querySelectorAll('#month-filter input'));
  const checked = boxes.filter(cb => cb.checked).map(cb => cb.dataset.month);
  const allChecked = checked.length === boxes.length;
  const rows = INDEX
    .map(c => {
      const ms = c.months.filter(m => checked.includes(m.id));
      return {
        name: c.name, slug: c.slug,
        months: ms.filter(m => m.decks > 0).length,
        decks: ms.reduce((sum, m) => sum + m.decks, 0),
      };
    })
    .sort((a, b) => b.decks - a.decks || a.name.localeCompare(b.name))
    .filter(r => allChecked || r.decks > 0);
  const tbody = document.querySelector('#index-table tbody');
  tbody.innerHTML = '';
  rows.forEach(r => {
    const tr = document.createElement('tr');
    const name = document.createElement('td');
    const a = document.createElement('a');
    a.href = r.slug + '/';
    a.textContent = r.name;
    name.appendChild(a);
    const months = document.createElement('td');
    months.className = 'num';
    months.textContent = r.months;
    const decks = document.createElement('td');
    decks.className = 'num';
    decks.textContent = r.decks;
    tr.append(name, months, decks);
    tbody.appendChild(tr);
  });
}
"""


def slug_to_dash(slug: str) -> str:
    """Convert a captain key to a URL slug (underscores become dashes).

    Args:
        slug: Captain key from captains.json (snake_case)

    Returns:
        Filesystem-safe slug containing only [a-z0-9-]
    """
    return slug.replace("_", "-")


def compute_best12(decks: list[list[str]]) -> list[dict]:
    """Compute best 12 cards from raw decks — Python mirror of the client JS.

    Counts deck presence per card, sorts by freq desc with alphabetical
    tie-break, takes top 12. Must match analyze_event.py's best12 for a
    single month (pinned by tests/test_render_captains.py).

    Args:
        decks: List of decks, each a list of card display names

    Returns:
        List of {card, freq, n, pct} dicts (n = deck count, pct = 0 decimals)
    """
    counts: dict[str, int] = {}
    for deck in decks:
        for card in set(deck):
            counts[card] = counts.get(card, 0) + 1
    n = len(decks)
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:12]
    return [{"card": card, "freq": freq, "n": n, "pct": round(freq / n * 100, 0)} for card, freq in ranked]


def load_analyses(events_dir: Path) -> list[dict]:
    """Load every event analysis, ordered by event directory name.

    Args:
        events_dir: Path to etl/dist/events

    Returns:
        List of parsed analysis.json dicts
    """
    if not events_dir.exists():
        return []
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(events_dir.glob("*/analysis.json"))]


def aggregate_captains(events_dir: Path, captains_file: Path) -> dict[str, dict]:
    """Aggregate per-captain deck data across all events.

    Every captain in captains.json gets an entry (with empty months if no
    data); analysis slugs missing from captains.json get entries whose name
    falls back to the slug (same behavior as analyze_event.py).

    Args:
        events_dir: Path to etl/dist/events
        captains_file: Path to etl/dist/captains.json

    Returns:
        Dict keyed by dashed slug: {slug, name, months: [{id, date, event, players}]}
    """
    captains_map = json.loads(captains_file.read_text(encoding="utf-8")) if captains_file.exists() else {}
    captains: dict[str, dict] = {}

    def entry(slug: str) -> dict:
        dashed = slug_to_dash(slug)
        if dashed not in captains:
            captains[dashed] = {"slug": dashed, "name": captains_map.get(slug, slug), "months": []}
        return captains[dashed]

    for slug in captains_map:
        entry(slug)

    for analysis in load_analyses(events_dir):
        event = analysis["event"]
        for captain in analysis["captains"]:
            entry(captain["slug"])["months"].append(
                {"id": event["id"], "date": event["date"], "event": event["name"], "players": captain["players"]}
            )

    for captain in captains.values():
        captain["months"].sort(key=lambda m: m["id"])
    return captains


def serialize_payload(payload: dict) -> str:
    """Serialize a page payload for embedding, escaping `</` so card names
    can't terminate the script tag.

    Args:
        payload: Page payload dict

    Returns:
        JSON string safe to embed in a script tag
    """
    return json.dumps(payload).replace("</", "<\\/")


def index_payload(captains: dict[str, dict]) -> list[dict]:
    """Reduce aggregated captains to the compact shape the index page needs.

    Args:
        captains: Aggregated captains dict from aggregate_captains

    Returns:
        List of {slug, name, months: [{id, decks}]} sorted by slug (decklists omitted)
    """
    return [
        {
            "slug": c["slug"],
            "name": c["name"],
            "months": [{"id": m["id"], "decks": len(m["players"])} for m in c["months"]],
        }
        for c in sorted(captains.values(), key=lambda c: c["slug"])
    ]


def _head(title: str, description: str, canonical: str, asset_prefix: str) -> str:
    """Shared document head for captain pages.

    Args:
        title: Page title
        description: Meta description
        canonical: Canonical URL
        asset_prefix: Relative prefix to docs/assets ("../" or "../../")

    Returns:
        HTML head string
    """
    return f"""<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
<link rel="canonical" href="{escape(canonical)}">
<meta name="robots" content="index, follow">
<link href="{FONTS_HREF}" rel="stylesheet">
<link rel="stylesheet" href="{asset_prefix}assets/galaxy-report.css?v={ASSET_VERSION}">
<style>{EXTRA_CSS}</style>
<script defer src="https://umami-taupe-gamma.vercel.app/script.js" data-website-id="a1be0c78-139e-413a-bb3c-e28b3b9dbe5c"></script>"""


def _deck_rows(captain: dict, report_ids: set[str] | None = None) -> str:
    """Render static decklist table rows for every winning deck.

    Month cells link to the event report; months without a published report
    stay plain text (all months link when report_ids is None).

    Args:
        captain: Aggregated captain dict
        report_ids: Event ids with a published report, or None for all

    Returns:
        HTML string of <tr> elements
    """
    rows = []
    for month in captain["months"]:
        month_id = escape(month["id"])
        if report_ids is None or month["id"] in report_ids:
            month_html = f'<a href="../../reports/{month_id}/">{month_id}</a>'
        else:
            month_html = month_id
        for player in month["players"]:
            pills = "".join(f'<span class="deck-pill">{escape(card)}</span>' for card in player["deck"])
            rows.append(
                f'<tr><td data-v="{month_id}">{month_html}</td>'
                f"<td>{escape(player['username'])}</td>"
                f"<td>{escape(player['archetype'])}</td>"
                f'<td><div class="deck-pills">{pills}</div></td></tr>'
            )
    return "\n        ".join(rows)


def _month_chips(month_ids: list[str], checked: set[str] | None = None) -> str:
    """Render month selector chips.

    Args:
        month_ids: Month ids in display order
        checked: Month ids to check (None = all checked)

    Returns:
        HTML string of label elements
    """
    return "".join(
        f'<label class="month-chip"><input type="checkbox"{" checked" if checked is None or m in checked else ""}'
        f' data-month="{escape(m)}">{escape(m)}</label>'
        for m in month_ids
    )


def render_captain_page(captain: dict, base_url: str, report_ids: set[str] | None = None) -> str:
    """Render one captain page.

    Args:
        captain: Aggregated captain dict from aggregate_captains
        base_url: Site base URL for canonical/meta
        report_ids: Event ids with a published report (month cells link
            only to those); None links every month

    Returns:
        Self-contained HTML page string
    """
    name = captain["name"]
    slug = captain["slug"]
    months = captain["months"]
    total_decks = sum(len(m["players"]) for m in months)
    payload = serialize_payload(captain)
    canonical = f"{base_url}/captains/{slug}/"
    description = (
        f"{name} captain statistics across Once Upon a Galaxy monthly tournaments: "
        f"{total_decks} winning decks across {len(months)} months, with best 12 cards and full decklists."
    )
    head = _head(f"{name} — Captain Stats | Galaxy Stats", description, canonical, "../../")

    if total_decks == 0:
        body = """
<main>
  <div class="section active">
    <div class="empty-note">No winning decks recorded yet.</div>
  </div>
</main>"""
        script = ""
    else:
        body = f"""
<main>
  <div class="section active">
    <div class="section-title">Best 12</div>
    <div class="section-desc">Most-picked cards across the checked months, recomputed from the raw decks
      below. Check or uncheck months to see how the picks shift.</div>
    <div class="captain-filter" id="month-filter">{_month_chips([m["id"] for m in captain["months"]])}</div>
    <table class="data-table" id="best12-table">
      <thead><tr><th data-sort="card">Card</th><th class="num" data-sort="freq">Freq</th>
        <th class="num no-sort">% of <span id="best12-count">0</span> decks</th></tr></thead>
      <tbody></tbody>
    </table>

    <div class="section-title" style="margin-top:48px">Decklists</div>
    <div class="section-desc">Every winning deck across all months.</div>
    <div class="captain-filter">
      <input id="deck-filter" class="filter-input" type="text"
        placeholder="Filter by player, archetype, month, or card…">
    </div>
    <table class="data-table" id="deck-table">
      <thead><tr><th data-sort="month">Month</th><th data-sort="player">Player</th>
        <th data-sort="archetype">Archetype</th><th class="no-sort">Deck</th></tr></thead>
      <tbody>
        {_deck_rows(captain, report_ids)}
      </tbody>
    </table>
  </div>
</main>"""
        script = (
            "<script>"
            f"{BEST12_JS}renderBest12();\n"
            "document.querySelectorAll('#month-filter input')"
            ".forEach(cb => cb.addEventListener('change', renderBest12));\n"
            f"{TABLE_JS}</script>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{head}
</head>
<body>
<header>
  <a href="../../index.html" class="event-label">Once Upon A Galaxy · Meta Analysis</a>
  <h1>{escape(name)}</h1>
  <div class="subtitle">Captain stats · <a href="../">all captains</a></div>
  <div class="stats-row">
    <div class="stat-item"><div class="stat-value">{total_decks}</div><div class="stat-label">Winning decks</div></div>
    <div class="stat-item"><div class="stat-value">{len(months)}</div><div class="stat-label">Months</div></div>
  </div>
</header>
{body}
<script type="application/json" id="captain-data">{payload}</script>
{script}
</body>
</html>"""


def render_index_page(captains: dict[str, dict], base_url: str) -> str:
    """Render the captains index page.

    Args:
        captains: Aggregated captains dict from aggregate_captains
        base_url: Site base URL for canonical/meta

    Returns:
        Self-contained HTML page string
    """
    canonical = f"{base_url}/captains/"
    head = _head(
        "OUAG Captains — All Captain Stats | Galaxy Stats",
        "All Once Upon a Galaxy captains with monthly tournament statistics: winning deck counts, "
        "best 12 cards, and full decklists per captain.",
        canonical,
        "../",
    )

    ranked = sorted(
        captains.values(),
        key=lambda c: (-sum(len(m["players"]) for m in c["months"]), c["name"]),
    )
    rows = "\n        ".join(
        f'<tr><td><a href="{escape(c["slug"])}/">{escape(c["name"])}</a></td>'
        f'<td class="num">{len(c["months"])}</td>'
        f'<td class="num">{sum(len(m["players"]) for m in c["months"])}</td></tr>'
        for c in ranked
    )
    month_ids = sorted({m["id"] for c in captains.values() for m in c["months"]})
    chips = _month_chips(month_ids, checked=set(month_ids[-2:]))
    payload = serialize_payload(index_payload(captains))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{head}
</head>
<body>
<header>
  <a href="../index.html" class="event-label">Once Upon A Galaxy · Meta Analysis</a>
  <h1>Captains</h1>
  <div class="subtitle">{len(captains)} captains · click a column to sort</div>
</header>
<main>
  <div class="section active">
    <div class="section-desc">Deck counts for the checked months; uncheck months to narrow the field.</div>
    <div class="captain-filter" id="month-filter">{chips}</div>
    <table class="data-table" id="index-table">
      <thead><tr><th data-sort="captain">Captain</th><th class="num" data-sort="months">Months</th>
        <th class="num" data-sort="decks">Winning decks</th></tr></thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </div>
</main>
<script type="application/json" id="captains-data">{payload}</script>
<script>{INDEX_JS}renderIndex();
document.querySelectorAll('#month-filter input').forEach(cb => cb.addEventListener('change', renderIndex));
{TABLE_JS}</script>
</body>
</html>"""


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate per-captain HTML pages")
    parser.add_argument("--dist-dir", default=None, help="Path to etl/dist (default: ../dist from script location)")
    parser.add_argument(
        "--docs-dir", default=None, help="Path to docs directory (default: ../../docs from script location)"
    )
    parser.add_argument("--base-url", default=BASE_URL, help=f"Base URL for the site (default: {BASE_URL})")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    dist_dir = Path(args.dist_dir) if args.dist_dir else script_dir.parent / "dist"
    docs_dir = Path(args.docs_dir) if args.docs_dir else script_dir.parent.parent / "docs"

    captains = aggregate_captains(dist_dir / "events", dist_dir / "captains.json")
    reports_dir = docs_dir / "reports"
    report_ids = {p.parent.name for p in reports_dir.glob("*/index.html")} if reports_dir.exists() else set()

    captains_root = docs_dir / "captains"
    captains_root.mkdir(parents=True, exist_ok=True)
    index_path = captains_root / "index.html"
    index_path.write_text(render_index_page(captains, args.base_url), encoding="utf-8")

    for captain in captains.values():
        captain_dir = captains_root / captain["slug"]
        captain_dir.mkdir(exist_ok=True)
        (captain_dir / "index.html").write_text(
            render_captain_page(captain, args.base_url, report_ids), encoding="utf-8"
        )

    with_decks = sum(1 for c in captains.values() if any(m["players"] for m in c["months"]))
    print(f"✓ Wrote {index_path}")
    print(f"✓ Wrote {len(captains)} captain pages ({with_decks} with data, {len(captains) - with_decks} empty)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

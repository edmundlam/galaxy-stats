#!/usr/bin/env python3
"""Render the cross-event player leaderboard page.

Reads every etl/dist/events/*/event.json, aggregates player finishes across all
events (gauntlet and monthly treated as one sequence), and writes an
intermediate artifact plus the static page.

Output:
    - etl/dist/leaderboard.json - full aggregation, top 100 per list
    - docs/leaderboard/index.html - static page embedding only what it displays

Every finisher won their own gauntlet, so a finish is a "win"; nothing here
implies a list or player is better than another.
"""

import argparse
import json
import sys
from html import escape
from pathlib import Path

BASE_URL = "https://www.galaxy-stats.com"
ASSET_VERSION = "7"
FONTS_HREF = (
    "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900"
    "&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500&display=swap"
)

# Generous artifact cutoffs; the rendered page trims to what it displays.
TOP_N = 100
PAGE_LISTS = {"most_wins": 10, "longest_streaks": 10, "active_streaks": 20, "podium": 3}
HISTORY_WINDOW = 12
LOYALTY_MIN = 3

# Extra CSS on top of the shared report stylesheet: the card grid, bar date
# overlays, the win-history grid and the record rows.
EXTRA_CSS = """
  main { max-width:1200px; }
  nav a { color:var(--muted); font-family:'IBM Plex Mono',monospace; font-size:12px; letter-spacing:2px;
          text-transform:uppercase; padding:16px 20px; border-bottom:2px solid transparent;
          white-space:nowrap; text-decoration:none; }
  nav a:hover { color:var(--text); }
  nav a.active { color:var(--accent); border-bottom-color:var(--accent); }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(420px,1fr)); gap:18px; }
  .cluster-card h2 { font-family:'Playfair Display',serif; font-size:19px; font-weight:700; margin-bottom:4px; }
  .card-desc { font-size:13px; color:var(--muted); margin-bottom:16px; line-height:1.6; }
  .bar-track { position:relative; }
  .bar-sub { position:absolute; left:8px; top:0; line-height:22px; font-family:'IBM Plex Mono',monospace;
             font-size:11px; color:#0d0f14; white-space:nowrap; }
  .hist { display:flex; flex-direction:column; gap:10px; }
  .hist-head, .hist-row { display:grid; grid-template-columns:110px 1fr 40px; gap:10px; align-items:center; }
  .hist-head span { font-family:'IBM Plex Mono',monospace; font-size:10px; color:var(--muted); text-align:center; }
  .cells { display:grid; gap:3px; }
  .cells i { display:block; height:20px; border-radius:2px; background:var(--surface2); border:1px solid var(--border); }
  .cells i.w { background:var(--accent); border-color:var(--accent); }
  .hist-row b { font-family:'IBM Plex Mono',monospace; font-size:12px; font-weight:500; white-space:nowrap;
                overflow:hidden; text-overflow:ellipsis; }
  .hist-row em { font-style:normal; font-family:'Playfair Display',serif; font-weight:700; color:var(--accent);
                 text-align:right; font-size:18px; }
  .rec { display:flex; justify-content:space-between; gap:12px; padding:10px 0; border-top:1px solid var(--border);
         align-items:baseline; }
  .rec:first-of-type { border-top:0; padding-top:0; }
  .rec b { font-family:'IBM Plex Mono',monospace; font-size:12px; font-weight:500; }
  .rec em { font-style:normal; font-family:'IBM Plex Mono',monospace; font-size:12px; color:var(--accent);
            text-align:right; }
  .rec-none { font-family:'IBM Plex Mono',monospace; font-size:12px; color:var(--muted); }
  @media(max-width:700px){
    .grid { grid-template-columns:1fr; }
    .hist-head, .hist-row { grid-template-columns:1fr 36px; gap:6px; }
    .hist-head > :first-child { display:none; }
    .hist-row b { grid-column:1/-1; }
    .hist-row .cells { grid-column:1; }
  }
"""


def load_aliases(path: Path) -> dict[str, str]:
    """Load the player alias map.

    Args:
        path: Path to etl/config/aliases.json

    Returns:
        Dict mapping a casefolded old username to the canonical display name,
        e.g. {"old name": "New Name"}. Starts empty; add renames as spotted.
        Missing file reads as an empty map.
    """
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_username(name: str, aliases: dict[str, str] | None = None) -> str:
    """Reduce a raw username to a match identity.

    Args:
        name: Raw username as written in event.json
        aliases: Optional alias map (casefolded old name -> canonical name)

    Returns:
        Trimmed, case-folded identity; alias hits fold to their canonical name
    """
    key = name.strip().casefold()
    if aliases:
        key = aliases.get(key, key).strip().casefold()
    return key


def load_events(events_dir: Path) -> list[dict]:
    """Load every parsed event, ordered by event directory name.

    Event totals are len(players) — event.json's total_champions has been
    wrong before (2026-02 claims 183, holds 138), so it is ignored.

    Args:
        events_dir: Path to etl/dist/events

    Returns:
        List of {id, name, date, short, total, players}, sorted by id — the
        append-only chronological source of truth every index refers to
    """
    events = []
    if not events_dir.exists():
        return events
    for path in sorted(events_dir.glob("*/event.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        event = data["event"]
        events.append(
            {
                "id": event["id"],
                "name": event["name"],
                "date": event["date"],
                "short": _month_short(event["date"]),
                "total": len(data["players"]),
                "players": data["players"],
            }
        )
    return events


_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _month_short(date: str) -> str:
    """Three-letter month label from an ISO date ("2026-04-18" -> "Apr")."""
    return _MONTHS[int(date[5:7]) - 1]


def build_event_list(events: list[dict]) -> list[dict]:
    """Reduce loaded events to the compact chronological list.

    Args:
        events: Loaded events from load_events

    Returns:
        List of {id, short, total} in chronological order
    """
    return [{"id": e["id"], "short": e["short"], "total": e["total"]} for e in sorted(events, key=lambda e: e["id"])]


def _runs(indices: list[int]) -> list[tuple[int, int]]:
    """Split a sorted index list into inclusive (start, end) consecutive runs."""
    runs: list[tuple[int, int]] = []
    for i in indices:
        if runs and runs[-1][1] == i - 1:
            runs[-1] = (runs[-1][0], i)
        else:
            runs.append((i, i))
    return runs


def _pct(part: int, total: int) -> int:
    """Percent as integer, rounded half-up (matches render_captains/JS Math.round)."""
    return int(part / total * 100 + 0.5) if total else 0


def compute_leaderboard(
    events: list[dict], aliases: dict[str, str] | None = None, captain_names: dict[str, str] | None = None
) -> dict:
    """Aggregate player finishes across all events.

    Args:
        events: Loaded events from load_events (chronological)
        aliases: Optional alias map for renames (see normalize_username)
        captain_names: Optional captain slug -> display name map for the
            loyalty record; slugs pass through when absent

    Returns:
        Dict with the full aggregation (top 100 per list): events, header
        stats, most_wins, longest_streaks, active_streaks (with per-event win
        history aligned to events) and the three record podiums
    """
    event_list = build_event_list(events)
    n_events = len(event_list)
    players: dict[str, dict] = {}

    for i, event in enumerate(sorted(events, key=lambda e: e["id"])):
        for p in event["players"]:
            raw = p["username"].strip().casefold()
            canonical = aliases.get(raw) if aliases else None
            identity = normalize_username(p["username"], aliases)
            entry = players.setdefault(identity, {"name": identity, "wins": 0, "indices": [], "captains": {}})
            entry["name"] = canonical if canonical else p["username"].strip()
            entry["wins"] += 1
            entry["indices"].append(i)
            entry["captains"][p["captain"]] = entry["captains"].get(p["captain"], 0) + 1

    all_runs: list[dict] = []
    active: list[dict] = []
    comebacks: list[dict] = []
    for identity, entry in players.items():
        indices = entry["indices"]
        for start, end in _runs(indices):
            run = {"name": entry["name"], "length": end - start + 1, "start": start, "end": end, "identity": identity}
            all_runs.append(run)
            if end == n_events - 1 and run["length"] >= 2:
                seen = set(indices)
                active.append({**run, "wins": [j in seen for j in range(n_events)]})
        gaps = [b - a - 1 for a, b in zip(indices, indices[1:])]
        gap = max(gaps, default=0)
        if gap:
            comebacks.append({"name": entry["name"], "gap": gap, "identity": identity})

    # Ties are alphabetical everywhere (resolved 2026-10-28); a player's two
    # equal-length runs order by start index.
    most_wins = sorted(players.items(), key=lambda kv: (-kv[1]["wins"], kv[1]["name"].casefold()))
    all_runs.sort(key=lambda r: (-r["length"], r["name"].casefold(), r["start"]))
    active.sort(key=lambda r: (-r["length"], r["name"].casefold()))
    comebacks.sort(key=lambda r: (-r["gap"], r["name"].casefold()))

    loyal = []
    for identity, entry in players.items():
        slug, wins = max(entry["captains"].items(), key=lambda kv: (kv[1], kv[0]))
        if wins >= LOYALTY_MIN:
            loyal.append({"name": entry["name"], "wins": wins, "captain": slug, "identity": identity})
    loyal.sort(key=lambda r: (-r["wins"], r["name"].casefold()))

    repeat = sum(1 for e in players.values() if e["wins"] >= 2)
    return {
        "events": event_list,
        "stats": {
            "players": len(players),
            "events": n_events,
            "longest_streak": max((r["length"] for r in all_runs), default=0),
            "repeat_pct": _pct(repeat, len(players)),
        },
        "most_wins": [{"name": e["name"], "wins": e["wins"]} for _, e in most_wins[:TOP_N]],
        "longest_streaks": [{k: r[k] for k in ("name", "length", "start", "end")} for r in all_runs[:TOP_N]],
        "active_streaks": [{"name": r["name"], "length": r["length"], "wins": r["wins"]} for r in active[:TOP_N]],
        "records": {
            "captains": [
                {"name": e["name"], "captains": len(e["captains"])}
                for _, e in sorted(players.items(), key=lambda kv: (-len(kv[1]["captains"]), kv[1]["name"].casefold()))[
                    : PAGE_LISTS["podium"]
                ]
            ],
            "loyal": [
                {
                    "name": r["name"],
                    "wins": r["wins"],
                    "captain": (captain_names or {}).get(r["captain"], r["captain"]),
                    "slug": r["captain"],
                }
                for r in loyal[: PAGE_LISTS["podium"]]
            ],
            "comeback": [{"name": r["name"], "gap": r["gap"]} for r in comebacks[: PAGE_LISTS["podium"]]],
        },
    }


def trim_embed(board: dict) -> dict:
    """Cut the full aggregation down to exactly what the page displays.

    Args:
        board: Full aggregation from compute_leaderboard

    Returns:
        Payload dict: header stats, 10 most-wins rows, 10 longest-streak rows
        (with month ranges), up to 20 active-streak players (histories windowed
        to the last 12 events), and the 3-row record podiums
    """
    window = board["events"][-HISTORY_WINDOW:]
    offset = len(board["events"]) - len(window)
    shorts = [e["short"] for e in board["events"]]
    streaks = [
        {"name": r["name"], "length": r["length"], "from": shorts[r["start"]], "to": shorts[r["end"]]}
        for r in board["longest_streaks"][: PAGE_LISTS["longest_streaks"]]
    ]
    return {
        "events": window,
        "stats": board["stats"],
        "most_wins": board["most_wins"][: PAGE_LISTS["most_wins"]],
        "longest_streaks": streaks,
        "active_streaks": [
            {**r, "wins": r["wins"][offset:]} for r in board["active_streaks"][: PAGE_LISTS["active_streaks"]]
        ],
        "records": board["records"],
    }


def serialize_payload(payload: dict) -> str:
    """Serialize a payload for embedding, escaping `</` so names can't end the script tag."""
    return json.dumps(payload).replace("</", "<\\/")


def _head(title: str, description: str, canonical: str) -> str:
    """Document head for the leaderboard page (same meta set as the captain pages)."""
    return f"""<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
<link rel="canonical" href="{escape(canonical)}">
<meta name="robots" content="index, follow">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#1c1747">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Galaxy Stats">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{escape(canonical)}">
<meta name="twitter:card" content="summary">
<link href="{FONTS_HREF}" rel="stylesheet">
<link rel="stylesheet" href="../assets/galaxy-report.css?v={ASSET_VERSION}">
<style>{EXTRA_CSS}</style>
<script defer src="https://umami-taupe-gamma.vercel.app/script.js" data-website-id="9d92bc0f-3019-480b-b295-2e79921d2792" data-domains="www.galaxy-stats.com"></script>"""


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def _bars(rows: list[tuple[str, int, str]], max_value: int, unit: str, top_bar: str, desc: str, heading: str) -> str:
    """One bar-chart card: rows of (name, value, sub-overlay), scaled to max_value."""
    chart = "\n".join(
        f'<div class="bar-row"><div class="bar-name" title="{escape(name)}">{escape(name)}</div>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{value / max_value * 100:.1f}%"></div>'
        f"{sub}</div>"
        f'<div class="bar-pct">{value}{unit}</div></div>'
        for name, value, sub in rows
    )
    return (
        f'<section class="cluster-card"><div class="cluster-top-bar" style="background:{top_bar}"></div>'
        f'<h2>{heading}</h2><p class="card-desc">{desc}</p>'
        f'<div class="bar-chart">{chart}</div></section>'
    )


def _range_label(short_from: str, short_to: str) -> str:
    return short_from if short_from == short_to else f"{short_from}–{short_to}"


def _active_card(active: list[dict], events: list[dict]) -> str:
    """Win-history grid card: one square per event, gold = finished."""
    cols = len(events)
    template = f"grid-template-columns:repeat({cols},1fr)"
    head = "".join(f"<span>{escape(e['short'])}</span>" for e in events)
    rows = []
    for player in active:
        cells = "".join(f'<i class="{"w" if won else ""}"></i>' for won in player["wins"])
        rows.append(
            f'<div class="hist-row"><b>{escape(player["name"])}</b>'
            f'<div class="cells" style="{template}">{cells}</div><em>{player["length"]}</em></div>'
        )
    body = "\n".join(rows) if rows else '<p class="rec-none">No active streaks yet.</p>'
    grid = f'<div class="hist"><div class="hist-head"><span></span><div class="cells" style="{template}">{head}</div><span></span></div>\n{body}</div>'
    return (
        '<section class="cluster-card"><div class="cluster-top-bar" style="background:var(--c-animals)"></div>'
        '<h2>Active streaks</h2><p class="card-desc">Players who won every event since their run began '
        "(2 or more). Gold squares are wins.</p>"
        f"{grid}</section>"
    )


def _record_rows(rows: list[dict]) -> str:
    """Render podium rows; `value` is builder output whose dynamic parts are pre-escaped."""
    if not rows:
        return '<p class="rec-none">No one qualifies yet.</p>'
    return "\n".join(f'<div class="rec"><b>{escape(r["name"])}</b><em>{r["value"]}</em></div>' for r in rows)


def _records_card(records: dict) -> str:
    """Records card: three badges, each with a top-3 podium (ties alphabetical)."""
    badges = [
        ("Most captains piloted", "Distinct captains across a player's wins", _record_rows(records["captains"])),
        ("Most loyal", f"Most wins on one captain (min {LOYALTY_MIN})", _record_rows(records["loyal"])),
        ("Longest comeback", "Most events missed between two wins", _record_rows(records["comeback"])),
    ]
    body = "".join(
        f'<div class="subsection-label">{label}</div><p class="card-desc" style="margin-bottom:8px">{desc}</p>{rows}'
        for label, desc, rows in badges
    )
    return (
        '<section class="cluster-card"><div class="cluster-top-bar" style="background:var(--c-pirates)"></div>'
        f'<h2>Records</h2><p class="card-desc">Small badges that give players something to chase.</p>{body}</section>'
    )


def render_page(embed: dict, base_url: str) -> str:
    """Render the static leaderboard page from the trimmed payload.

    Args:
        embed: Trimmed payload from trim_embed
        base_url: Site base URL for canonical/meta

    Returns:
        Self-contained HTML page string
    """
    stats = embed["stats"]
    total = stats["events"]
    wins = embed["most_wins"]
    streaks = embed["longest_streaks"]

    most_wins_rows = [(r["name"], r["wins"], "") for r in wins]
    streak_rows = [
        (r["name"], r["length"], f'<span class="bar-sub">{escape(_range_label(r["from"], r["to"]))}</span>')
        for r in streaks
    ]
    max_wins = max((r["wins"] for r in wins), default=1)
    max_streak = max((r["length"] for r in streaks), default=1)

    record_values = {
        "captains": [
            {"name": r["name"], "value": _plural(r["captains"], "captain")} for r in embed["records"]["captains"]
        ],
        "loyal": [
            {
                "name": r["name"],
                "value": (
                    f"{_plural(r['wins'], 'win')} with "
                    f'<a href="../captains/{escape(r["slug"].replace("_", "-"))}/">{escape(r["captain"])}</a>'
                ),
            }
            for r in embed["records"]["loyal"]
        ],
        "comeback": [
            {"name": r["name"], "value": f"back after {_plural(r['gap'], 'event')}"}
            for r in embed["records"]["comeback"]
        ],
    }

    stats_row = "".join(
        f'<div class="stat-item"><div class="stat-value">{v}</div><div class="stat-label">{label}</div></div>'
        for v, label in (
            (stats["players"], "Players tracked"),
            (total, "Events"),
            (stats["longest_streak"], "Longest streak"),
            (f"{stats['repeat_pct']}%", "Win again"),
        )
    )
    canonical = f"{base_url}/leaderboard/"
    head = _head(
        "Player Leaderboard | Once Upon a Galaxy",
        "Once Upon a Galaxy (OUAG) player leaderboard: gauntlet win totals, longest streaks, active runs and "
        "records across every monthly event.",
        canonical,
    )
    payload = serialize_payload(embed)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{head}
</head>
<body>
<header>
  <a href="../" class="event-label">Once Upon A Galaxy · Meta Analysis</a>
  <h1>Leaderboard</h1>
  <div class="subtitle">Win totals, streaks and who is hot right now.</div>
  <div class="stats-row">{stats_row}</div>
</header>
<nav>
  <a href="./" class="active">Leaderboard</a>
  <a href="../captains/">Captains</a>
  <a href="../about.html">About</a>
</nav>
<main>
  <div class="section active">
    <div class="section-title">Who keeps winning</div>
    <p class="section-desc">Players ranked by gauntlet wins across every event, plus the runs they&rsquo;re on right now.
      Every finisher won their own gauntlet, so a win means one event finished on top.</p>
    <div class="grid">
      {_bars(most_wins_rows, max_wins, f" / {total}", "var(--accent)", f"Top 10 players by total wins across all {total} events.", "Most wins")}
      {_bars(streak_rows, max_streak, "", "var(--c-candy)", "Most consecutive events won. Bar labels show when the run happened.", "Longest streaks")}
      {_active_card(embed["active_streaks"], embed["events"])}
      {_records_card(record_values)}
    </div>
    <p class="note">Names are matched case-insensitively across events and merged with the alias map in
      etl/config/aliases.json, so a rename doesn&rsquo;t split a player&rsquo;s history.</p>
  </div>
</main>
<script type="application/json" id="leaderboard-data">{payload}</script>
</body>
</html>"""


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate the cross-event player leaderboard page")
    parser.add_argument("--dist-dir", default=None, help="Path to etl/dist (default: ../dist from script location)")
    parser.add_argument(
        "--docs-dir", default=None, help="Path to docs directory (default: ../../docs from script location)"
    )
    parser.add_argument("--base-url", default=BASE_URL, help=f"Base URL for the site (default: {BASE_URL})")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    dist_dir = Path(args.dist_dir) if args.dist_dir else script_dir.parent / "dist"
    docs_dir = Path(args.docs_dir) if args.docs_dir else script_dir.parent.parent / "docs"

    aliases = load_aliases(script_dir.parent / "config" / "aliases.json")
    captains_file = dist_dir / "captains.json"
    captain_names = json.loads(captains_file.read_text(encoding="utf-8")) if captains_file.exists() else {}

    events = load_events(dist_dir / "events")
    board = compute_leaderboard(events, aliases, captain_names)

    artifact_path = dist_dir / "leaderboard.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(board, indent=2) + "\n", encoding="utf-8")

    page_path = docs_dir / "leaderboard" / "index.html"
    page_path.parent.mkdir(parents=True, exist_ok=True)
    page_path.write_text(render_page(trim_embed(board), args.base_url), encoding="utf-8")

    print(f"✓ Wrote {artifact_path}")
    print(f"✓ Wrote {page_path}")
    print(f"  {board['stats']['players']} players across {board['stats']['events']} events")
    return 0


if __name__ == "__main__":
    sys.exit(main())

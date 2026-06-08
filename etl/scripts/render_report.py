#!/usr/bin/env python3
"""Render HTML report from analysis data.

This script generates a standalone HTML report from the analysis JSON.
It embeds the analysis data into a pre-defined HTML template.

Input:
    - etl/dist/events/<event_id>-analysis.json - Analysis data from analyze_event.py

Output:
    - etl/dist/events/<event_id>-report.html - Complete standalone HTML report
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Asset version for cache busting - increment when CSS/JS changes
ASSET_VERSION = "1"


def load_analysis(event_id: str, events_dir: Path) -> dict:
    """Load analysis JSON file.

    Args:
        event_id: Event identifier (e.g., "2026-02")
        events_dir: Path to etl/dist/events directory

    Returns:
        Analysis data dictionary
    """
    analysis_path = events_dir / event_id / "analysis.json"

    if not analysis_path.exists():
        raise FileNotFoundError(f"Analysis data not found: {analysis_path}")

    with analysis_path.open(encoding="utf-8") as f:
        return json.load(f)


def format_date(date_str: str) -> str:
    """Format date string for display.

    Args:
        date_str: ISO date string (YYYY-MM-DD)

    Returns:
        Formatted date string (e.g., "February 2026")
    """
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%B %Y")
    except ValueError:
        return date_str


def get_html_template() -> str:
    """Return the HTML template for the report.

    Returns:
        HTML template string with DATA placeholder
    """
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Once Upon A Galaxy — {EVENT_NAME} Meta Analysis</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../../assets/galaxy-report.css?v={ASSET_VERSION}">
<script defer src="https://umami-taupe-gamma.vercel.app/script.js" data-website-id="a1be0c78-139e-413a-bb3c-e28b3b9dbe5c"></script>
</head>
<body>

<header>
  <a href="../../index.html" class="event-label">Once Upon A Galaxy · Meta Analysis</a>
  <h1>{MONTH_YEAR}<br>Gauntlet Report</h1>
  <div class="subtitle">{EVENT_DATE} · {TOTAL_CHAMPIONS} champions · 6-win gauntlet finishers</div>
  <div class="stats-row">
    <div class="stat-item"><div class="stat-value">{TOTAL_PLAYERS}</div><div class="stat-label">Players</div></div>
    <div class="stat-item"><div class="stat-value">{TOTAL_CAPTAINS}</div><div class="stat-label">Captains played</div></div>
    <div class="stat-item"><div class="stat-value">{TOTAL_UNIQUE_CARDS}</div><div class="stat-label">Unique cards</div></div>
    <div class="stat-item"><div class="stat-value">{MOST_PLAYED_CARD}</div><div class="stat-label">Most-played card</div></div>
  </div>
</header>

<nav>
  <button class="active" onclick="showSection('top-cards',this)">Top Cards</button>
  <button onclick="showSection('clusters',this)">Card Archetypes</button>
  <button onclick="showSection('captains',this)">Captains</button>
</nav>

<main>

  <!-- TOP CARDS -->
  <div class="section active" id="top-cards">
    <div class="section-title">Card Popularity</div>
    <div class="section-desc">How often each card appeared across all {TOTAL_PLAYERS} winning decklists. These are the cards players voluntarily added on top of the shared default set — high playrates signal genuine conviction.</div>
    <div class="bar-chart" id="bar-chart-container"></div>
    <div class="note">Top 30 cards shown by playrate.</div>

    <div class="section-title" style="margin-top:48px">Captain Popularity</div>
    <div class="section-desc">How often each captain was played across all {TOTAL_PLAYERS} winning decklists. Shows which leaders players chose to pilot through the gauntlet.</div>
    <div class="bar-chart" id="captains-chart-container"></div>
    <div class="note">All {TOTAL_CAPTAINS} captains shown by player count.</div>
  </div>

  <!-- CLUSTERS -->
  <div class="section" id="clusters">
    <div class="section-title">Card Archetypes</div>
    <div class="section-desc">Archetype popularity shows which strategic approaches players brought to the event. Card clusters below show specific cards grouped by co-occurrence frequency.</div>
    <div class="bar-chart" id="archetypes-chart-container"></div>
    <div class="note">All archetypes shown by player count.</div>

    <div class="section-title" style="margin-top:48px">Card Clusters</div>
    <div class="section-desc">Cards grouped by co-occurrence frequency using hierarchical clustering. Review and adjust cluster definitions for future events as needed.</div>
    <div class="clusters-grid" id="clusters-container"></div>
    <div class="note">Cards are grouped based on how often they appear together in winning decks. Cluster labels are derived from data.</div>
  </div>

  <!-- CAPTAINS -->
  <div class="section" id="captains">
    <div class="section-title">Captain Analysis</div>
    <div class="section-desc">Toggle between <strong>Best 12</strong> (most picked), <strong>Decklists</strong> (individual player decklists grouped by captain), or <strong>Signature Cards</strong> (lift). Cards are color-coded by archetype cluster. Captains with fewer than 5 finishers are flagged; treat their data cautiously.</div>
    <div class="legend" id="archetype-legend"></div>
    <div class="captain-filter" id="captain-filter"></div>
    <div class="captains-grid" id="captains-container"></div>
  </div>

</main>

<script src="../../assets/galaxy-report.js?v={ASSET_VERSION}"></script>
<script>
const DATA = {DATA_JSON};
const CARDS = {CARDS_JSON};

// INIT - call render functions with data
renderBars();
renderCaptainBars();
setupCaptainObserver();
renderArchetypeBars();
renderClusters();
renderCaptains();
if (DATA.cluster_map) {
  renderArchetypeLegend();
  renderCaptainFilter();
}
setTimeout(animateBars, 80);
</script>
</body>
</html>"""


def calculate_stats(analysis: dict) -> dict:
    """Calculate additional stats for the header.

    Args:
        analysis: Analysis data dictionary

    Returns:
        Dictionary with calculated stats
    """
    total_players = analysis.get("total_players", 0)
    top_cards = analysis.get("top_cards", [])
    clusters = analysis.get("clusters", [])
    captains = analysis.get("captains", [])

    # Calculate total unique cards
    unique_cards = 0
    for cluster in clusters:
        if "cards" in cluster:
            unique_cards += len(cluster["cards"])
        elif "core" in cluster and "situational" in cluster:
            unique_cards += len(cluster["core"]) + len(cluster["situational"])

    # Most-played card (name + percentage)
    most_played_card = f"{top_cards[0]['name']} ({top_cards[0]['pct']:.1f}%)" if top_cards else "N/A"

    # Get champions from event data
    event = analysis.get("event", {})
    total_champions = event.get("total_champions", total_players)

    return {
        "total_players": total_players,
        "total_captains": len(captains),
        "total_champions": total_champions,
        "unique_cards": unique_cards,
        "most_played_card": most_played_card,
    }


def load_cards(project_root: Path) -> dict:
    """Load cards JSON file.

    Args:
        project_root: Path to project root

    Returns:
        Cards data dictionary (slug -> name mapping)
    """
    cards_path = project_root / "etl" / "dist" / "cards.json"

    if not cards_path.exists():
        return {}

    with cards_path.open(encoding="utf-8") as f:
        return json.load(f)


def render_report(event_id: str, events_dir: Path) -> str:
    """Generate HTML report from analysis data.

    Args:
        event_id: Event identifier
        events_dir: Path to etl/dist/events directory

    Returns:
        Generated HTML string
    """
    # Load analysis data
    analysis = load_analysis(event_id, events_dir)

    # Load cards data for link generation
    project_root = Path(__file__).parent.parent.parent
    cards = load_cards(project_root)

    # Calculate stats
    stats = calculate_stats(analysis)

    # Get event info
    event = analysis.get("event", {})
    event_name = event.get("name", "Event")
    event_date = event.get("date", "")

    # Format data for template
    month_year = format_date(event_date)

    # Build template placeholders
    template_vars = {
        "EVENT_NAME": event_name,
        "MONTH_YEAR": month_year,
        "EVENT_DATE": event_date,
        "TOTAL_CHAMPIONS": stats["total_champions"],
        "TOTAL_PLAYERS": stats["total_players"],
        "TOTAL_CAPTAINS": stats["total_captains"],
        "TOTAL_UNIQUE_CARDS": stats["unique_cards"],
        "MOST_PLAYED_CARD": stats["most_played_card"],
        "DATA_JSON": json.dumps(analysis, separators=(",", ":")),
        "CARDS_JSON": json.dumps(cards, separators=(",", ":")),
        "ASSET_VERSION": ASSET_VERSION,
    }

    # Get template and fill placeholders
    template = get_html_template()
    for key, value in template_vars.items():
        template = template.replace(f"{{{key}}}", str(value))

    return template


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Render HTML report from analysis data")
    parser.add_argument("event_id", help="Event identifier (e.g., 2026-02)")
    args = parser.parse_args()

    try:
        # Setup paths
        project_root = Path(__file__).parent.parent.parent
        events_dir = project_root / "etl" / "dist" / "events"

        # Generate report
        print(f"Rendering report for {args.event_id}...")
        html = render_report(args.event_id, events_dir)

        # Write output to event-specific subdirectory
        output_path = events_dir / args.event_id / "report.html"
        with output_path.open("w", encoding="utf-8") as f:
            f.write(html)

        print(f"✓ Wrote {output_path}")

        # Log summary
        print("\nReport Stats:")
        print(f"  Event: {args.event_id}")
        print(f"  Output: {output_path}")
        print(f"  Size: {len(html):,} bytes")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nHint: Make sure you've run analyze_event.py first to generate the analysis JSON.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error rendering report: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

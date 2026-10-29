#!/usr/bin/env python3
"""Generate sitemap.xml for GitHub Pages.

This script walks the docs directory to generate a sitemap.xml file
for search engines. It includes the index page and all event reports.

lastmod reflects when a page's data last changed, not the build date:
reports use their event date, captain pages the latest event date the
captain appeared in, and the root/captains/leaderboard indexes the newest
event date. Pages with no event data fall back to file mtime.

Output:
    - docs/sitemap.xml - XML sitemap with lastmod dates
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path


def get_lastmod(file_path: Path) -> str:
    """Get last modification date as ISO string.

    Args:
        file_path: Path to the file

    Returns:
        ISO format date string (YYYY-MM-DD)
    """
    timestamp = file_path.stat().st_mtime
    dt = datetime.fromtimestamp(timestamp, tz=UTC)
    return dt.strftime("%Y-%m-%d")


def load_event_data(events_dir: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Read per-event and per-captain lastmod dates from analysis files.

    Args:
        events_dir: Path to etl/dist/events

    Returns:
        (event_dates, captain_dates) — event id -> event date, and
        hyphenated captain slug -> date of the latest event they appear in
    """
    event_dates: dict[str, str] = {}
    captain_dates: dict[str, str] = {}
    if not events_dir.exists():
        return event_dates, captain_dates

    for event_dir in sorted(events_dir.iterdir()):
        analysis_file = event_dir / "analysis.json"
        if not analysis_file.exists():
            continue
        with analysis_file.open(encoding="utf-8") as f:
            analysis = json.load(f)
        date = analysis.get("event", {}).get("date")
        if not date:
            continue
        event_dates[event_dir.name] = date
        for captain in analysis.get("captains", []):
            captain_dates[captain["slug"].replace("_", "-")] = date

    return event_dates, captain_dates


def find_reports(docs_dir: Path) -> list[str]:
    """Find all event reports in docs/reports.

    Args:
        docs_dir: Path to docs directory

    Returns:
        List of url paths (e.g. /reports/2026-07/)
    """
    reports_dir = docs_dir / "reports"
    if not reports_dir.exists():
        return []

    reports = []
    for event_dir in sorted(reports_dir.iterdir()):
        if event_dir.is_dir():
            index_file = event_dir / "index.html"
            if index_file.exists():
                # URL path: /reports/2026-07/
                reports.append(f"/reports/{event_dir.name}/")

    return reports


def find_captains(docs_dir: Path) -> list[str]:
    """Find the captains index and all per-captain pages in docs/captains.

    Args:
        docs_dir: Path to docs directory

    Returns:
        List of url paths (e.g. /captains/, /captains/ammit/)
    """
    captains_dir = docs_dir / "captains"
    if not captains_dir.exists():
        return []

    pages = []
    index_file = captains_dir / "index.html"
    if index_file.exists():
        pages.append("/captains/")

    for captain_dir in sorted(captains_dir.iterdir()):
        if captain_dir.is_dir():
            index_file = captain_dir / "index.html"
            if index_file.exists():
                pages.append(f"/captains/{captain_dir.name}/")

    return pages


def generate_sitemap(docs_dir: Path, base_url: str, events_dir: Path | None = None) -> str:
    """Generate sitemap XML content.

    Args:
        docs_dir: Path to docs directory
        base_url: Base URL for the site (e.g., https://example.com)
        events_dir: Path to etl/dist/events for data-driven lastmod
            (default: etl/dist/events relative to this script)

    Returns:
        Sitemap XML string
    """
    if events_dir is None:
        events_dir = Path(__file__).parent.parent / "dist" / "events"
    event_dates, captain_dates = load_event_data(events_dir)
    site_lastmod = max(event_dates.values(), default="")

    def page_lastmod(url_path: str) -> str:
        """Data-driven lastmod for a page, falling back to file mtime."""
        if url_path == "/":
            index_file, data_date = docs_dir / "index.html", site_lastmod
        elif url_path in ("/captains/", "/leaderboard/"):
            index_file, data_date = docs_dir / url_path.lstrip("/") / "index.html", site_lastmod
        elif url_path.startswith("/reports/"):
            index_file = docs_dir / url_path.lstrip("/") / "index.html"
            data_date = event_dates.get(url_path.split("/")[2])
        else:
            index_file = docs_dir / url_path.lstrip("/") / "index.html"
            data_date = captain_dates.get(url_path.rstrip("/").split("/")[-1])
        return data_date or (get_lastmod(index_file) if index_file.exists() else "")

    # Always include root index.html
    root_index = docs_dir / "index.html"
    root_lastmod = page_lastmod("/") if root_index.exists() else ""

    # Find all event reports, captain pages and the cross-event leaderboard
    reports = find_reports(docs_dir)
    captains = find_captains(docs_dir)
    if (docs_dir / "leaderboard" / "index.html").exists():
        captains.append("/leaderboard/")

    # Build XML
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    # Root index page
    lines.append("  <url>")
    lines.append(f"    <loc>{base_url}/</loc>")
    if root_lastmod:
        lines.append(f"    <lastmod>{root_lastmod}</lastmod>")
    lines.append("  </url>")

    # Event reports and captain pages
    for url_path in [*reports, *captains]:
        lines.append("  <url>")
        lines.append(f"    <loc>{base_url}{url_path}</loc>")
        lastmod = page_lastmod(url_path)
        if lastmod:
            lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append("  </url>")

    lines.append("</urlset>")

    return "\n".join(lines)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate sitemap.xml for GitHub Pages")
    parser.add_argument(
        "--base-url",
        default="https://www.galaxy-stats.com",
        help="Base URL for the site (default: https://www.galaxy-stats.com)",
    )
    parser.add_argument(
        "--docs-dir", default=None, help="Path to docs directory (default: ./../docs from script location)"
    )
    args = parser.parse_args()

    try:
        # Determine docs directory
        if args.docs_dir:
            docs_dir = Path(args.docs_dir)
        else:
            # Default: ../docs from script location (etl/scripts/)
            script_dir = Path(__file__).parent
            docs_dir = script_dir.parent.parent / "docs"

        if not docs_dir.exists():
            print(f"Error: docs directory not found: {docs_dir}", file=sys.stderr)
            return 1

        # Generate sitemap
        sitemap = generate_sitemap(docs_dir, args.base_url)

        # Write output
        output_path = docs_dir / "sitemap.xml"
        with output_path.open("w", encoding="utf-8") as f:
            f.write(sitemap)

        print(f"✓ Wrote {output_path}")

        # Log summary
        report_count = len(find_reports(docs_dir))
        captain_count = len(find_captains(docs_dir))
        print("\nSitemap Stats:")
        print(f"  Base URL: {args.base_url}")
        print(
            f"  Total URLs: {report_count + captain_count + 1} "
            f"(root + {report_count} reports + {captain_count} captains)"
        )

        return 0

    except Exception as e:
        print(f"Error generating sitemap: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Generate sitemap.xml for GitHub Pages.

This script walks the docs directory to generate a sitemap.xml file
for search engines. It includes the index page and all event reports.

Output:
    - docs/sitemap.xml - XML sitemap with lastmod dates
"""

import argparse
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


def find_reports(docs_dir: Path) -> list[tuple[str, str]]:
    """Find all event reports in docs/reports.

    Args:
        docs_dir: Path to docs directory

    Returns:
        List of (url_path, lastmod) tuples
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
                url_path = f"/reports/{event_dir.name}/"
                lastmod = get_lastmod(index_file)
                reports.append((url_path, lastmod))

    return reports


def generate_sitemap(docs_dir: Path, base_url: str) -> str:
    """Generate sitemap XML content.

    Args:
        docs_dir: Path to docs directory
        base_url: Base URL for the site (e.g., https://example.com)

    Returns:
        Sitemap XML string
    """
    # Always include root index.html
    root_index = docs_dir / "index.html"
    root_lastmod = get_lastmod(root_index) if root_index.exists() else ""

    # Find all event reports
    reports = find_reports(docs_dir)

    # Build XML
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    # Root index page
    lines.append("  <url>")
    lines.append(f"    <loc>{base_url}/</loc>")
    if root_lastmod:
        lines.append(f"    <lastmod>{root_lastmod}</lastmod>")
    lines.append("  </url>")

    # Event reports
    for url_path, lastmod in reports:
        lines.append("  <url>")
        lines.append(f"    <loc>{base_url}{url_path}</loc>")
        lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append("  </url>")

    lines.append("</urlset>")

    return "\n".join(lines)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate sitemap.xml for GitHub Pages")
    parser.add_argument(
        "--base-url",
        default="https://edmundlam.github.io/galaxy-stats",
        help="Base URL for the site (default: https://edmundlam.github.io/galaxy-stats)",
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
        print("\nSitemap Stats:")
        print(f"  Base URL: {args.base_url}")
        print(f"  Total URLs: {report_count + 1} (root + {report_count} reports)")

        return 0

    except Exception as e:
        print(f"Error generating sitemap: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

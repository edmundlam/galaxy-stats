#!/usr/bin/env python3
"""Scrape captain rules text from the Galaxy Guide cards list page.

Fetches https://guide.galaxy.fun/cards/?type=captain (server-rendered — each
<db-card> embeds data-card-key and data-card-text) and merges the rules text
into etl/dist/captain_rules.json as {snake_case_key: rules_text}. Existing
entries are never overwritten, mirroring parse_event.py's merge semantics.

Usage: uv run scripts/scrape_captain_rules.py
"""

import argparse
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

GUIDE_URL = "https://guide.galaxy.fun/cards/?type=captain"

DB_CARD_RE = re.compile(r"<db-card\s([^>]*)>", re.S)


def _attr(attrs: str, name: str) -> str | None:
    match = re.search(rf'data-{name}="(.*?)"', attrs, re.S)
    return html.unescape(match.group(1)) if match else None


def extract_rules(page_html: str) -> dict[str, str]:
    """Extract {key: rules_text} for captain cards from the list page HTML."""
    rules: dict[str, str] = {}
    for match in DB_CARD_RE.finditer(page_html):
        attrs = match.group(1)
        if _attr(attrs, "card-type") != "captain":
            continue
        key = _attr(attrs, "card-key")
        text = _attr(attrs, "card-text")
        if key and text:
            rules[key] = text.strip()
    return rules


def merge_rules(existing: dict[str, str], scraped: dict[str, str]) -> dict[str, str]:
    """Merge scraped rules into existing map, never overwriting an entry."""
    return {**scraped, **existing}


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape captain rules text into captain_rules.json")
    parser.add_argument(
        "--dist-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "dist",
        help="Path to etl/dist (default: ../dist relative to this script)",
    )
    parser.add_argument("--url", default=GUIDE_URL, help="Guide cards list URL")
    args = parser.parse_args()

    with urllib.request.urlopen(args.url) as response:
        page_html = response.read().decode("utf-8")

    scraped = extract_rules(page_html)
    if not scraped:
        print("✗ No captain rules found — page structure may have changed", file=sys.stderr)
        return 1

    rules_path = args.dist_dir / "captain_rules.json"
    existing = json.loads(rules_path.read_text(encoding="utf-8")) if rules_path.exists() else {}
    merged = merge_rules(existing, scraped)
    rules_path.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")

    added = len(merged) - len(existing)
    print(f"✓ Wrote {rules_path} ({len(scraped)} scraped, {added} new, {len(merged)} total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

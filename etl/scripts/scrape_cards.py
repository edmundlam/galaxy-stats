#!/usr/bin/env python3
"""Scrape card ids from the Galaxy Guide cards list page.

Fetches https://guide.galaxy.fun/cards/ (server-rendered — each <db-card>
embeds data-card-key, data-card-name and data-card-cid) and merges
{snake_case_key: {name, cid}} into etl/dist/cards.json. Scraped entries win —
unlike captain rules text, card names and cids come straight from the guide
with no hand edits to protect. Legacy plain-string entries ("slug": "Name")
are normalized to {"name": "Name"} so every consumer sees one shape.

Usage: uv run scripts/scrape_cards.py
"""

import argparse
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

GUIDE_URL = "https://guide.galaxy.fun/cards/"

DB_CARD_RE = re.compile(r"<db-card\s([^>]*)>", re.S)


def _attr(attrs: str, name: str) -> str | None:
    match = re.search(rf'data-{name}="(.*?)"', attrs, re.S)
    return html.unescape(match.group(1)) if match else None


def extract_cards(page_html: str) -> dict[str, dict]:
    """Extract {key: {name, cid}} for every card on the list page HTML."""
    cards: dict[str, dict] = {}
    for match in DB_CARD_RE.finditer(page_html):
        attrs = match.group(1)
        key = _attr(attrs, "card-key")
        name = _attr(attrs, "card-name")
        cid = _attr(attrs, "card-cid")
        if key and name and cid:
            cards[key] = {"name": name.strip(), "cid": int(cid)}
    return cards


def merge_cards(existing: dict, scraped: dict[str, dict]) -> dict[str, dict]:
    """Merge scraped cards into existing map; normalize legacy string entries."""
    legacy = {slug: (entry if isinstance(entry, dict) else {"name": entry}) for slug, entry in existing.items()}
    return {**legacy, **scraped}


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape card names and cids into cards.json")
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

    scraped = extract_cards(page_html)
    if not scraped:
        print("✗ No cards found — page structure may have changed", file=sys.stderr)
        return 1

    cards_path = args.dist_dir / "cards.json"
    existing = json.loads(cards_path.read_text(encoding="utf-8")) if cards_path.exists() else {}
    merged = merge_cards(existing, scraped)
    cards_path.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")

    added = len(merged) - len(existing)
    print(f"✓ Wrote {cards_path} ({len(scraped)} scraped, {added} new, {len(merged)} total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

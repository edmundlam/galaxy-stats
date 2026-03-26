#!/usr/bin/env python3
"""Parse Galaxy event HTML files to JSON format.

This script parses HTML event data from galaxy.fun and converts it to JSON format.
It creates three output files:
1. src/data/events/<event-id>.json - Event metadata and player data
2. src/data/cards.json - Deck cards only (slug -> display name)
3. src/data/captains.json - Captain cards only (slug -> display name)
"""

import argparse
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup


def extract_slug(href: str) -> str:
    """Extract card slug from href URL.

    Args:
        href: URL like "https://guide.galaxy.fun/cards/card_slug/" or "/cards/card_slug/"

    Returns:
        The card slug (e.g., "card_slug")

    Raises:
        ValueError: If slug cannot be extracted from href
    """
    match = re.search(r"/cards/([^/]+)/?", href)
    if not match:
        raise ValueError(f"Could not extract slug from href: {href}")
    return match.group(1)


def parse_event(html_file_path: str, event_id: str) -> tuple[dict, dict, dict, int, int]:
    """Parse event HTML file and extract data.

    Args:
        html_file_path: Path to the HTML file
        event_id: Event identifier (e.g., "2026-02")

    Returns:
        Tuple of (event_data, cards_data, captains_data, new_cards_count, new_captains_count)
    """
    html_path = Path(html_file_path)
    if not html_path.exists():
        raise FileNotFoundError(f"File not found: {html_file_path}")

    # Parse HTML
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "lxml")

    # Extract event metadata
    h1 = soup.find("h1")
    event_name = h1.get_text(strip=True) if h1 else ""

    time_tag = soup.find("time")
    event_date = ""
    if time_tag and time_tag.get("datetime"):
        event_date = time_tag["datetime"].split("T")[0]

    # Extract total champions from prose paragraph
    total_champions = 0
    for p in soup.find_all("p"):
        text = p.get_text()
        if "players were crowned" in text:
            match = re.search(r"(\d+)\s+players were crowned", text)
            if match:
                total_champions = int(match.group(1))
            break

    # Extract player data
    players = []
    cards_map: dict[str, str] = {}
    captains_map: dict[str, str] = {}

    for champ_info in soup.find_all("li", class_="champ-info"):
        # Extract username
        champ_name = champ_info.find("div", class_="champ-name")
        username = champ_name.get_text(strip=True) if champ_name else ""

        # Extract captain
        captain_div = champ_info.find("div", class_="champ-captain")
        captain_slug = ""
        if captain_div:
            captain_link = captain_div.find("a")
            if captain_link and captain_link.get("href"):
                captain_href = captain_link["href"]
                captain_slug = extract_slug(captain_href)
                captain_name = captain_link.get_text(strip=True)
                if captain_slug and captain_name:
                    captains_map[captain_slug] = captain_name

        # Extract deck cards
        deck_cards: list[str] = []
        cards_list = champ_info.find("ul", class_="cards-list")
        if cards_list:
            for card_link in cards_list.find_all("a"):
                href = card_link.get("href", "")
                if href:
                    card_slug = extract_slug(href)
                    card_name = card_link.get_text(strip=True)
                    if card_slug and card_name:
                        deck_cards.append(card_slug)
                        cards_map[card_slug] = card_name

        players.append(
            {
                "username": username,
                "captain": captain_slug,
                "deck": deck_cards,
            }
        )

    event_data = {
        "event": {
            "id": event_id,
            "name": event_name,
            "date": event_date,
            "total_champions": total_champions,
        },
        "players": players,
    }

    return event_data, cards_map, captains_map


def load_existing_json(path: Path) -> dict:
    """Load existing JSON file if it exists.

    Args:
        path: Path to JSON file

    Returns:
        Dict with existing data, or empty dict if file doesn't exist
    """
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def merge_cards(existing: dict, new_cards: dict) -> tuple[dict, int]:
    """Merge new cards into existing cards without overwriting.

    Args:
        existing: Existing card data
        new_cards: New card data to merge

    Returns:
        Tuple of (merged_cards, new_count)
    """
    merged = existing.copy()
    new_count = 0
    for slug, name in new_cards.items():
        if slug not in merged:
            merged[slug] = name
            new_count += 1
    return merged, new_count


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Parse Galaxy event HTML files to JSON format")
    parser.add_argument("html_file", help="Path to the HTML file")
    parser.add_argument("event_id", help="Event identifier (e.g., 2026-02)")
    args = parser.parse_args()

    try:
        # Parse event
        event_data, cards_map, captains_map = parse_event(args.html_file, args.event_id)

        # Setup paths
        project_root = Path.cwd()
        events_dir = project_root / "src" / "data" / "events"
        data_dir = project_root / "src" / "data"

        # Create directories
        events_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)

        # Load existing cards and captains
        cards_path = data_dir / "cards.json"
        captains_path = data_dir / "captains.json"

        existing_cards = load_existing_json(cards_path)
        existing_captains = load_existing_json(captains_path)

        # Merge new cards and captains (never overwrite existing entries)
        merged_cards, new_cards_count = merge_cards(existing_cards, cards_map)
        merged_captains, new_captains_count = merge_cards(existing_captains, captains_map)

        # Write event JSON
        event_json_path = events_dir / f"{args.event_id}.json"
        event_json_path.write_text(json.dumps(event_data, indent=2) + "\n", encoding="utf-8")
        print(f"✓ Wrote {event_json_path}")

        # Write cards JSON (deck cards only)
        cards_path.write_text(json.dumps(merged_cards, indent=2) + "\n", encoding="utf-8")
        print(f"✓ Wrote {cards_path}")

        # Write captains JSON (captain cards only)
        captains_path.write_text(json.dumps(merged_captains, indent=2) + "\n", encoding="utf-8")
        print(f"✓ Wrote {captains_path}")

        # Log summary
        print("\nSummary:")
        print(f"  Players parsed: {len(event_data['players'])}")
        print(f"  New deck cards added: {new_cards_count}")
        print(f"  New captain cards added: {new_captains_count}")

        return 0

    except Exception as e:
        print(f"Error parsing event: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

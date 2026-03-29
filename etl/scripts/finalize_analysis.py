#!/usr/bin/env python3
"""Finalize event analysis with optional archetype overrides.

This script converts auto-analysis.json to analysis.json, with optional manual
archetype overrides applied from a config file.

Input:
    - etl/dist/events/<event_id>-auto-analysis.json - Auto-generated analysis
    - etl/dist/cards.json - Card slug to name mappings (required)

Optional:
    - etl/config/archetypes.json - Manual archetype definitions

Output:
    - etl/dist/events/<event_id>-analysis.json - Finalized analysis for rendering
"""

import argparse
import json
import sys
from pathlib import Path


def load_cards_json(cards_path: Path) -> dict:
    """Load slug -> name mapping from cards.json.

    Args:
        cards_path: Path to cards.json file

    Returns:
        Dictionary mapping card slugs to display names

    Raises:
        FileNotFoundError: If cards.json doesn't exist
        json.JSONDecodeError: If cards.json is invalid
    """
    if not cards_path.exists():
        raise FileNotFoundError(f"Required file not found: {cards_path}")

    with cards_path.open(encoding="utf-8") as f:
        return json.load(f)


def load_archetypes_config(config_path: Path) -> dict | None:
    """Load archetype overrides config with graceful fallback.

    Args:
        config_path: Path to archetypes.json config file

    Returns:
        Config dictionary, or None if file doesn't exist

    Raises:
        FileNotFoundError: If --override-config was specified but file missing
        json.JSONDecodeError: If config is invalid JSON
    """
    if not config_path.exists():
        return None

    with config_path.open(encoding="utf-8") as f:
        return json.load(f)


def build_card_lookup(all_cards: list) -> dict:
    """Build card_slug -> card_data mapping from all clusters.

    Args:
        all_cards: List of cluster objects containing card data

    Returns:
        Dictionary mapping card slugs to card data dicts
    """
    lookup = {}
    for cluster in all_cards:
        for card in cluster.get("cards", []):
            slug = card.get("slug")
            if slug:
                lookup[slug] = card
    return lookup


def split_core_situational(cards: list, threshold: int | None) -> dict:
    """Split cards into core/situational by frequency threshold.

    Args:
        cards: List of card objects with 'freq' field
        threshold: Absolute deck count for core split (None = no split)

    Returns:
        Dict with either 'cards' key (no split) or 'core'/'situational' keys
    """
    if threshold is None:
        return {"cards": cards}

    core = [c for c in cards if c.get("freq", 0) >= threshold]
    situational = [c for c in cards if c.get("freq", 0) < threshold]

    return {"core": core, "situational": situational}


def assign_cards_to_archetypes(card_lookup: dict, archetypes_config: dict, slug_to_name: dict) -> list[dict]:
    """Assign cards to archetypes using slugs, create 'Other' cluster.
       Translates slugs to names in output.

    Args:
        card_lookup: Mapping of card slugs to card data
        archetypes_config: Config dict with archetype definitions
        slug_to_name: Mapping of slugs to display names

    Returns:
        List of cluster dicts with archetype assignments
    """
    clusters = []
    assigned_slugs = set()
    other_cards = []

    # Track duplicates across archetypes
    seen_slugs = set()

    for arch_name, arch_config in archetypes_config.get("archetypes", {}).items():
        cards = []
        core_threshold = arch_config.get("core_threshold")
        color = arch_config.get("color", "#7a7d8a")

        for slug in arch_config.get("cards", []):
            # Check for duplicates
            if slug in seen_slugs:
                raise ValueError(f"Duplicate slug '{slug}' found in archetype '{arch_name}'")

            seen_slugs.add(slug)

            # Skip if slug not in cards.json
            if slug not in slug_to_name:
                print(f"Warning: Slug '{slug}' not found in cards.json, skipping", file=sys.stderr)
                continue

            # Skip if card not in this event
            if slug not in card_lookup:
                print(f"Info: Slug '{slug}' not in event data, skipping", file=sys.stderr)
                continue

            # Get card data and translate slug to name (remove slug from final output)
            card_data = card_lookup[slug].copy()
            card_data["name"] = slug_to_name[slug]
            # Remove slug field from final output (keep only name)
            if "slug" in card_data:
                del card_data["slug"]
            cards.append(card_data)
            assigned_slugs.add(slug)

        # Split into core/situational if threshold specified
        if core_threshold is not None:
            split = split_core_situational(cards, core_threshold)
            clusters.append(
                {
                    "id": arch_name.lower().replace(" ", "_"),
                    "label": arch_name,
                    "color": color,
                    "core": split.get("core", []),
                    "situational": split.get("situational", []),
                }
            )
        else:
            clusters.append(
                {
                    "id": arch_name.lower().replace(" ", "_"),
                    "label": arch_name,
                    "color": color,
                    "cards": cards,
                }
            )

    # Create "Other" cluster for unassigned cards
    for slug, card_data in card_lookup.items():
        if slug not in assigned_slugs:
            other_card = card_data.copy()
            other_card["name"] = slug_to_name.get(slug, slug)
            # Remove slug field from final output (keep only name)
            if "slug" in other_card:
                del other_card["slug"]
            other_cards.append(other_card)

    if other_cards:
        # Sort by frequency
        other_cards.sort(key=lambda c: -c.get("freq", 0))
        clusters.append(
            {
                "id": "other",
                "label": "Other",
                "color": "#7a7d8a",
                "cards": other_cards,
            }
        )

    return clusters


def rebuild_cluster_map(clusters: list) -> dict:
    """Build cluster_map from new cluster labels.

    Args:
        clusters: List of cluster dicts

    Returns:
        Dictionary mapping cluster labels to colors
    """
    return {cluster["label"]: cluster["color"] for cluster in clusters}


def finalize_analysis(event_id: str, dist_dir: Path, override_config: Path | None = None) -> dict:
    """Main function: load auto-analysis, apply config (optional), write analysis.

    Args:
        event_id: Event identifier (e.g., "2026-02")
        dist_dir: Path to etl/dist directory
        override_config: Path to archetypes config (optional)

    Returns:
        Finalized analysis dictionary

    Raises:
        FileNotFoundError: If required files missing
        ValueError: If config validation fails
    """
    events_dir = dist_dir / "events"
    auto_analysis_path = events_dir / f"{event_id}-auto-analysis.json"
    cards_path = dist_dir / "cards.json"

    # Load auto-analysis
    if not auto_analysis_path.exists():
        raise FileNotFoundError(f"Auto-analysis not found: {auto_analysis_path}")

    with auto_analysis_path.open(encoding="utf-8") as f:
        auto_analysis = json.load(f)

    # Load cards.json (required for slug resolution)
    slug_to_name = load_cards_json(cards_path)

    if override_config:
        # Load archetype overrides
        archetypes_config = load_archetypes_config(override_config)
        if archetypes_config is None:
            raise FileNotFoundError(f"Override config not found: {override_config}")

        print(f"Applying archetype overrides from {override_config}...")

        # Build card lookup from auto-analysis
        card_lookup = build_card_lookup(auto_analysis["clusters"])

        # Apply archetype overrides
        clusters = assign_cards_to_archetypes(card_lookup, archetypes_config, slug_to_name)

        # Rebuild cluster map
        cluster_map = rebuild_cluster_map(clusters)

        # Build finalized analysis
        analysis = {
            "event": auto_analysis["event"],
            "total_players": auto_analysis["total_players"],
            "clusters": clusters,
            "captains": auto_analysis["captains"],
            "top_cards": auto_analysis["top_cards"],
            "cluster_map": cluster_map,
        }
    else:
        # No overrides: just copy auto-analysis and remove slug field
        print("No overrides specified, copying auto-analysis...")
        clusters = []

        for cluster in auto_analysis["clusters"]:
            new_cluster = cluster.copy()
            # Remove slug field from cards, keep only name
            if "cards" in new_cluster:
                new_cluster["cards"] = [{k: v for k, v in card.items() if k != "slug"} for card in new_cluster["cards"]]
            # Handle core/situational structure
            if "core" in new_cluster:
                new_cluster["core"] = [{k: v for k, v in card.items() if k != "slug"} for card in new_cluster["core"]]
                new_cluster["situational"] = [
                    {k: v for k, v in card.items() if k != "slug"} for card in new_cluster["situational"]
                ]
            clusters.append(new_cluster)

        analysis = {
            "event": auto_analysis["event"],
            "total_players": auto_analysis["total_players"],
            "clusters": clusters,
            "captains": auto_analysis["captains"],
            "top_cards": auto_analysis["top_cards"],
            "cluster_map": auto_analysis["cluster_map"],
        }

    return analysis


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Finalize event analysis with optional archetype overrides")
    parser.add_argument("event_id", help="Event identifier (e.g., 2026-02)")
    parser.add_argument("--override-config", help="Path to archetypes config file (e.g., config/archetypes.json)")

    args = parser.parse_args()

    try:
        # Setup paths
        project_root = Path(__file__).parent.parent.parent
        dist_dir = project_root / "etl" / "dist"
        events_dir = dist_dir / "events"

        # Ensure output directory exists
        events_dir.mkdir(parents=True, exist_ok=True)

        # Finalize analysis
        print(f"Finalizing analysis for {args.event_id}...")
        override_path = None
        if args.override_config:
            override_path = project_root / args.override_config

        analysis = finalize_analysis(args.event_id, dist_dir, override_path)

        # Write final analysis
        output_path = events_dir / f"{args.event_id}-analysis.json"
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2)

        print(f"✓ Wrote {output_path}")

        # Log summary
        print("\nFinalization Summary:")
        print(f"  Total players: {analysis['total_players']}")
        print(f"  Archetypes: {len(analysis['clusters'])}")
        for cluster in analysis["clusters"]:
            if "cards" in cluster:
                print(f"    - {cluster['label']}: {len(cluster['cards'])} cards")
            elif "core" in cluster:
                print(
                    f"    - {cluster['label']}: {len(cluster['core'])} core, {len(cluster['situational'])} situational"
                )

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error finalizing analysis: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

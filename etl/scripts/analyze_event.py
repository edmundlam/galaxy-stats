#!/usr/bin/env python3
"""Analyze event data and generate statistics.

This script performs statistical analysis on event data:
- Card popularity analysis
- Hierarchical clustering to identify card archetypes
- Captain lift calculations (signature cards)
- Captain best12 analysis (most commonly picked cards)

Input:
    - etl/dist/events/<event_id>.json - Event data from parse_event.py
    - etl/dist/cards.json - Card name mappings
    - etl/dist/captains.json - Captain name mappings

Output:
    - etl/dist/events/<event_id>-analysis.json - Analysis data for report generation
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform


def load_data(event_id: str, dist_dir: Path) -> tuple[dict, dict, dict]:
    """Load event, cards, and captains data.

    Args:
        event_id: Event identifier (e.g., "2026-02")
        dist_dir: Path to etl/dist directory

    Returns:
        Tuple of (event_data, cards_map, captains_map)
    """
    event_path = dist_dir / "events" / f"{event_id}.json"
    cards_path = dist_dir / "cards.json"
    captains_path = dist_dir / "captains.json"

    if not event_path.exists():
        raise FileNotFoundError(f"Event data not found: {event_path}")
    if not cards_path.exists():
        raise FileNotFoundError(f"Cards data not found: {cards_path}")
    if not captains_path.exists():
        raise FileNotFoundError(f"Captains data not found: {captains_path}")

    with open(event_path, encoding="utf-8") as f:
        event_data = json.load(f)
    with open(cards_path, encoding="utf-8") as f:
        cards_map = json.load(f)
    with open(captains_path, encoding="utf-8") as f:
        captains_map = json.load(f)

    return event_data, cards_map, captains_map


def build_cooccurrence_matrix(players: list[dict]) -> np.ndarray:
    """Build card co-occurrence matrix for clustering.

    Args:
        players: List of player records with deck data

    Returns:
        Co-occurrence distance matrix for hierarchical clustering
    """
    # Collect all unique cards
    all_cards_set = set()
    for player in players:
        all_cards_set.update(player["deck"])
    all_cards = sorted(all_cards_set)
    card_idx = {card: i for i, card in enumerate(all_cards)}
    n = len(all_cards)

    # Build player-deck matrix
    total = len(players)
    matrix = np.zeros((total, n), dtype=int)
    for pi, player in enumerate(players):
        for card in player["deck"]:
            matrix[pi, card_idx[card]] = 1

    # Build co-occurrence matrix
    cooccur = np.zeros((n, n), dtype=int)
    for deck_matrix in matrix:
        deck_indices = np.where(deck_matrix == 1)[0]
        for i in deck_indices:
            for j in deck_indices:
                if i != j:
                    cooccur[i, j] += 1

    # Convert to distance matrix (inverse of co-occurrence, normalized)
    max_val = cooccur.max()
    if max_val > 0:
        distance = max_val - cooccur
    else:
        distance = np.ones((n, n))

    # Set diagonal to 0 (cards are identical to themselves)
    np.fill_diagonal(distance, 0)

    return distance, all_cards, card_idx, matrix


def perform_hierarchical_clustering(distance_matrix: np.ndarray, n_clusters: int = 6) -> list[int]:
    """Perform hierarchical clustering on distance matrix.

    Args:
        distance_matrix: Square distance matrix
        n_clusters: Number of clusters to create

    Returns:
        List of cluster assignments (1-indexed)
    """
    # Convert to condensed distance matrix
    condensed = squareform(distance_matrix, checks=False)

    # Perform hierarchical clustering with Ward's method
    Z = linkage(condensed, method="ward")

    # Cut into clusters
    clusters = fcluster(Z, t=n_clusters, criterion="maxclust")

    return clusters


def get_cluster_label(cards_in_cluster: list[str], cards_map: dict, card_freq: dict) -> str:
    """Generate a label for a cluster based on its most frequent card.

    Args:
        cards_in_cluster: List of card slugs in the cluster
        cards_map: Mapping of card slugs to display names
        card_freq: Frequency of each card in the dataset

    Returns:
        A label for the cluster
    """
    if not cards_in_cluster:
        return "Unknown"

    # Find the most frequent card in the cluster
    most_frequent = max(cards_in_cluster, key=lambda c: card_freq.get(c, 0))
    return cards_map.get(most_frequent, most_frequent)


def assign_cluster_colors(n: int) -> list[str]:
    """Generate colors for clusters.

    Args:
        n: Number of clusters

    Returns:
        List of hex color codes
    """
    # Predefined colors for consistent styling
    base_colors = [
        "#c8a96e",  # Gold/Treasure
        "#e87d9e",  # Pink/Candy
        "#9e6ec8",  # Purple/Mage
        "#6e9ec8",  # Blue/Pirates
        "#6ec89e",  # Green/Animals
        "#7a7d8a",  # Gray/Fringe
    ]

    # If more clusters than predefined colors, generate variations
    colors = []
    for i in range(n):
        if i < len(base_colors):
            colors.append(base_colors[i])
        else:
            # Generate gray variations for extra clusters
            shade = 50 + (i * 20) % 150
            colors.append(f"#{shade:02x}{shade:02x}{shade:02x}")

    return colors


def calculate_captain_stats(
    players: list[dict], cards_map: dict, captains_map: dict, all_cards: list[str], card_idx: dict, matrix: np.ndarray
) -> list[dict]:
    """Calculate captain statistics (lift and best12).

    Args:
        players: List of player records
        cards_map: Card name mappings
        captains_map: Captain name mappings
        all_cards: List of all unique card slugs
        card_idx: Card slug to index mapping
        matrix: Player-deck matrix

    Returns:
        List of captain statistics
    """
    total = len(players)
    card_freq = matrix.sum(axis=0)
    base_rates = card_freq / total if total > 0 else np.zeros(len(all_cards))

    # Group players by captain
    cap_players = defaultdict(list)
    for pi, player in enumerate(players):
        cap_players[player["captain"]].append(pi)

    captain_data = []
    for captain_slug, player_indices in cap_players.items():
        n_players = len(player_indices)

        # Skip captains with very few players (less than 3 for meaningful stats)
        if n_players < 3:
            continue

        cap_matrix = matrix[player_indices]
        cap_freq_arr = cap_matrix.sum(axis=0)
        cap_rate = cap_freq_arr / n_players

        # Signature cards (lift)
        lifts = []
        for i, card in enumerate(all_cards):
            if base_rates[i] == 0 or cap_freq_arr[i] == 0:
                continue
            lift = cap_rate[i] / base_rates[i]
            lifts.append(
                {"card": cards_map[card], "lift": round(lift, 1), "freq": int(cap_freq_arr[i]), "n": n_players}
            )
        lifts.sort(key=lambda x: -x["lift"])

        # Best 12: most commonly picked cards for this captain
        best12 = []
        for i, card in enumerate(all_cards):
            if cap_freq_arr[i] == 0:
                continue
            best12.append(
                {
                    "card": cards_map[card],
                    "freq": int(cap_freq_arr[i]),
                    "n": n_players,
                    "pct": round(cap_freq_arr[i] / n_players * 100, 0),
                }
            )
        best12.sort(key=lambda x: -x["freq"])
        best12 = best12[:12]

        captain_data.append(
            {
                "slug": captain_slug,
                "name": captains_map.get(captain_slug, captain_slug),
                "n": n_players,
                "signature": lifts[:8],
                "best12": best12,
            }
        )

    captain_data.sort(key=lambda x: -x["n"])
    return captain_data


def analyze_event(event_id: str, dist_dir: Path, n_clusters: int = 6) -> dict:
    """Perform full event analysis.

    Args:
        event_id: Event identifier
        dist_dir: Path to etl/dist directory
        n_clusters: Number of clusters for archetype analysis

    Returns:
        Analysis data dictionary
    """
    # Load data
    event_data, cards_map, captains_map = load_data(event_id, dist_dir)
    players = event_data["players"]

    # Build co-occurrence matrix and get card data
    distance_matrix, all_cards, card_idx, matrix = build_cooccurrence_matrix(players)
    total = len(players)
    n_cards = len(all_cards)

    # Calculate card frequencies
    card_freq = matrix.sum(axis=0)

    # Perform clustering
    cluster_assignments = perform_hierarchical_clustering(distance_matrix, n_clusters)

    # Group cards by cluster
    cluster_groups = defaultdict(list)
    for card, cluster_id in zip(all_cards, cluster_assignments):
        cluster_groups[cluster_id].append(card)

    # Build cluster data with auto-generated labels
    colors = assign_cluster_colors(len(cluster_groups))
    clusters = []
    cluster_freq_map = {card: int(card_freq[card_idx[card]]) for card in all_cards}

    for cluster_id, cards_in_cluster in sorted(cluster_groups.items()):
        # Auto-generate label from most frequent card
        label = get_cluster_label(cards_in_cluster, cards_map, cluster_freq_map)

        # Get card info for this cluster
        cards_data = []
        for card in sorted(cards_in_cluster, key=lambda c: -cluster_freq_map.get(c, 0)):
            freq = cluster_freq_map[card]
            cards_data.append(
                {
                    "slug": card,
                    "name": cards_map[card],
                    "freq": freq,
                    "pct": round(freq / total * 100, 1) if total > 0 else 0,
                }
            )

        clusters.append(
            {
                "id": f"cluster_{cluster_id}",
                "label": label,
                "color": colors[cluster_id - 1] if cluster_id <= len(colors) else "#7a7d8a",
                "cards": cards_data,
            }
        )

    # Sort clusters by size (number of cards)
    clusters.sort(key=lambda c: -len(c["cards"]))

    # Calculate captain statistics
    captain_data = calculate_captain_stats(players, cards_map, captains_map, all_cards, card_idx, matrix)

    # Build top cards list
    top_cards = []
    for card in sorted(all_cards, key=lambda c: -int(card_freq[card_idx[c]])):
        freq = int(card_freq[card_idx[card]])
        if freq > 0:
            top_cards.append(
                {"name": cards_map[card], "freq": freq, "pct": round(freq / total * 100, 1) if total > 0 else 0}
            )

    # Build output
    output = {
        "event": event_data["event"],
        "total_players": total,
        "clusters": clusters,
        "captains": captain_data,
        "top_cards": top_cards[:30],  # Top 30 cards
    }

    return output


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze Galaxy event data and generate statistics")
    parser.add_argument("event_id", help="Event identifier (e.g., 2026-02)")
    parser.add_argument(
        "--clusters", type=int, default=6, help="Number of clusters for archetype analysis (default: 6)"
    )
    args = parser.parse_args()

    try:
        # Setup paths
        project_root = Path(__file__).parent.parent.parent
        dist_dir = project_root / "etl" / "dist"
        events_dir = dist_dir / "events"

        # Ensure output directory exists
        events_dir.mkdir(parents=True, exist_ok=True)

        # Perform analysis
        print(f"Analyzing event {args.event_id}...")
        analysis = analyze_event(args.event_id, dist_dir, n_clusters=args.clusters)

        # Write analysis JSON
        output_path = events_dir / f"{args.event_id}-analysis.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2)

        print(f"✓ Wrote {output_path}")

        # Log summary
        print("\nAnalysis Summary:")
        print(f"  Total players: {analysis['total_players']}")
        print(f"  Clusters found: {len(analysis['clusters'])}")
        for cluster in analysis["clusters"]:
            print(f"    - {cluster['label']}: {len(cluster['cards'])} cards")
        print(f"  Captains analyzed: {len(analysis['captains'])}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nHint: Make sure you've run parse_event.py first to generate the event JSON.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error analyzing event: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

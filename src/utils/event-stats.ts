// src/utils/event-stats.ts

/**
 * Raw event data structure (from JSON files in src/data/events/)
 */
export interface EventData {
  event: {
    id: string;
    name: string;
    date: string;
    total_champions: number;
  };
  players: Array<{
    username: string;
    captain: string;
    deck: string[];
  }>;
}

/**
 * Card lookup type: maps card slugs to display names
 */
export type CardLookup = Record<string, string>;

/**
 * Processed captain statistics with resolved display name
 */
export interface CaptainStats {
  slug: string;
  name: string;
  count: number;
  percentage: number;
}

/**
 * Processed card statistics with resolved display name
 */
export interface CardStats {
  slug: string;
  name: string;
  count: number;
  percentage: number;
}

/**
 * Generic usage stats for top-N filtering
 */
export interface UsageStats {
  count: number;
  percentage: number;
}

/**
 * Resolve card slugs to display names using the cards lookup table.
 * Falls back to the slug itself if not found in the lookup.
 */
export function resolveCardName(slug: string, cards: CardLookup): string {
  return cards[slug] || slug;
}

/**
 * Calculate captain usage frequency from event data.
 * Returns array sorted by count (descending).
 */
export function getCaptainStats(eventData: EventData, cards: CardLookup): CaptainStats[] {
  const counts = new Map<string, number>();

  // Count captain occurrences
  for (const player of eventData.players) {
    const captainSlug = player.captain;
    counts.set(captainSlug, (counts.get(captainSlug) || 0) + 1);
  }

  // Convert to stats array with percentages
  const total = eventData.players.length;
  const stats: CaptainStats[] = Array.from(counts.entries()).map(([slug, count]) => ({
    slug,
    name: resolveCardName(slug, cards),
    count,
    percentage: (count / total) * 100,
  }));

  // Sort by count descending
  return stats.sort((a, b) => b.count - a.count);
}

/**
 * Calculate card usage frequency across all decks.
 * Returns array sorted by count (descending).
 */
export function getCardStats(eventData: EventData, cards: CardLookup): CardStats[] {
  const counts = new Map<string, number>();

  // Count card occurrences across all decks
  for (const player of eventData.players) {
    for (const cardSlug of player.deck) {
      counts.set(cardSlug, (counts.get(cardSlug) || 0) + 1);
    }
  }

  // Convert to stats array with percentages
  const totalCards = eventData.players.reduce((sum, p) => sum + p.deck.length, 0);
  const stats: CardStats[] = Array.from(counts.entries()).map(([slug, count]) => ({
    slug,
    name: resolveCardName(slug, cards),
    count,
    percentage: (count / totalCards) * 100,
  }));

  // Sort by count descending
  return stats.sort((a, b) => b.count - a.count);
}

/**
 * Get top N items by usage count (generic).
 */
export function getTopN<T extends UsageStats>(stats: T[], n: number): T[] {
  return stats.slice(0, n);
}

/**
 * Calculate deck diversity metric: unique cards used / total possible cards.
 * Returns percentage (0-100).
 */
export function calculateDeckDiversity(eventData: EventData, cards: CardLookup): number {
  const uniqueCards = new Set<string>();

  for (const player of eventData.players) {
    for (const cardSlug of player.deck) {
      uniqueCards.add(cardSlug);
    }
  }

  const totalPossibleCards = Object.keys(cards).length;
  return (uniqueCards.size / totalPossibleCards) * 100;
}

/**
 * Get captain-card pairing statistics.
 * Returns map of captain slug -> map of card slug -> count.
 */
export function getCaptainCardPairings(eventData: EventData): Map<string, Map<string, number>> {
  const pairings = new Map<string, Map<string, number>>();

  for (const player of eventData.players) {
    const captainSlug = player.captain;

    if (!pairings.has(captainSlug)) {
      pairings.set(captainSlug, new Map());
    }

    const cardCounts = pairings.get(captainSlug)!;
    for (const cardSlug of player.deck) {
      cardCounts.set(cardSlug, (cardCounts.get(cardSlug) || 0) + 1);
    }
  }

  return pairings;
}

/**
 * Get top N cards paired with a specific captain.
 */
export function getTopCardsForCaptain(
  eventData: EventData,
  captainSlug: string,
  cards: CardLookup,
  n: number
): CardStats[] {
  const pairings = getCaptainCardPairings(eventData);
  const cardCounts = pairings.get(captainSlug) || new Map();

  const totalPlayersWithCaptain = eventData.players.filter(p => p.captain === captainSlug).length;

  const stats: CardStats[] = Array.from(cardCounts.entries()).map(([slug, count]) => ({
    slug,
    name: resolveCardName(slug, cards),
    count,
    percentage: (count / totalPlayersWithCaptain) * 100,
  }));

  return stats.sort((a, b) => b.count - a.count).slice(0, n);
}

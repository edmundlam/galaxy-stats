/**
 * Data loading utilities for Galaxy Stats
 *
 * This module provides typed access to the ETL output data from etl/dist/
 */

// Type definitions for the event data structure
export interface Event {
  event: EventMetadata;
  players: Player[];
}

export interface EventMetadata {
  id: string;
  name: string;
  date: string;
  total_champions: number;
}

export interface Player {
  username: string;
  captain: string;
  deck: string[];
}

export type CardSlug = string;
export type CardDisplayName = string;
export type CardsMap = Record<CardSlug, CardDisplayName>;
export type CaptainsMap = Record<CardSlug, CardDisplayName>;

// Import ETL output data
// Note: These imports will be resolved at build time by Astro

/**
 * Get card display name from slug
 * @param slug - Card slug (e.g., "legend_of_loxley")
 * @returns Card display name (e.g., "Legend of Loxley")
 */
export async function getCardName(slug: string): Promise<string | undefined> {
  const cards = await getCards();
  return cards[slug];
}

/**
 * Get captain display name from slug
 * @param slug - Captain card slug (e.g., "indiana_clones")
 * @returns Captain display name (e.g., "Indiana Clones")
 */
export async function getCaptainName(slug: string): Promise<string | undefined> {
  const captains = await getCaptains();
  return captains[slug];
}

/**
 * Get all cards map
 * @returns Map of card slugs to display names
 */
export async function getCards(): Promise<CardsMap> {
  // This will be implemented when we set up the data import
  // For now, return empty object
  return {};
}

/**
 * Get all captains map
 * @returns Map of captain card slugs to display names
 */
export async function getCaptains(): Promise<CaptainsMap> {
  // This will be implemented when we set up the data import
  // For now, return empty object
  return {};
}

/**
 * Get event data by ID
 * @param eventId - Event ID (e.g., "2026-02")
 * @returns Event data with metadata and players
 */
export async function getEvent(eventId: string): Promise<Event | undefined> {
  // This will be implemented when we set up the data import
  // For now, return undefined
  return undefined;
}

/**
 * Get all events
 * @returns Array of all event data
 */
export async function getAllEvents(): Promise<Event[]> {
  // This will be implemented when we set up the data import
  // For now, return empty array
  return [];
}

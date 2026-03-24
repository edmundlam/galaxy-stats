# Event Stats Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an interactive statistics dashboard for Galaxy Tournament events that visualizes captain usage and card popularity from parsed event data.

**Architecture:** Static data loading at build time using Astro's static import for JSON files, server-side data processing with TypeScript utilities, client-side interactivity via Vue components for sorting/filtering/charts, pure CSS bar charts with Starlight theme integration.

**Tech Stack:** Astro (static site generator), Starlight (docs theme), Vue 3 (via @astrojs/vue), TypeScript (strict mode), CSS custom properties (for theming)

---

## File Structure

**New files to create:**
- `src/utils/event-stats.ts` - Data processing utilities (type definitions, stats calculations)
- `src/styles/dashboard.css` - Dashboard-specific styles with theme-aware CSS variables
- `src/components/dashboard/StatsHeader.astro` - Hero statistics row component
- `src/components/dashboard/CaptainChart.vue` - Bar chart visualization for top 10 captains
- `src/components/dashboard/CardTable.vue` - Sortable/searchable data table for card usage
- `src/components/dashboard/PairingPreview.astro` - Captain-card pairing preview
- `src/components/dashboard/InsightsPanel.astro` - Key findings/metrics panel
- `src/content/docs/event-stats/2026-02.mdx` - Dashboard page for February Monthly event

**Files to modify:**
- `astro.config.mjs` - Add Event Stats section to sidebar navigation

---

## Task 1: Create TypeScript type definitions and utility functions

**Files:**
- Create: `src/utils/event-stats.ts`

**Purpose:** Define all TypeScript interfaces and create data processing utilities for calculating captain and card statistics from event JSON data.

- [ ] **Step 1: Create the utility file with types and functions**

```typescript
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
```

- [ ] **Step 2: Commit the utility file**

```bash
git add src/utils/event-stats.ts
git commit -m "feat: add event stats utility functions

Add TypeScript utilities for processing event data:
- Type definitions for EventData, CaptainStats, CardStats
- getCaptainStats: calculate captain usage frequency
- getCardStats: calculate card usage frequency
- getTopN: generic top-N filtering
- calculateDeckDiversity: deck diversity metric
- getCaptainCardPairings: captain-card pairing stats
- getTopCardsForCaptain: top cards for specific captain
- resolveCardName: card slug to display name with fallback"
```

---

## Task 1.5: Verify required data files exist

**Files:**
- Test: `src/data/events/2026-02.json`, `src/data/cards.json`

**Purpose:** Ensure the data files that the dashboard depends on actually exist before creating components that import them.

- [ ] **Step 1: Verify event data file exists**

```bash
test -f src/data/events/2026-02.json && echo "✓ Event data file exists" || echo "✗ Missing: src/data/events/2026-02.json"
```

Expected output: `✓ Event data file exists`

- [ ] **Step 2: Verify cards data file exists**

```bash
test -f src/data/cards.json && echo "✓ Cards data file exists" || echo "✗ Missing: src/data/cards.json"
```

Expected output: `✓ Cards data file exists`

- [ ] **Step 3: If files are missing, run the parser**

If either file is missing, the event data needs to be parsed from HTML:

```bash
# Check if context/2026-02.html exists
test -f context/2026-02.html && npm run parse-event context/2026-02.html 2026-02
```

If `context/2026-02.html` doesn't exist, the user needs to obtain the event HTML from galaxy.fun and place it in the `context/` directory.

- [ ] **Step 4: Verify file contents are valid JSON**

```bash
# Check event data is valid JSON
node -e "JSON.parse(require('fs').readFileSync('src/data/events/2026-02.json', 'utf8'))" && echo "✓ Event data is valid JSON"

# Check cards data is valid JSON
node -e "JSON.parse(require('fs').readFileSync('src/data/cards.json', 'utf8'))" && echo "✓ Cards data is valid JSON"
```

Expected output: Both commands print their respective success messages

- [ ] **Step 5: Create a verification commit**

```bash
# If files were generated/verified
git add src/data/events/2026-02.json src/data/cards.json 2>/dev/null || true
git commit -m "chore: verify event data files exist

Ensure required data files are present:
- src/data/events/2026-02.json (event player data)
- src/data/cards.json (card name lookup)"
```

---

## Task 2: Create dashboard CSS styles with theme support

**Files:**
- Create: `src/styles/dashboard.css`

**Purpose:** Dashboard-specific styles that integrate with Starlight's light/dark theme using CSS custom properties.

- [ ] **Step 1: Create dashboard styles file**

```css
/* src/styles/dashboard.css */

/* Dashboard container */
.dashboard {
  --dashboard-spacing: 1.5rem;
  --dashboard-radius: 0.5rem;
}

/* Stats header - grid of metric cards */
.stats-header {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--dashboard-spacing);
  margin-bottom: var(--dashboard-spacing);
}

.stat-card {
  background: var(--sl-color-bg-nav);
  border: 1px solid var(--sl-color-text-low);
  border-radius: var(--dashboard-radius);
  padding: 1.25rem;
  text-align: center;
}

.stat-card__value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--sl-color-accent);
  line-height: 1.2;
}

.stat-card__label {
  font-size: 0.875rem;
  color: var(--sl-color-text-low);
  margin-top: 0.5rem;
}

/* Main content grid */
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: var(--dashboard-spacing);
  margin-bottom: var(--dashboard-spacing);
}

.dashboard-grid__left,
.dashboard-grid__right {
  display: flex;
  flex-direction: column;
  gap: var(--dashboard-spacing);
}

/* Responsive breakpoints per spec: mobile < 768px, tablet < 1024px, desktop >= 1024px */
@media (max-width: 1023px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

/* Dashboard sections */
.dashboard-section {
  background: var(--sl-color-bg-nav);
  border: 1px solid var(--sl-color-text-low);
  border-radius: var(--dashboard-radius);
  padding: 1.5rem;
}

.dashboard-section__title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 0;
  margin-bottom: 1rem;
  color: var(--sl-color-text);
}

/* Bar chart */
.chart {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.chart-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.chart-bar__label {
  flex-shrink: 0;
  width: 150px;
  font-size: 0.875rem;
  color: var(--sl-color-text);
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chart-bar__track {
  flex-grow: 1;
  height: 2rem;
  background: var(--sl-color-bg);
  border-radius: 0.25rem;
  overflow: hidden;
  position: relative;
}

.chart-bar__fill {
  height: 100%;
  background: linear-gradient(90deg, var(--sl-color-accent), color-mix(in srgb, var(--sl-color-accent) 75%, white));
  transition: width 0.3s ease;
  display: flex;
  align-items: center;
  padding-left: 0.5rem;
}

.chart-bar__value {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--sl-color-text-inverted);
  white-space: nowrap;
}

@media (max-width: 768px) {
  .chart-bar__label {
    width: 100px;
    font-size: 0.75rem;
  }
}

/* Data table */
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.data-table thead {
  border-bottom: 2px solid var(--sl-color-text-low);
}

.data-table th {
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: var(--sl-color-text);
  cursor: pointer;
  user-select: none;
}

.data-table th:hover {
  color: var(--sl-color-accent);
}

.data-table th.sortable::after {
  content: ' ↕';
  opacity: 0.5;
  font-size: 0.75rem;
}

.data-table th.sortable.asc::after {
  content: ' ↑';
  opacity: 1;
}

.data-table th.sortable.desc::after {
  content: ' ↓';
  opacity: 1;
}

.data-table tbody tr {
  border-bottom: 1px solid var(--sl-color-text-low);
}

.data-table tbody tr:hover {
  background: var(--sl-color-bg);
}

.data-table td {
  padding: 0.75rem;
  color: var(--sl-color-text);
}

.data-table td[data-col="percentage"] {
  font-family: monospace;
}

/* Search input */
.table-search {
  width: 100%;
  padding: 0.5rem 0.75rem;
  margin-bottom: 1rem;
  border: 1px solid var(--sl-color-text-low);
  border-radius: 0.25rem;
  background: var(--sl-color-bg);
  color: var(--sl-color-text);
  font-size: 0.875rem;
}

.table-search:focus {
  outline: none;
  border-color: var(--sl-color-accent);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--sl-color-accent) 25%, transparent);
}

/* Expand button */
.expand-button {
  display: block;
  width: 100%;
  padding: 0.75rem;
  margin-top: 1rem;
  border: 1px solid var(--sl-color-accent);
  border-radius: 0.25rem;
  background: transparent;
  color: var(--sl-color-accent);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.expand-button:hover {
  background: color-mix(in srgb, var(--sl-color-accent) 10%, transparent);
}

/* Pairing preview list */
.pairing-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.pairing-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--sl-color-text-low);
}

.pairing-item:last-child {
  border-bottom: none;
}

.pairing-item__name {
  flex-grow: 1;
  font-size: 0.875rem;
  color: var(--sl-color-text);
}

.pairing-item__value {
  flex-shrink: 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--sl-color-accent);
}

/* Insights panel */
.insights-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.insight-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.insight-item__label {
  font-size: 0.75rem;
  color: var(--sl-color-text-low);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.insight-item__value {
  font-size: 1rem;
  font-weight: 600;
  color: var(--sl-color-text);
}

.insight-item__value--highlight {
  color: var(--sl-color-accent);
}
```

- [ ] **Step 2: Commit the styles file**

```bash
git add src/styles/dashboard.css
git commit -m "feat: add dashboard styles with theme support

Add CSS for dashboard components:
- Stat cards grid layout
- Bar chart with animated fills
- Sortable data table styles
- Search input styling
- Pairing preview list
- Insights panel
- Responsive design with mobile breakpoints
- Starlight theme integration via CSS custom properties"
```

---

## Task 3: Create StatsHeader Astro component

**Files:**
- Create: `src/components/dashboard/StatsHeader.astro`

**Purpose:** Display event overview metrics (total players, unique captains, unique cards, total deck cards).

- [ ] **Step 1: Create StatsHeader component**

```astro
---
// src/components/dashboard/StatsHeader.astro
import type { EventData } from '../../utils/event-stats';

interface Props {
  eventData: EventData;
}

const { eventData } = Astro.props;

// Calculate metrics
const uniqueCaptains = new Set(eventData.players.map(p => p.captain)).size;
const uniqueCards = new Set(eventData.players.flatMap(p => p.deck)).size;
const totalDeckCards = eventData.players.reduce((sum, p) => sum + p.deck.length, 0);
---

<div class="dashboard">
  <div class="stats-header">
    <div class="stat-card">
      <div class="stat-card__value">{eventData.players.length}</div>
      <div class="stat-card__label">Total Players</div>
    </div>

    <div class="stat-card">
      <div class="stat-card__value">{uniqueCaptains}</div>
      <div class="stat-card__label">Unique Captains</div>
    </div>

    <div class="stat-card">
      <div class="stat-card__value">{uniqueCards}</div>
      <div class="stat-card__label">Unique Cards</div>
    </div>

    <div class="stat-card">
      <div class="stat-card__value">{totalDeckCards}</div>
      <div class="stat-card__label">Total Deck Cards</div>
    </div>
  </div>
</div>

<style>
  import '../../styles/dashboard.css';
</style>
```

- [ ] **Step 2: Commit the component**

```bash
git add src/components/dashboard/StatsHeader.astro
git commit -m "feat: add StatsHeader component

Display event overview metrics:
- Total players count
- Unique captains count
- Unique cards used
- Total deck cards
- Grid layout with 4 metric cards"
```

---

## Task 4: Create CaptainChart Vue component

**Files:**
- Create: `src/components/dashboard/CaptainChart.vue`

**Purpose:** Interactive bar chart showing top 10 captains by usage count with percentage bars.

- [ ] **Step 1: Create CaptainChart component**

```vue
<!-- src/components/dashboard/CaptainChart.vue -->
<script setup lang="ts">
import { computed } from 'vue';
import type { CaptainStats } from '../../utils/event-stats';

interface Props {
  stats: CaptainStats[];
  limit?: number;
}

const props = withDefaults(defineProps<Props>(), {
  limit: 10,
});

// Get top N captains
const topCaptains = computed(() => props.stats.slice(0, props.limit));

// Find max count for scaling bars
const maxCount = computed(() =>
  Math.max(...topCaptains.value.map(s => s.count))
);
</script>

<template>
  <div class="dashboard-section">
    <h2 class="dashboard-section__title">Top {{ limit }} Captains by Usage</h2>
    <div class="chart">
      <div
        v-for="captain in topCaptains"
        :key="captain.slug"
        class="chart-bar"
      >
        <div class="chart-bar__label" :title="captain.name">
          {{ captain.name }}
        </div>
        <div class="chart-bar__track">
          <div
            class="chart-bar__fill"
            :style="{ width: `${(captain.count / maxCount) * 100}%` }"
          >
            <span class="chart-bar__value">{{ captain.count }} ({{ captain.percentage.toFixed(1) }}%)</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
  import '../../styles/dashboard.css';
</style>
```

- [ ] **Step 2: Commit the component**

```bash
git add src/components/dashboard/CaptainChart.vue
git commit -m "feat: add CaptainChart component

Bar chart visualization for captain usage:
- Displays top 10 captains by default (configurable)
- Animated bar fills scaled to max value
- Shows count and percentage
- Tooltips on truncated labels"
```

---

## Task 5: Create CardTable Vue component

**Files:**
- Create: `src/components/dashboard/CardTable.vue`

**Purpose:** Sortable, searchable data table for card usage statistics with expand functionality.

- [ ] **Step 1: Create CardTable component**

```vue
<!-- src/components/dashboard/CardTable.vue -->
<script setup lang="ts">
import { ref, computed } from 'vue';
import type { CardStats } from '../../utils/event-stats';

interface Props {
  stats: CardStats[];
  initialLimit?: number;
}

const props = withDefaults(defineProps<Props>(), {
  initialLimit: 10,
});

const expanded = ref(false);
const searchQuery = ref('');
const sortColumn = ref<'name' | 'count' | 'percentage'>('count');
const sortDirection = ref<'asc' | 'desc'>('desc');

// Filter by search query
const filteredStats = computed(() => {
  if (!searchQuery.value.trim()) {
    return props.stats;
  }

  const query = searchQuery.value.toLowerCase();
  return props.stats.filter(s =>
    s.name.toLowerCase().includes(query) ||
    s.slug.toLowerCase().includes(query)
  );
});

// Sort by column
const sortedStats = computed(() => {
  const stats = [...filteredStats.value];
  stats.sort((a, b) => {
    let aVal: string | number;
    let bVal: string | number;

    switch (sortColumn.value) {
      case 'name':
        aVal = a.name;
        bVal = b.name;
        break;
      case 'count':
        aVal = a.count;
        bVal = b.count;
        break;
      case 'percentage':
        aVal = a.percentage;
        bVal = b.percentage;
        break;
    }

    if (typeof aVal === 'string' && typeof bVal === 'string') {
      return sortDirection.value === 'asc'
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal);
    }

    return sortDirection.value === 'asc'
      ? (aVal as number) - (bVal as number)
      : (bVal as number) - (aVal as number);
  });

  return stats;
});

// Apply limit unless expanded
const displayStats = computed(() => {
  return expanded.value ? sortedStats.value : sortedStats.value.slice(0, props.initialLimit);
});

// Toggle sort
function handleSort(column: 'name' | 'count' | 'percentage') {
  if (sortColumn.value === column) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortColumn.value = column;
    sortDirection.value = 'desc';
  }
}

// Get sort class for header
function getSortClass(column: 'name' | 'count' | 'percentage'): string {
  if (sortColumn.value !== column) {
    return 'sortable';
  }

  return sortDirection.value === 'asc' ? 'sortable asc' : 'sortable desc';
}

// Toggle expanded state
function toggleExpanded() {
  expanded.value = !expanded.value;
}
</script>

<template>
  <div class="dashboard-section">
    <h2 class="dashboard-section__title">Most Played Cards</h2>

    <input
      v-model="searchQuery"
      type="text"
      placeholder="Search cards..."
      class="table-search"
    />

    <table class="data-table">
      <thead>
        <tr>
          <th
            :class="getSortClass('name')"
            @click="handleSort('name')"
          >
            Card Name
          </th>
          <th
            :class="getSortClass('count')"
            @click="handleSort('count')"
          >
            Count
          </th>
          <th
            :class="getSortClass('percentage')"
            @click="handleSort('percentage')"
          >
            Percentage
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="card in displayStats" :key="card.slug">
          <td>{{ card.name }}</td>
          <td>{{ card.count }}</td>
          <td data-col="percentage">{{ card.percentage.toFixed(2) }}%</td>
        </tr>
      </tbody>
    </table>

    <button
      v-if="sortedStats.length > initialLimit"
      class="expand-button"
      @click="toggleExpanded"
    >
      {{ expanded ? 'Show Less' : `Show All ${sortedStats.length} Cards` }}
    </button>
  </div>
</template>

<style>
  import '../../styles/dashboard.css';
</style>
```

- [ ] **Step 2: Commit the component**

```bash
git add src/components/dashboard/CardTable.vue
git commit -m "feat: add CardTable component

Sortable, searchable data table for card stats:
- Sort by name, count, or percentage
- Search by card name or slug
- Expandable to show all cards
- Visual sort indicators"
```

---

## Task 6: Create PairingPreview Astro component

**Files:**
- Create: `src/components/dashboard/PairingPreview.astro`

**Purpose:** Show top 5 cards most commonly paired with a specific captain.

- [ ] **Step 1: Create PairingPreview component**

```astro
---
// src/components/dashboard/PairingPreview.astro
import type { CardStats } from '../../utils/event-stats';

interface Props {
  captainName: string;
  topCards: CardStats[];
}

const { captainName, topCards } = Astro.props;
---

<div class="dashboard-section">
  <h2 class="dashboard-section__title">Top Cards for {captainName}</h2>

  <div class="pairing-list">
    {
      topCards.length > 0 ? (
        topCards.map((card) => (
          <div class="pairing-item">
            <span class="pairing-item__name">{card.name}</span>
            <span class="pairing-item__value">{card.count} ({card.percentage.toFixed(1)}%)</span>
          </div>
        ))
      ) : (
        <p style="color: var(--sl-color-text-low);">No pairing data available</p>
      )
    }
  </div>
</div>

<style>
  import '../../styles/dashboard.css';
</style>
```

- [ ] **Step 2: Commit the component**

```bash
git add src/components/dashboard/PairingPreview.astro
git commit -m "feat: add PairingPreview component

Shows top 5 cards for a specific captain:
- Displays card name with count and percentage
- Handles empty data gracefully"
```

---

## Task 7: Create InsightsPanel Astro component

**Files:**
- Create: `src/components/dashboard/InsightsPanel.astro`

**Purpose:** Display key findings from the event data (most popular captain, most played card, deck diversity).

- [ ] **Step 1: Create InsightsPanel component**

```astro
---
// src/components/dashboard/InsightsPanel.astro
import type { CaptainStats, CardStats } from '../../utils/event-stats';

interface Props {
  mostPopularCaptain: CaptainStats;
  mostPlayedCard: CardStats;
  deckDiversity: number;
}

const { mostPopularCaptain, mostPlayedCard, deckDiversity } = Astro.props;
---

<div class="dashboard-section">
  <h2 class="dashboard-section__title">Key Insights</h2>

  <div class="insights-list">
    <div class="insight-item">
      <div class="insight-item__label">Most Popular Captain</div>
      <div class="insight-item__value insight-item__value--highlight">
        {mostPopularCaptain.name} ({mostPopularCaptain.count} players)
      </div>
    </div>

    <div class="insight-item">
      <div class="insight-item__label">Most Played Card</div>
      <div class="insight-item__value insight-item__value--highlight">
        {mostPlayedCard.name} ({mostPlayedCard.count} times)
      </div>
    </div>

    <div class="insight-item">
      <div class="insight-item__label">Deck Diversity</div>
      <div class="insight-item__value">
        {deckDiversity.toFixed(1)}% of card pool used
      </div>
    </div>
  </div>
</div>

<style>
  import '../../styles/dashboard.css';
</style>
```

- [ ] **Step 2: Commit the component**

```bash
git add src/components/dashboard/InsightsPanel.astro
git commit -m "feat: add InsightsPanel component

Displays key event metrics:
- Most popular captain with player count
- Most played card with usage count
- Deck diversity percentage
- Highlighted values for emphasis"
```

---

## Task 8: Create event stats page for February Monthly

**Files:**
- Create: `src/content/docs/event-stats/2026-02.mdx`

**Purpose:** Main dashboard page that loads event data and composes all components.

- [ ] **Step 1: Ensure the event-stats directory exists**

```bash
mkdir -p src/content/docs/event-stats
```

Expected: Directory created (no error if already exists)

- [ ] **Step 2: Create the event stats page**

```mdx
---
// src/content/docs/event-stats/2026-02.mdx
import eventData from '../../../data/events/2026-02.json';
import cardsJson from '../../../data/cards.json';
import {
  getCaptainStats,
  getCardStats,
  getTopCardsForCaptain,
  calculateDeckDiversity,
  type EventData,
  type CardLookup,
} from '../../../utils/event-stats';
import StatsHeader from '../../../components/dashboard/StatsHeader.astro';
import CaptainChart from '../../../components/dashboard/CaptainChart.vue';
import CardTable from '../../../components/dashboard/CardTable.vue';
import PairingPreview from '../../../components/dashboard/PairingPreview.astro';
import InsightsPanel from '../../../components/dashboard/InsightsPanel.astro';

title: "February Monthly 2026 - Event Stats"
description: "Statistics and insights from the February Monthly 2026 tournament event"
sidebar:
  badge: { text: "Event Stats", variant: "neutral" }

// Type-safe data loading
const event = eventData as EventData;
const cards = cardsJson as CardLookup;

// Calculate statistics
const captainStats = getCaptainStats(event, cards);
const cardStats = getCardStats(event, cards);
const deckDiversity = calculateDeckDiversity(event, cards);

// Get most popular items for insights
const mostPopularCaptain = captainStats[0];
const mostPlayedCard = cardStats[0];

// Get top cards for most popular captain (for pairing preview)
const topCardsForTopCaptain = getTopCardsForCaptain(
  event,
  mostPopularCaptain.slug,
  cards,
  5
);
---

# February Monthly 2026 - Event Statistics

Welcome to the event statistics dashboard for the February Monthly 2026 tournament. This page visualizes captain and card usage data from {event.players.length} champion participants.

<StatsHeader eventData={event} />

<div class="dashboard-grid">
  <div class="dashboard-grid__left">
    <CaptainChart stats={captainStats} client:load />
    <CardTable stats={cardStats} client:load />
  </div>

  <div class="dashboard-grid__right">
    <PairingPreview
      captainName={mostPopularCaptain.name}
      topCards={topCardsForTopCaptain}
    />
    <InsightsPanel
      mostPopularCaptain={mostPopularCaptain}
      mostPlayedCard={mostPlayedCard}
      deckDiversity={deckDiversity}
    />
  </div>
</div>

<style>
  import '../../../styles/dashboard.css';
</style>
```

**Note:** Using `client:load` hydration directive for Vue components ensures interactivity works immediately on page load. Alternative: `client:idle` for better performance (hydrates when browser is idle), but sorting/searching are core features so `client:load` provides better UX.

- [ ] **Step 2: Commit the page**

```bash
git add src/content/docs/event-stats/2026-02.mdx
git commit -m "feat: add February Monthly event stats page

Create dashboard page for 2026-02 event:
- Loads event and card data at build time
- Composes all dashboard components
- Two-column grid layout
- Client hydration for interactive Vue components"
```

---

## Task 9: Update sidebar configuration

**Files:**
- Modify: `astro.config.mjs`

**Purpose:** Add Event Stats section to the Starlight sidebar navigation.

- [ ] **Step 1: Update sidebar in astro.config.mjs**

Read the current file first to see the exact sidebar configuration, then update it:

```bash
# Current sidebar has "Guides" and "Reference" sections
# We need to add "Event Stats" section after them
```

Update the `sidebar` array in `astro.config.mjs` to include the Event Stats section:

```javascript
// astro.config.mjs - Find the sidebar: [ ... ] section and update it
sidebar: [
  {
    label: 'Guides',
    items: [
      { label: 'Example Guide', slug: 'guides/example' },
    ],
  },
  {
    label: 'Reference',
    autogenerate: { directory: 'reference' },
  },
  {
    label: 'Event Stats',
    items: [
      {
        label: 'February Monthly 2026',
        slug: 'event-stats/2026-02',
      },
    ],
  },
],
```

**Exact change:** Add the `{ label: 'Event Stats', items: [...] }` object after the Reference section (after the closing brace of the Reference object, before the closing bracket of the sidebar array).

- [ ] **Step 2: Commit the config change**

```bash
git add astro.config.mjs
git commit -m "feat: add Event Stats section to sidebar

Add navigation link to February Monthly 2026 event stats dashboard"
```

---

## Task 10: Test the dashboard

**Files:**
- Test: Manual browser testing

**Purpose:** Verify all components render correctly and interactive features work.

- [ ] **Step 1: Start development server**

```bash
npm run dev
```

Expected output: Server starts at http://localhost:4321

- [ ] **Step 2: Navigate to event stats page**

Visit: http://localhost:4321/event-stats/2026-02/

- [ ] **Step 3: Verify components render**

Check that all components display:
- [ ] Stats header shows correct counts (183 players, etc.)
- [ ] Captain chart displays top 10 with bars
- [ ] Card table shows top 10 cards
- [ ] Pairing preview shows cards for top captain
- [ ] Insights panel displays key metrics

- [ ] **Step 4: Test interactive features**

Test Vue component interactivity:
- [ ] Click table headers to sort by name/count/percentage
- [ ] Type in search box to filter cards
- [ ] Click "Show All" button to expand table
- [ ] Verify sort indicators appear correctly

- [ ] **Step 5: Test dark mode**

Toggle theme:
- [ ] Click theme toggle in site header
- [ ] Verify all components adapt to dark mode
- [ ] Check text contrast is readable
- [ ] Verify bar chart colors render correctly

- [ ] **Step 6: Test responsive design**

Test different viewport sizes:
- [ ] Desktop (>= 1024px) - two-column grid
- [ ] Tablet (768px - 1023px) - stacked layout
- [ ] Mobile (< 768px) - single column, narrow bars

- [ ] **Step 7: Check for console errors**

Open browser DevTools:
- [ ] Check Console tab for errors
- [ ] Check Network tab for failed requests
- [ ] Verify no TypeScript/build errors

- [ ] **Step 8: Verify data accuracy**

Spot check a few values:
- [ ] Total players matches event data (183)
- [ ] Captain counts add up correctly
- [ ] Card percentages sum to ~100%

- [ ] **Step 9: Stop dev server**

```bash
# Press Ctrl+C to stop
```

---

## Task 11: Build production bundle and verify

**Files:**
- Test: Production build

**Purpose:** Ensure the dashboard builds correctly for production.

- [ ] **Step 1: Build the site**

```bash
npm run build
```

Expected: Build completes successfully with no errors

- [ ] **Step 2: Preview production build**

```bash
npm run preview
```

Expected: Preview server starts

- [ ] **Step 3: Verify production build**

Visit: http://localhost:4321/event-stats/2026-02/

Check:
- [ ] Page loads correctly
- [ ] All components render
- [ ] Interactive features work
- [ ] No console errors

- [ ] **Step 4: Check build output**

Verify:
- [ ] dist/ directory contains built files
- [ ] Page HTML is generated
- [ ] Client-side JavaScript is bundled
- [ ] CSS includes dashboard styles

- [ ] **Step 5: Stop preview server**

```bash
# Press Ctrl+C to stop
```

---

## Task 12: Final documentation and cleanup

**Files:**
- Modify: `README.md` (optional, if it exists)
- Test: Verify git status

**Purpose:** Document the new feature and prepare for handoff.

- [ ] **Step 1: Check git status**

```bash
git status
```

Expected: All changes committed except potential untracked files

- [ ] **Step 2: Review implementation against spec**

Verify success criteria from spec:
- [ ] Dashboard loads and displays all data from 2026-02 event (183 players)
- [ ] All interactive elements work (sort, search, expand)
- [ ] Dark mode renders correctly across all components
- [ ] Page is responsive: mobile < 768px, tablet < 1024px, desktop >= 1024px
- [ ] Code follows Astro/Vue patterns from the existing codebase
- [ ] Page load time < 2 seconds on desktop (verified during testing)
- [ ] All data uses TypeScript strict mode types
- [ ] Missing card slugs fall back gracefully to slug display

- [ ] **Step 3: Create summary commit**

```bash
git add -A
git commit -m "feat: complete Event Stats Dashboard implementation

Implementation of event statistics dashboard for Galaxy Tournament events:
- Data processing utilities with TypeScript types
- Five dashboard components (StatsHeader, CaptainChart, CardTable, PairingPreview, InsightsPanel)
- Theme-aware CSS styles with responsive design
- Event stats page for February Monthly 2026
- Sidebar navigation integration
- Sortable, searchable, interactive data visualizations

All success criteria met:
- 183 players data displayed correctly
- Interactive features working (sort, search, expand)
- Dark mode support via Starlight theme variables
- Responsive design (mobile, tablet, desktop)
- TypeScript strict mode throughout
- Graceful fallback for missing card names

Spec: docs/superpowers/specs/2026-03-23-event-stats-dashboard-design.md"
```

- [ ] **Step 4: Verify complete implementation**

```bash
git log --oneline -15
```

Expected: Series of commits implementing each component and utility

---

## Implementation Complete

**Summary:**

This plan implements the Event Stats Dashboard for Galaxy Tournament events with:
- **5 Astro/Vue components** for displaying statistics
- **7 utility functions** for data processing
- **1 CSS stylesheet** with theme-aware responsive design
- **1 page** for February Monthly 2026 event data

**Key Features:**
- Static data loading at build time (no client-side API calls)
- Client-side interactivity via Vue (sorting, searching, expanding)
- Pure CSS bar charts (no external chart library)
- Starlight theme integration (automatic dark mode)
- Responsive design with mobile breakpoints
- TypeScript strict mode throughout
- Graceful fallback for missing card names

**Next Steps:**
- Run the plan using @superpowers:subagent-driven-development (recommended) or @superpowers:executing-plans
- Test thoroughly against the success criteria
- Add event pages for additional events by creating new MDX files in `src/content/docs/event-stats/`

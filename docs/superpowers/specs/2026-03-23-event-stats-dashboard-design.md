# Event Stats Dashboard Design

**Date:** 2026-03-23
**Status:** Draft
**Event:** February Monthly 2026 (2026-02)

## Overview

Build an interactive statistics dashboard page for Galaxy Tournament events, visualizing captain usage and card popularity from parsed event data. The dashboard will integrate with the existing Astro Starlight documentation site and support both light and dark themes.

## Goals

- Display captain and card usage statistics from event JSON data
- Provide interactive visualizations (bar charts, pairing previews)
- Offer sortable, searchable data tables
- Support Starlight's built-in dark mode
- Create reusable components for future events

## Data Structure

**Input:** `src/data/events/<event-id>.json`
```json
{
  "event": { "id": "2026-02", "name": "February Monthly", "date": "2026-02-20", "total_champions": 183 },
  "players": [
    { "username": "...", "captain": "legend_of_loxley", "deck": ["card1", "card2", ...] }
  ]
}
```

**Reference:** `src/data/cards.json` - Maps card slugs to display names

**Missing card handling:** If a slug is not found in `cards.json`, display the slug itself as fallback.

## Type Definitions

```typescript
// Raw event data structure (from JSON)
interface EventData {
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

// Card lookup type
type CardLookup = Record<string, string>; // slug -> displayName

// Processed statistics (includes both slug and resolved name)
interface CaptainStats {
  slug: string;
  name: string;
  count: number;
  percentage: number;
}

interface CardStats {
  slug: string;
  name: string;
  count: number;
  percentage: number;
}

// For generic top-N filtering
interface UsageStats {
  count: number;
  percentage: number;
}
```

**Card Resolution Strategy:** All utility functions return objects with both `slug` and `name` fields. The `name` is resolved from `cards.json` at call time, with fallback to the slug if not found.

## Components

### 1. Event Stats Page (`src/content/docs/event-stats.mdx`)

New documentation page with embedded Vue components for the dashboard.

### 2. Vue Components

**`StatsHeader.astro`** - Hero statistics row
- Total players
- Unique captains count
- Unique cards used
- Total deck cards

**`CaptainChart.vue`** - Bar chart visualization
- Shows top 10 captains by usage
- Uses simple HTML/CSS bars (no external chart library)
- Responsive to dark/light theme

**`CardTable.vue`** - Sortable data table
- Displays card usage statistics
- Columns: Card Name, Count, Percentage
- Sortable by any column
- Searchable by card name
- Expandable to show all cards

**`PairingPreview.astro`** - Captain-card pairing preview
- Shows top 5 cards most commonly paired with selected captain
- Simple list or mini bar chart (not full network graph)
- Links to full detailed view for in-depth analysis

**`InsightsPanel.astro`** - Key findings
- Most popular captain (highest usage count)
- Most played card (appears in most decks)
- Deck diversity: `(unique cards in event) / (total unique cards in database)` percentage

### 3. Data Processing Utilities

**`src/utils/event-stats.ts`**

```typescript
// Load event data by ID (server-side only)
export async function loadEventData(eventId: string): Promise<EventData>;

// Load card lookup table
export async function loadCards(): Promise<CardLookup>;

// Resolve card slugs to display names (with fallback)
export function resolveCardNames(slugs: string[], cards: CardLookup): Map<string, string>;

// Calculate captain usage frequency
export function getCaptainStats(eventData: EventData, cards: CardLookup): CaptainStats[];

// Calculate card usage frequency (across all decks)
export function getCardStats(eventData: EventData, cards: CardLookup): CardStats[];

// Get top N items by usage (generic)
export function getTopN<T extends UsageStats>(stats: T[], n: number): T[];

// Calculate deck diversity metric (unique cards / total possible cards)
export function calculateDeckDiversity(eventData: EventData): number;
```

**Usage Pattern:**
```typescript
// In Astro component (server-side)
const eventData = await loadEventData('2026-02');
const cards = await loadCards();
const captainStats = getCaptainStats(eventData, cards);

// Pass to Vue component via props
<CaptainChart stats={captainStats} />
```

### 4. Styling

**`src/styles/dashboard.css`** - Dashboard-specific styles
- Uses CSS custom properties for theme awareness
- Inherits Starlight's light/dark mode variables
- Responsive grid layouts
- Chart bar animations

## Theme Support

All components will use Starlight's CSS custom properties for color values:
- `--sl-hue` for primary color
- `--sl-color-bg`, `--sl-color-text` for backgrounds and text
- `--sl-color-accent` for highlights

This ensures automatic dark mode compatibility without additional logic.

## Page Structure

```
Event Stats Dashboard (e.g., /event-stats/2026-02/)
├── Header Stats Row (4 metric cards)
├── Main Grid (2 columns)
│   ├── Left Column
│   │   ├── Captain Usage Bar Chart (top 10)
│   │   └── Most Played Cards Table (top 10, expandable)
│   └── Right Column
│       ├── Card Pairings Preview (top 5 cards for selected captain)
│       └── Insights Panel (key metrics)
└── Full Data Tables (expandable section, sortable/searchable)
```

## Technical Approach

1. **Data Loading**: In Astro component, use static `import` for JSON files (build-time)
2. **Card Resolution**: Utilities accept `cards` lookup parameter and resolve names server-side
3. **Client-Side Interactivity**: Vue components for sorting, filtering, and search
4. **Charts**: Pure CSS/HTML bar charts (no external dependencies)
5. **Routing**: Static page per event at `/event-stats/<event-id>/` (e.g., `/event-stats/2026-02/`)

**Example Loading Pattern:**
```astro
---
// src/content/docs/event-stats/2026-02.mdx
import eventData from '../../../data/events/2026-02.json';
import cardsJson from '../../../data/cards.json';
import { getCaptainStats, getCardStats } from '../../../utils/event-stats';

const cards = cardsJson as CardLookup;
const captainStats = getCaptainStats(eventData, cards);
const cardStats = getCardStats(eventData, cards);
---

<StatsHeader eventData={eventData} />
<CaptainChart stats={captainStats} />
<CardTable stats={cardStats} />
```

## File Structure

```
src/
├── components/
│   └── dashboard/
│       ├── StatsHeader.astro
│       ├── CaptainChart.vue
│       ├── CardTable.vue
│       ├── PairingPreview.astro
│       └── InsightsPanel.astro
├── utils/
│   └── event-stats.ts
├── styles/
│   └── dashboard.css
└── content/
    └── docs/
        └── event-stats/
            └── 2026-02.mdx
```

## Future Enhancements

- Full interactive network graph showing captain-card relationships (force-directed layout)
- Support for multiple events (event selector dropdown)
- Historical comparison between events
- Export data as CSV/JSON
- Per-player deck details view
- Archetype detection based on card clusters

## Success Criteria

- Dashboard loads and displays all data from 2026-02 event (183 players)
- All interactive elements work (sort, search, expand)
- Dark mode renders correctly across all components (auto-switches with theme toggle)
- Page is responsive: mobile < 768px, tablet < 1024px, desktop >= 1024px
- Code follows Astro/Vue patterns from the existing codebase
- Page load time < 2 seconds on desktop
- All data uses TypeScript strict mode types
- Missing card slugs fall back gracefully to slug display

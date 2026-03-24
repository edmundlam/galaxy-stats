# Event Stats Dashboard Design

**Date:** 2026-03-23
**Status:** Draft
**Event:** February Monthly 2026 (2026-02)

## Overview

Build an interactive statistics dashboard page for Galaxy Tournament events, visualizing captain usage and card popularity from parsed event data. The dashboard will integrate with the existing Astro Starlight documentation site and support both light and dark themes.

## Goals

- Display captain and card usage statistics from event JSON data
- Provide interactive visualizations (bar charts, network graphs)
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

**`NetworkGraph.vue`** - Interactive pairing visualization
- Shows captain-card relationships
- Nodes: captains (center), cards (surrounding)
- Click to expand/collapse connections
- Optional: Simplified SVG implementation

**`InsightsPanel.astro`** - Key findings
- Most popular captain
- Most played card
- Deck diversity metric

### 3. Data Processing Utilities

**`src/utils/event-stats.ts`**

```typescript
// Calculate captain usage frequency
export function getCaptainStats(eventData: EventData): CaptainStats[]

// Calculate card usage frequency
export function getCardStats(eventData: EventData): CardStats[]

// Get card pairings for a captain
export function getCaptainPairings(eventData: EventData, captain: string): CardStats[]

// Get top N items by usage
export function getTopN<T extends UsageStats>(stats: T[], n: number): T[]
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
Event Stats Dashboard
├── Header Stats Row (4 metric cards)
├── Main Grid (2 columns)
│   ├── Left Column
│   │   ├── Captain Usage Bar Chart
│   │   └── Most Played Cards Table
│   └── Right Column
│       ├── Card Pairings Network Preview
│       └── Insights Panel
└── Full Data Tables (expandable section)
```

## Technical Approach

1. **Data Loading**: Import JSON files directly in Astro component build time
2. **Client-Side Interactivity**: Vue components for sorting, filtering, and search
3. **Charts**: Pure CSS/HTML bar charts (no heavy dependencies)
4. **Network Graph**: Simplified SVG with Vue reactivity
5. **Routing**: Single page accessible at `/event-stats/` or `/event-stats/2026-02/`

## File Structure

```
src/
├── components/
│   ├── dashboard/
│   │   ├── StatsHeader.astro
│   │   ├── CaptainChart.vue
│   │   ├── CardTable.vue
│   │   ├── NetworkGraph.vue
│   │   └── InsightsPanel.astro
├── utils/
│   └── event-stats.ts
├── styles/
│   └── dashboard.css
└── content/
    └── docs/
        └── event-stats.mdx
```

## Future Enhancements

- Support for multiple events (event selector dropdown)
- Historical comparison between events
- Export data as CSV/JSON
- Per-player deck details view
- Archetype detection based on card clusters

## Success Criteria

- Dashboard loads and displays all data from 2026-02 event
- All interactive elements work (sort, search, expand)
- Dark mode renders correctly across all components
- Page is responsive on mobile and desktop
- Code follows Astro/Vue patterns from the existing codebase

# Event Stats Dashboard Design

**Date**: 2026-03-23
**Status**: Draft
**Event**: February Monthly 2026 Tournament

## Overview

Build an interactive statistics dashboard for tournament event data that visualizes captain usage, card popularity, and deck composition patterns. The dashboard will aggregate player data from parsed event JSON files and present insights through charts, tables, and interactive visualizations.

## Data Sources

- **Event Data**: `src/data/events/<event-id>.json`
  - Event metadata (id, name, date, total_champions)
  - Player records (username, captain card slug, deck card slugs)
- **Cards Lookup**: `src/data/cards.json`
  - Maps card slugs to display names (173 cards)

**Current Data**: February Monthly 2026 (183 players, 42 unique captains)

## Page Structure

### 1. Header Stats Bar
Quick overview metrics displayed prominently at the top:
- Total Players (e.g., 183)
- Unique Captains (e.g., 42)
- Cards Used (e.g., 173)
- Total Decks (e.g., 2,196 = 183 players × 12 cards)

### 2. Main Dashboard Grid
Two-column layout:

**Left Column:**
- **Captain Usage Chart**: Horizontal bar chart showing top 10 captains by player count
- **Most Played Cards Table**: Top cards with count and percentage, expandable to full list

**Right Column:**
- **Card Pairings Preview**: Teaser for interactive network graph
- **Insights Panel**: Key findings (most popular captain, must-have cards, diversity metrics)

### 3. Full Data Tables Section
Expandable/collapsible section containing:
- Sortable, filterable table of all captains with usage stats
- Sortable, filterable table of all cards with usage stats

### 4. Interactive Network Graph (Full View)
Dedicated view showing:
- Captain cards as central nodes
- Deck cards as surrounding nodes
- Edge thickness representing pairing frequency
- Click/hover for detailed stats

## Technical Implementation

### Architecture

```
src/
├── pages/
│   └── stats/
│       └── [event-id].astro      # Dynamic route for event stats
├── components/
│   ├── StatsHeader.astro         # Overview metrics
│   ├── CaptainChart.astro        # Bar chart (using Chart.js or similar)
│   ├── CardTable.astro           # Sortable table component
│   ├── InsightsPanel.astro       # Key findings
│   └── NetworkGraph.astro        # Interactive force-directed graph
└── lib/
    └── stats.ts                  # Data aggregation utilities
```

### Data Processing (`src/lib/stats.ts`)

**Functions:**
- `loadEventData(eventId: string)` - Load and parse event JSON
- `aggregateCaptainStats(eventData)` - Count captain usage, calculate percentages
- `aggregateCardStats(eventData)` - Count card appearances across all decks
- `calculatePairings(eventData)` - Build captain→card pairing matrix
- `getInsights(stats)` - Derive key findings (most popular, diversity, etc.)

**Return Types:**
```typescript
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

interface PairingData {
  captain: string;
  cards: Map<string, number>;  // card slug -> count
}

interface DashboardData {
  event: EventMetadata;
  totalPlayers: number;
  totalCaptains: number;
  totalCards: number;
  totalDecks: number;
  captains: CaptainStats[];
  cards: CardStats[];
  pairings: PairingData[];
  insights: Insights;
}
```

### Component Details

**StatsHeader.astro**
- Props: `totalPlayers`, `totalCaptains`, `totalCards`, `totalDecks`
- Renders: 4-column grid with metric labels and values
- Styling: Centered numbers, subtle backgrounds

**CaptainChart.astro**
- Props: `captains: CaptainStats[]` (top 10)
- Implementation: Chart.js horizontal bar chart
- Interactivity: Tooltip on hover showing exact count/percentage
- Responsive: Maintains aspect ratio on mobile

**CardTable.astro**
- Props: `cards: CardStats[]`, `limit?: number`
- Features:
  - Sortable by count, percentage, name
  - Search/filter input
  - Pagination for full card list
  - Expand button to show all cards

**InsightsPanel.astro**
- Props: `insights: Insights`
- Displays:
  - Most popular captain (name + count + %)
  - Most played card (name + count + %)
  - Deck diversity (unique captains / total players)

**NetworkGraph.astro**
- Props: `pairings: PairingData[]`
- Implementation: D3.js force-directed graph OR Vis.js
- Layout: Captain nodes in center, card nodes radiating outward
- Interactivity:
  - Click captain to highlight its common pairings
  - Hover node for stats tooltip
  - Zoom/pan controls
  - Legend for node types

### Visualization Libraries

**Options:**
1. **Chart.js** - Simple, lightweight, good for bar/pie charts
2. **D3.js** - Full control, complex visualizations (network graph)
3. **Vis.js** - Specialized network graphs, easier than D3 for this use case
4. **Apache ECharts** - All-in-one solution, Vue-friendly

**Recommendation**: Use **Chart.js** for bar charts + **Vis.js** for network graph
- Both are Vue-compatible
- Lightweight individually
- Good documentation
- No build complexity

### Routing

Add dynamic route: `src/pages/stats/[event-id].astro`

**URL Pattern**: `/stats/2026-02` for February Monthly

**Fallback**: If event doesn't exist, show 404 or list available events

## Visual Design

### Color Palette
- Primary blue: `#3b82f6` (Chart bars, links)
- Secondary: `#60a5fa`, `#93c5fd`, `#bfdbfe` (Gradients)
- Background: `#f8fafc` (Light gray)
- Cards: White with subtle shadow
- Text: `#1e293b` (Primary), `#64748b` (Secondary)

### Typography
- Headings: 14px, semibold, tight spacing
- Body: 11-12px for tables, readable line height
- Stats numbers: 24px, bold, prominent

### Spacing
- 16px padding for cards/sections
- 12-16px gap between grid items
- 8px margin between table rows

## Success Criteria

1. ✅ Dashboard loads and displays all 183 player records
2. ✅ Captain usage chart accurately reflects top 10 captains
3. ✅ Card table is sortable and searchable
4. ✅ Network graph renders without errors
5. ✅ Page is responsive on mobile (stacks columns)
6. ✅ Data processing handles edge cases (missing cards, empty decks)
7. ✅ Page loads in under 2 seconds

## Future Enhancements (Out of Scope)

- Compare multiple events side-by-side
- Historical trends over time
- Player-specific deck analysis
- Export data as CSV/JSON
- Dark mode toggle
- Print-friendly layout

---
name: process-month
description: Generate a tournament report and update the index.html page
---

You are processing a new tournament month for Galaxy Stats. This involves generating the report and updating the index.html page.

## Input

The user will provide:
- **EVENT_ID**: The event ID (e.g., "2026-08")
- **HTML_FILE** (optional): The source HTML file path (default: `context/2026-08.html`)

## Process

### Step 1: Generate the report

Run the full report generation pipeline from the repository root:

```bash
make report HTML_FILE=context/{EVENT_ID}.html EVENT_ID={EVENT_ID}
```

If the user doesn't provide HTML_FILE, assume `context/{EVENT_ID}.html`.

### Step 2: Extract stats for index.html

Read both the analysis.json and auto-analysis.json to extract the stats needed for the index page:

```bash
python3 << 'EOF'
import json
event_id = "{EVENT_ID}"
with open(f'etl/dist/events/{event_id}/analysis.json') as f:
    data = json.load(f)
with open(f'etl/dist/events/{event_id}/auto-analysis.json') as f:
    auto = json.load(f)

players = data['total_players']
captains = len(data['captains'])
cards = sum(len(c.get('cards', [])) for c in auto['clusters'])
top_card = data['top_cards'][0]
top_captain = data['top_captains'][0]

print(f"Players: {players}")
print(f"Captains: {captains}")
print(f"Cards: {cards}")
print(f"Top card: {top_card['name']} ({top_card['pct']:.1f}%)")
print(f"Top captain: {top_captain['name']} ({top_captain['pct']:.1f}%)")
EOF
```

Also read the previous month's data to calculate deltas. For example, if processing 2026-08, read 2026-07:

```bash
python3 << 'EOF'
import json
prev_id = "{PREVIOUS_EVENT_ID}"
with open(f'etl/dist/events/{prev_id}/analysis.json') as f:
    prev = json.load(f)
with open(f'etl/dist/events/{prev_id}/auto-analysis.json') as f:
    prev_auto = json.load(f)

prev_players = prev['total_players']
prev_captains = len(prev['captains'])
prev_cards = sum(len(c.get('cards', [])) for c in prev_auto['clusters'])
prev_top_card = prev['top_cards'][0]
prev_top_captain = prev['top_captains'][0]

# Calculate deltas for current event
# (use these values to update the index.html)
EOF
```

### Step 3: Update docs/index.html

Update `docs/index.html` to add the new event row. This involves:

1. **Insert the new row at the top** of both:
   - The desktop table (`.report-table`)
   - The mobile cards (`.report-cards`)

2. **Add the LATEST badge** to the new row

3. **Remove the LATEST badge** from the previous month's row

4. **Update deltas** for all rows that need comparison to the new previous month

The new row should follow this format (desktop):

```html
<a href="reports/{EVENT_ID}/" class="report-row latest">
  <div class="latest-badge">LATEST</div>
  <div class="row-event">
    <span class="row-title">{Month} {Year} Monthly</span>
    <span class="row-date">{EVENT_ID}</span>
  </div>
  <div>
    <div class="row-num">{PLAYERS}</div>
    <div class="row-sub">players</div>
  </div>
  <div class="row-stat">
    <span class="row-stat-num">{CAPTAINS}</span>
    <span class="delta {DIRECTION}">{ICON} {DELTA}</span>
  </div>
  <div class="row-stat">
    <span class="row-stat-num">{CARDS}</span>
    <span class="delta {DIRECTION}">{ICON} {DELTA}</span>
  </div>
  <div class="row-pick">
    <span class="row-pick-name">{TOP_CARD_NAME}</span>
    <div class="row-pick-meta">
      <span class="row-pick-pct">{TOP_CARD_PCT}%</span>
      <span class="delta {DIRECTION}">{ICON} {DELTA}</span>
    </div>
  </div>
  <div class="row-pick">
    <span class="row-pick-name">{TOP_CAPTAIN_NAME}</span>
    <div class="row-pick-meta">
      <span class="row-pick-pct">{TOP_CAPTAIN_PCT}%</span>
      <span class="delta {DIRECTION}">{ICON} {DELTA}</span>
    </div>
  </div>
  <span class="row-link">View →</span>
</a>
```

**Delta calculation rules:**
- Use `▼` for decrease, `▲` for increase
- Use `NEW` if the item wasn't in the previous month's top spot
- For percentages, show the absolute difference (e.g., `▼ 13.9`)
- For counts, show the absolute difference (e.g., `▼ 36`)
- If no previous data exists, use `&mdash;` (em dash)

**Mobile card format** (similar structure, different classes):
- Use `.report-card-m` instead of `.report-row`
- Structure: `.card-m-title`, `.card-m-date`, `.card-m-nums`, `.card-m-picks`, `.card-m-footer`

## Output

Confirm completion with:
- Report location: `docs/reports/{EVENT_ID}/index.html`
- Index.html updated with new row
- Stats summary for the new event

## Example

For event 2026-08:
- Previous month: 2026-07
- Players: 183 (▼ 36 from 219)
- Captains: 22 (▼ 6 from 28)
- Cards: 158 (▼ 1 from 159)
- Top card: Miseria (46.4%, ▼ 13.9 from 60.3%)
- Top captain: Galileo Galilei (7.7%, NEW - different from Baba Yaga)
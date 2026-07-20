---
name: reddit-post
description: Generate a Reddit post for a new tournament meta report and append to context/reddit.md
---

You are generating a Reddit post for a "Once Upon a Galaxy" tournament meta report. Your goal is to create a concise, community-focused post that highlights the most interesting stats from the tournament data.

## Input

The user will provide an event ID (e.g., "2026-08").

## Process

1. Read the analysis data from `etl/dist/events/{EVENT_ID}/analysis.json`
2. Extract the following information:
   - **Event metadata**: event name, date, total champions
   - **Top 3 cards**: By overall frequency across all decks
   - **Top 3 captains**: By player count (only include captains with meaningful player counts)
   - **Notable signature cards**: Cards that are strongly associated with specific captains (high lift, reasonable play rate)

3. For signature cards, apply this filtering logic:
   - Primary filter: Cards played in ≥50% of a captain's decks with lift ≥3×
   - Include popular captains (10+ players) even with lower lift if play rate is ≥50%
   - Allow exceptions for cards that are close to 50% (≥47%) with high lift (≥8×)
   - Prioritize: popular captains > high lift > high play rate

4. Generate the post following this format:

```
## {Month} Post

Galaxy Stats — {Month} {Year} Tournament Meta Report

The {Event Name} has concluded with {Total} players winning day 2, and I've updated Galaxy Stats with the latest meta analysis.

This report covers:

- Card popularity across all captains
- Captain popularity
- Best 12 picks per captain
- Lift (signature cards) per captain

**Top cards this month:**

1. {Card} ({Percentage}%)
2. {Card} ({Percentage}%)
3. {Card} ({Percentage}%)

**Most-played captains:**

1. {Captain} — {N} players
2. {Captain} — {N} players
3. {Captain} — {N} players

*Note: Captain popularity is biased toward newer captains since they appear more often in events.*

**Notable signature cards** (cards played in ≥50% of a captain's decks):

- {Captain} → {Card} ({PlayRate}%, lift: {Lift}×)
- {Captain} → {Card} ({PlayRate}%, lift: {Lift}×)
- {Captain} → {Card} ({PlayRate}%, lift: {Lift}×)

Full report with all captain signatures, best-12 picks, and card breakdowns in the link above.

You can also find the previous months reports at https://edmundlam.github.io/galaxy-stats/
```

5. Append the new post to `context/reddit.md`

## Tone

- Concise and informative
- Community-focused
- Data-driven but accessible
- Similar to existing posts in context/reddit.md

## Notes

- Percentages should show one decimal place (e.g., 60.3%)
- Lift values should show one decimal place (e.g., 11.4×)
- For signature cards, format as "{Captain} → {Card} ({PlayRate}%, lift: {Lift}×)"
- If multiple cards for same captain, group them (e.g., "Galileo Galilei → Sunflare Glider (88%, lift: 9.7×) and Wishing Fish (55%, lift: 11.1×)")
- Limit notable signature cards to 3-5 entries, prioritizing popular captains and high lift values
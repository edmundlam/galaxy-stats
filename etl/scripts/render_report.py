#!/usr/bin/env python3
"""Render HTML report from analysis data.

This script generates a standalone HTML report from the analysis JSON.
It embeds the analysis data into a pre-defined HTML template.

Input:
    - etl/dist/events/<event_id>-analysis.json - Analysis data from analyze_event.py

Output:
    - etl/dist/events/<event_id>-report.html - Complete standalone HTML report
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def load_analysis(event_id: str, events_dir: Path) -> dict:
    """Load analysis JSON file.

    Args:
        event_id: Event identifier (e.g., "2026-02")
        events_dir: Path to etl/dist/events directory

    Returns:
        Analysis data dictionary
    """
    analysis_path = events_dir / f"{event_id}-analysis.json"

    if not analysis_path.exists():
        raise FileNotFoundError(f"Analysis data not found: {analysis_path}")

    with analysis_path.open(encoding="utf-8") as f:
        return json.load(f)


def format_date(date_str: str) -> str:
    """Format date string for display.

    Args:
        date_str: ISO date string (YYYY-MM-DD)

    Returns:
        Formatted date string (e.g., "February 2026")
    """
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%B %Y")
    except ValueError:
        return date_str


def get_html_template() -> str:
    """Return the HTML template for the report.

    Returns:
        HTML template string with DATA placeholder
    """
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Once Upon A Galaxy — {EVENT_NAME} Meta Analysis</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0d0f14;
    --surface: #13161e;
    --surface2: #1a1e2a;
    --border: #252a38;
    --accent: #c8a96e;
    --text: #e8e4dc;
    --muted: #7a7d8a;
    --c-treasure: #c8a96e;
    --c-candy: #e87d9e;
    --c-mage: #9e6ec8;
    --c-pirates: #6e9ec8;
    --c-animals: #6ec89e;
    --c-fringe: #5a5d6a;
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:var(--bg); color:var(--text); font-family:'IBM Plex Sans',sans-serif; font-weight:300; min-height:100vh; line-height:1.6; }

  /* HEADER */
  header { padding:48px 40px 36px; border-bottom:1px solid var(--border); position:relative; overflow:hidden; }
  header::before { content:''; position:absolute; top:-60px; right:-60px; width:360px; height:360px; background:radial-gradient(circle, rgba(200,169,110,0.07) 0%, transparent 70%); pointer-events:none; }
  .event-label { font-family:'IBM Plex Mono',monospace; font-size:11px; letter-spacing:3px; text-transform:uppercase; color:var(--accent); margin-bottom:10px; text-decoration:none; display:inline-block; transition:opacity 0.2s; }
  .event-label:hover { opacity:0.75; text-decoration:underline; text-decoration-style:dotted; text-underline-offset:3px; }
  h1 { font-family:'Playfair Display',serif; font-size:clamp(28px,5vw,52px); font-weight:900; line-height:1.1; letter-spacing:-1px; }
  .subtitle { margin-top:12px; color:var(--muted); font-size:13px; font-family:'IBM Plex Mono',monospace; }
  .stats-row { display:flex; gap:32px; margin-top:28px; flex-wrap:wrap; }
  .stat-value { font-family:'Playfair Display',serif; font-size:32px; font-weight:700; color:var(--accent); line-height:1; }
  .stat-label { font-family:'IBM Plex Mono',monospace; font-size:10px; color:var(--muted); letter-spacing:2px; text-transform:uppercase; margin-top:3px; }

  /* NAV */
  nav { display:flex; border-bottom:1px solid var(--border); padding:0 40px; overflow-x:auto; scrollbar-width:none; }
  nav::-webkit-scrollbar { display:none; }
  nav button { background:none; border:none; color:var(--muted); font-family:'IBM Plex Mono',monospace; font-size:11px; letter-spacing:2px; text-transform:uppercase; padding:16px 20px; cursor:pointer; border-bottom:2px solid transparent; transition:all 0.2s; white-space:nowrap; }
  nav button:hover { color:var(--text); }
  nav button.active { color:var(--accent); border-bottom-color:var(--accent); }

  /* MAIN */
  main { padding:40px; max-width:1400px; }
  .section { display:none; }
  .section.active { display:block; animation:fadeUp 0.35s ease both; }
  @keyframes fadeUp { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
  .section-title { font-family:'Playfair Display',serif; font-size:26px; font-weight:700; margin-bottom:6px; }
  .section-desc { color:var(--muted); font-size:13px; margin-bottom:32px; max-width:680px; line-height:1.75; }
  .note { font-family:'IBM Plex Mono',monospace; font-size:11px; color:var(--muted); margin-top:24px; padding:12px 16px; border-left:2px solid var(--border); line-height:1.8; }

  /* BAR CHART */
  .bar-chart { display:flex; flex-direction:column; gap:5px; }
  .bar-row { display:grid; grid-template-columns:180px 1fr 48px; align-items:center; gap:10px; }
  .bar-name { font-family:'IBM Plex Mono',monospace; font-size:11px; color:var(--text); text-align:right; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .bar-track { background:var(--surface2); height:22px; border-radius:2px; overflow:hidden; }
  .bar-fill { height:100%; border-radius:2px; background:linear-gradient(90deg,var(--accent),rgba(200,169,110,0.55)); transition:width 0.9s cubic-bezier(0.16,1,0.3,1); position:relative; }
  .bar-fill::after { content:''; position:absolute; top:0;left:0;right:0; height:1px; background:rgba(255,255,255,0.12); }
  .bar-pct { font-family:'IBM Plex Mono',monospace; font-size:11px; color:var(--muted); }
  @media(max-width:600px){
    .bar-row{grid-template-columns:110px 1fr 40px;}
    .bar-name{font-size:10px;}
  }

  /* CLUSTERS */
  .clusters-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:18px; }
  .cluster-card { background:var(--surface); border:1px solid var(--border); border-radius:4px; padding:22px; position:relative; overflow:hidden; }
  .cluster-top-bar { position:absolute; top:0;left:0;right:0; height:3px; }
  .cluster-header { display:flex; align-items:center; gap:10px; margin-bottom:16px; }
  .cluster-label { font-family:'IBM Plex Mono',monospace; font-size:11px; letter-spacing:2px; text-transform:uppercase; font-weight:500; }
  .cluster-count { font-family:'IBM Plex Mono',monospace; font-size:10px; color:var(--muted); margin-left:auto; }

  /* sub-sections within clusters */
  .subsection-label { font-family:'IBM Plex Mono',monospace; font-size:10px; letter-spacing:1px; text-transform:uppercase; color:var(--muted); margin:14px 0 8px; padding-bottom:4px; border-bottom:1px solid var(--border); }
  .subsection-label:first-of-type { margin-top:0; }

  .pills { display:flex; flex-wrap:wrap; gap:5px; }
  .pill { font-family:'IBM Plex Mono',monospace; font-size:11px; padding:3px 9px; border-radius:2px; background:var(--surface2); border:1px solid; display:flex; align-items:center; gap:5px; }
  .pill-freq { opacity:0.45; font-size:10px; }

  /* CAPTAINS */
  .captains-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:18px; }
  .captain-card { background:var(--surface); border:1px solid var(--border); border-radius:4px; overflow:hidden; }
  .captain-header { display:flex; align-items:center; gap:8px; padding:18px 20px 14px; border-bottom:1px solid var(--border); }
  .captain-name { font-family:'Playfair Display',serif; font-size:17px; font-weight:700; flex:1; }
  .captain-n { font-family:'IBM Plex Mono',monospace; font-size:10px; color:var(--muted); background:var(--surface2); padding:3px 7px; border-radius:2px; }
  .captain-n.warn { color:#c87a6e; background:rgba(200,122,110,0.1); }

  /* Toggle */
  .toggle-bar { display:flex; border-bottom:1px solid var(--border); }
  .toggle-btn { flex:1; background:none; border:none; font-family:'IBM Plex Mono',monospace; font-size:10px; letter-spacing:1.5px; text-transform:uppercase; color:var(--muted); padding:10px 8px; cursor:pointer; border-bottom:2px solid transparent; transition:all 0.15s; }
  .toggle-btn.active { color:var(--accent); border-bottom-color:var(--accent); }
  .toggle-btn:hover:not(.active) { color:var(--text); }

  .view { display:none; padding:16px 20px; max-height:310px; overflow-y:auto; scrollbar-width:thin; scrollbar-color:var(--border) var(--surface); }
  .view.active { display:block; }
  .view::-webkit-scrollbar { width:6px; }
  .view::-webkit-scrollbar-track { background:var(--surface); }
  .view::-webkit-scrollbar-thumb { background:var(--border); border-radius:3px; }
  .view::-webkit-scrollbar-thumb:hover { background:var(--muted); }

  /* Signature (lift) rows */
  .lift-rows { display:flex; flex-direction:column; gap:7px; }
  .lift-row { display:grid; grid-template-columns:1fr auto auto; align-items:center; gap:8px; }
  .lift-name { font-family:'IBM Plex Mono',monospace; font-size:11px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .lift-freq { font-family:'IBM Plex Mono',monospace; font-size:10px; color:var(--muted); flex-shrink:0; }
  .lift-badge { font-family:'IBM Plex Mono',monospace; font-size:10px; padding:2px 6px; border-radius:2px; min-width:48px; text-align:center; flex-shrink:0; }
  .lift-hi { background:rgba(200,169,110,0.15); color:var(--c-treasure); }
  .lift-mid { background:rgba(110,158,200,0.12); color:var(--c-pirates); }
  .lift-lo { background:rgba(122,125,138,0.08); color:var(--muted); }

  /* Best 12 rows */
  .best-rows { display:flex; flex-direction:column; gap:6px; }
  .best-row { display:grid; grid-template-columns:1fr auto; align-items:center; gap:8px; }
  .best-name { font-family:'IBM Plex Mono',monospace; font-size:11px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .best-track { display:flex; align-items:center; gap:6px; }
  .best-bar-wrap { width:60px; height:6px; background:var(--surface2); border-radius:3px; overflow:hidden; flex-shrink:0; }
  .best-bar-fill { height:100%; border-radius:3px; background:var(--accent); opacity:0.7; }
  .best-pct { font-family:'IBM Plex Mono',monospace; font-size:10px; color:var(--muted); width:34px; text-align:right; flex-shrink:0; }

  /* Archetype badge styles */
  .tag { display:inline-flex; align-items:center; font-family:'IBM Plex Mono',monospace;
          font-size:9px; letter-spacing:1px; text-transform:uppercase;
          padding:2px 7px; border-radius:2px; font-weight:500; }
  .tag-treasure { background:rgba(200,169,110,0.12); color:var(--c-treasure); border:1px solid rgba(200,169,110,0.25); }
  .tag-candy { background:rgba(232,125,158,0.12); color:var(--c-candy); border:1px solid rgba(232,125,158,0.25); }
  .tag-mage { background:rgba(158,110,200,0.12); color:var(--c-mage); border:1px solid rgba(158,110,200,0.25); }
  .tag-pirates { background:rgba(110,158,200,0.12); color:var(--c-pirates); border:1px solid rgba(110,158,200,0.25); }
  .tag-animals { background:rgba(110,200,158,0.12); color:var(--c-animals); border:1px solid rgba(110,200,158,0.25); }
  .tag-fringe { background:rgba(122,125,138,0.12); color:var(--c-fringe); border:1px solid rgba(122,125,138,0.25); }

  /* Decklists view */
  .decklist-option-a { display:flex; flex-direction:column; gap:4px; }
  .player-row { border:1px solid var(--border); border-radius:3px; overflow:hidden; }
  .player-row-header { display:flex; align-items:center; gap:8px; padding:7px 10px;
                      cursor:pointer; background:var(--surface2); transition:background 0.15s; user-select:none; }
  .player-row-header:hover { background:#1e2230; }
  .player-username { font-family:'IBM Plex Mono',monospace; font-size:11px; flex:1; }
  .expand-icon { font-family:'IBM Plex Mono',monospace; font-size:10px; color:var(--muted);
                transition:transform 0.2s; flex-shrink:0; }
  .player-row.open .expand-icon { transform:rotate(90deg); }
  .player-deck { display:none; padding:8px 10px; border-top:1px solid var(--border); background:var(--bg); }
  .player-row.open .player-deck { display:block; }
  .deck-pills { display:flex; flex-wrap:wrap; gap:4px; }
  .deck-pill { font-family:'IBM Plex Mono',monospace; font-size:10px; padding:2px 8px;
               border-radius:2px; background:var(--surface2); border:1px solid var(--border); color:var(--text); }

  /* Legend and filter */
  .legend { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:24px; padding:12px 14px;
           background:var(--surface); border:1px solid var(--border); border-radius:4px; align-items:center; }
  .legend-label { font-family:'IBM Plex Mono',monospace; font-size:10px; letter-spacing:2px;
                 text-transform:uppercase; color:var(--muted); margin-right:4px; flex-shrink:0; }
  .legend-item { display:flex; align-items:center; gap:5px; font-family:'IBM Plex Mono',monospace; font-size:10px; }
  .legend-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }

  .captain-filter { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:20px; align-items:center; }
  .filter-label { font-family:'IBM Plex Mono',monospace; font-size:10px; letter-spacing:2px;
                 text-transform:uppercase; color:var(--muted); margin-right:2px; }
  .filter-btn { background:var(--surface2); border:1px solid var(--border); border-radius:2px;
                font-family:'IBM Plex Mono',monospace; font-size:10px; letter-spacing:1px;
                text-transform:uppercase; color:var(--muted); padding:5px 10px; cursor:pointer;
                transition:all 0.15s; }
  .filter-btn:hover { color:var(--text); }
  .filter-btn.active { color:var(--accent); border-color:rgba(200,169,110,0.4);
                      background:rgba(200,169,110,0.08); }
  .captain-card.hidden { display:none; }

  @media(max-width:700px){
    header,nav,main{padding-left:16px;padding-right:16px;}
    header{padding-top:32px;}
    .captains-grid{grid-template-columns:1fr;}
    .clusters-grid{grid-template-columns:1fr;}
  }
</style>
</head>
<body>

<header>
  <a href="../../index.html" class="event-label">Once Upon A Galaxy · Meta Analysis</a>
  <h1>{MONTH_YEAR}<br>Gauntlet Report</h1>
  <div class="subtitle">{EVENT_DATE} · {TOTAL_CHAMPIONS} champions · 6-win gauntlet finishers</div>
  <div class="stats-row">
    <div class="stat-item"><div class="stat-value">{TOTAL_PLAYERS}</div><div class="stat-label">Players</div></div>
    <div class="stat-item"><div class="stat-value">{TOTAL_CAPTAINS}</div><div class="stat-label">Captains played</div></div>
    <div class="stat-item"><div class="stat-value">{TOTAL_UNIQUE_CARDS}</div><div class="stat-label">Unique cards</div></div>
    <div class="stat-item"><div class="stat-value">{TOP_CARD_RATE}</div><div class="stat-label">Top card rate</div></div>
  </div>
</header>

<nav>
  <button class="active" onclick="showSection('top-cards',this)">Top Cards</button>
  <button onclick="showSection('clusters',this)">Card Archetypes</button>
  <button onclick="showSection('captains',this)">Captains</button>
</nav>

<main>

  <!-- TOP CARDS -->
  <div class="section active" id="top-cards">
    <div class="section-title">Card Popularity</div>
    <div class="section-desc">How often each card appeared across all {TOTAL_PLAYERS} winning decklists. These are the cards players voluntarily added on top of the shared default set — high playrates signal genuine conviction.</div>
    <div class="bar-chart" id="bar-chart-container"></div>
    <div class="note">Top 30 cards shown by playrate.</div>
  </div>

  <!-- CLUSTERS -->
  <div class="section" id="clusters">
    <div class="section-title">Card Archetypes</div>
    <div class="section-desc">Cards grouped by co-occurrence frequency using hierarchical clustering. Cluster labels are auto-generated from the most frequent card in each group. Review and adjust cluster definitions for future events as needed.</div>
    <div class="clusters-grid" id="clusters-container"></div>
    <div class="note">Cards are grouped based on how often they appear together in winning decks. Cluster labels are derived from data — you can adjust them by editing the analysis JSON or archetypes config.</div>
  </div>

  <!-- CAPTAINS -->
  <div class="section" id="captains">
    <div class="section-title">Captain Analysis</div>
    <div class="section-desc">Toggle between <strong>Best 12</strong> (most picked), <strong>Decklists</strong> (individual player decklists grouped by captain), or <strong>Signature Cards</strong> (lift). Cards are color-coded by archetype cluster. Captains with fewer than 5 finishers are flagged; treat their data cautiously.</div>
    <div class="legend" id="archetype-legend"></div>
    <div class="captain-filter" id="captain-filter"></div>
    <div class="captains-grid" id="captains-container"></div>
  </div>

</main>

<script>
const DATA = {DATA_JSON};

function showSection(id, btn) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  btn.classList.add('active');
  if (id === 'top-cards') animateBars();
}

// BAR CHART
function renderBars() {
  const c = document.getElementById('bar-chart-container');
  const max = DATA.top_cards[0].pct;
  c.innerHTML = DATA.top_cards.map(card => `
    <div class="bar-row">
      <div class="bar-name">${card.name}</div>
      <div class="bar-track"><div class="bar-fill" style="width:0%" data-w="${card.pct/max*100}"></div></div>
      <div class="bar-pct">${card.pct}%</div>
    </div>`).join('');
}
function animateBars() {
  requestAnimationFrame(() => {
    document.querySelectorAll('.bar-fill').forEach(el => { el.style.width = el.dataset.w + '%'; });
  });
}

// CLUSTERS
function renderClusters() {
  const c = document.getElementById('clusters-container');
  c.innerHTML = DATA.clusters.map(cl => {
    const color = cl.color;
    let inner = '';
    if (cl.core) {
      inner = `
        <div class="subsection-label" style="color:${color}99">Core — high frequency</div>
        <div class="pills">${cl.core.map(card => pill(card, color, 0.8)).join('')}</div>
        <div class="subsection-label" style="color:${color}60;margin-top:14px">Situational — lower frequency</div>
        <div class="pills">${cl.situational.map(card => pill(card, color, 0.35)).join('')}</div>`;
    } else {
      inner = `<div class="pills">${cl.cards.map(card => pill(card, color, 0.7)).join('')}</div>`;
    }
    return `
      <div class="cluster-card">
        <div class="cluster-top-bar" style="background:${color};opacity:0.75"></div>
        <div class="cluster-header">
          <span class="cluster-label" style="color:${color}">${cl.label}</span>
          <span class="cluster-count">${(cl.core ? cl.core.length + cl.situational.length : cl.cards.length)} cards</span>
        </div>
        ${inner}
      </div>`;
  }).join('');
}
function pill(card, color, opacity) {
  return `<div class="pill" style="border-color:${color}${Math.round(opacity*99).toString(16).padStart(2,'0')}">
    <span>${card.name}</span><span class="pill-freq">${card.freq}</span>
  </div>`;
}

// CAPTAINS
function renderCaptains() {
  const c = document.getElementById('captains-container');

  // Build card name lookup and color mapping
  const cardInfo = {};
  const archColors = {};
  DATA.clusters.forEach(cl => {
    archColors[cl.label] = cl.color;
    // Handle both flat structure (cl.cards) and split structure (cl.core/cl.situational)
    if (cl.core) {
      // Split structure: core and situational arrays
      cl.core.forEach(card => {
        const key = card.slug || card.name;
        cardInfo[key] = { name: card.name, color: cl.color };
      });
      cl.situational.forEach(card => {
        const key = card.slug || card.name;
        cardInfo[key] = { name: card.name, color: cl.color };
      });
    } else if (cl.cards) {
      // Flat structure: single cards array
      cl.cards.forEach(card => {
        const key = card.slug || card.name;
        cardInfo[key] = { name: card.name, color: cl.color };
      });
    }
  });

  c.innerHTML = DATA.captains.map((cap, i) => {
    const uid = `cap-${i}`;
    const warn = cap.n < 5;

    // Track archetypes for filtering
    const archetypesPresent = cap.players ?
      [...new Set(cap.players.map(p => p.archetype))].join(' ') : '';

    // Signature rows (existing)
    const sigRows = cap.signature.map(tc => {
      const cls = tc.lift >= 10 ? 'lift-hi' : tc.lift >= 5 ? 'lift-mid' : 'lift-lo';
      const color = cardInfo[tc.card.replace(/\\s+/g, '_').toLowerCase()]?.color;
      return `<div class="lift-row">
        <div class="lift-name" style="color:${color || ''}">${tc.card}</div>
        <div class="lift-freq">${tc.freq}/${cap.n}</div>
        <div class="lift-badge ${cls}">${tc.lift}×</div>
      </div>`;
    }).join('');

    // Best 12 rows (existing)
    const bestRows = cap.best12.map(tc => {
      const color = cardInfo[tc.card.replace(/\\s+/g, '_').toLowerCase()]?.color;
      return `<div class="best-row">
        <div class="best-name" style="color:${color || ''}">${tc.card}</div>
        <div class="best-track">
          <div class="best-bar-wrap"><div class="best-bar-fill" style="width:${tc.pct}%"></div></div>
          <div class="best-pct">${tc.pct}%</div>
        </div>
      </div>`;
    }).join('');

    // Decklists view (new)
    const deckView = cap.players && cap.players.length > 0 ?
      `<div class="decklist-option-a">
        ${cap.players.map((p, pi) => `
          <div class="player-row" id="${uid}p${pi}" data-archetypes="${p.archetype}">
            <div class="player-row-header" onclick="togglePlayer('${uid}p${pi}')">
              <span class="player-username">${p.username}</span>
              <span class="tag" style="background:${archColors[p.archetype]}20; color:${archColors[p.archetype]}; border-color:${archColors[p.archetype]}40">
                ${p.archetype}
              </span>
              <span class="expand-icon">▶</span>
            </div>
            <div class="player-deck">
              <div class="deck-pills">
                ${p.deck.map(cardSlug => {
                  const info = cardInfo[cardSlug] || { name: cardSlug, color: '' };
                  return `<span class="deck-pill" style="${info.color ? 'color:' + info.color + 'cc;border-color:' + info.color + '30' : ''}">${info.name}</span>`;
                }).join('')}
              </div>
            </div>
          </div>
        `).join('')}
      </div>` :
      '<div style="padding:16px; color:var(--muted); font-size:11px;">No decklist data available</div>';

    return `
      <div class="captain-card" data-archetypes="${archetypesPresent}">
        <div class="captain-header">
          <div class="captain-name">${cap.name}</div>
          <div class="captain-n ${warn ? 'warn' : ''}">n=${cap.n}${warn ? ' ⚠' : ''}</div>
        </div>
        <div class="toggle-bar">
          <button class="toggle-btn active" onclick="switchView('${uid}','best',this)">Best 12</button>
          <button class="toggle-btn" onclick="switchView('${uid}','deck',this)">Decklists</button>
          <button class="toggle-btn" onclick="switchView('${uid}','sig',this)">Signature</button>
        </div>
        <div class="view active" id="${uid}-best"><div class="best-rows">${bestRows}</div></div>
        <div class="view" id="${uid}-deck">${deckView}</div>
        <div class="view" id="${uid}-sig"><div class="lift-rows">${sigRows}</div></div>
      </div>`;
  }).join('');
}

function switchView(uid, view, btn) {
  const card = btn.closest('.captain-card');
  card.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
  card.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById(`${uid}-${view}`).classList.add('active');
}

// Render archetype legend
function renderArchetypeLegend() {
  const c = document.getElementById('archetype-legend');
  const archetypes = Object.entries(DATA.cluster_map || {});
  c.innerHTML = `<span class="legend-label">Archetypes</span>` +
    archetypes.map(([label, color]) => `
      <div class="legend-item">
        <div class="legend-dot" style="background:${color}"></div>
        ${label}
      </div>`).join('');
}

// Render captain filter
function renderCaptainFilter() {
  const c = document.getElementById('captain-filter');
  const archetypes = ['all', ...Object.keys(DATA.cluster_map || {})];
  c.innerHTML = `<span class="filter-label">Show</span>` +
    archetypes.map(arch => `
      <button class="filter-btn ${arch === 'all' ? 'active' : ''}"
              onclick="filterCaptains('${arch}', this)">
        ${arch === 'all' ? 'All' : arch}
      </button>`).join('');
}

// Filter captains by archetype
function filterCaptains(key, btn) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.captain-card').forEach(card => {
    if (key === 'all') {
      card.classList.remove('hidden');
    } else {
      const archs = card.dataset.archetypes || '';
      card.classList.toggle('hidden', !archs.includes(key));
    }
  });
}

// Toggle player row expansion
function togglePlayer(id) {
  const row = document.getElementById(id);
  row.classList.toggle('open');
}

// INIT
renderBars();
renderClusters();
renderCaptains();
if (DATA.cluster_map) {
  renderArchetypeLegend();
  renderCaptainFilter();
}
setTimeout(animateBars, 80);
</script>
</body>
</html>"""


def calculate_stats(analysis: dict) -> dict:
    """Calculate additional stats for the header.

    Args:
        analysis: Analysis data dictionary

    Returns:
        Dictionary with calculated stats
    """
    total_players = analysis.get("total_players", 0)
    top_cards = analysis.get("top_cards", [])
    clusters = analysis.get("clusters", [])
    captains = analysis.get("captains", [])

    # Calculate total unique cards
    unique_cards = 0
    for cluster in clusters:
        if "cards" in cluster:
            unique_cards += len(cluster["cards"])
        elif "core" in cluster and "situational" in cluster:
            unique_cards += len(cluster["core"]) + len(cluster["situational"])

    # Top card rate
    top_card_rate = f"{top_cards[0]['pct']:.1f}%" if top_cards else "0%"

    # Get champions from event data
    event = analysis.get("event", {})
    total_champions = event.get("total_champions", total_players)

    return {
        "total_players": total_players,
        "total_captains": len(captains),
        "total_champions": total_champions,
        "unique_cards": unique_cards,
        "top_card_rate": top_card_rate,
    }


def render_report(event_id: str, events_dir: Path) -> str:
    """Generate HTML report from analysis data.

    Args:
        event_id: Event identifier
        events_dir: Path to etl/dist/events directory

    Returns:
        Generated HTML string
    """
    # Load analysis data
    analysis = load_analysis(event_id, events_dir)

    # Calculate stats
    stats = calculate_stats(analysis)

    # Get event info
    event = analysis.get("event", {})
    event_name = event.get("name", "Event")
    event_date = event.get("date", "")

    # Format data for template
    month_year = format_date(event_date)

    # Build template placeholders
    template_vars = {
        "EVENT_NAME": event_name,
        "MONTH_YEAR": month_year,
        "EVENT_DATE": event_date,
        "TOTAL_CHAMPIONS": stats["total_champions"],
        "TOTAL_PLAYERS": stats["total_players"],
        "TOTAL_CAPTAINS": stats["total_captains"],
        "TOTAL_UNIQUE_CARDS": stats["unique_cards"],
        "TOP_CARD_RATE": stats["top_card_rate"],
        "DATA_JSON": json.dumps(analysis, separators=(",", ":")),
    }

    # Get template and fill placeholders
    template = get_html_template()
    for key, value in template_vars.items():
        template = template.replace(f"{{{key}}}", str(value))

    return template


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Render HTML report from analysis data")
    parser.add_argument("event_id", help="Event identifier (e.g., 2026-02)")
    args = parser.parse_args()

    try:
        # Setup paths
        project_root = Path(__file__).parent.parent.parent
        events_dir = project_root / "etl" / "dist" / "events"

        # Generate report
        print(f"Rendering report for {args.event_id}...")
        html = render_report(args.event_id, events_dir)

        # Write output
        output_path = events_dir / f"{args.event_id}-report.html"
        with output_path.open("w", encoding="utf-8") as f:
            f.write(html)

        print(f"✓ Wrote {output_path}")

        # Log summary
        print("\nReport Stats:")
        print(f"  Event: {args.event_id}")
        print(f"  Output: {output_path}")
        print(f"  Size: {len(html):,} bytes")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nHint: Make sure you've run analyze_event.py first to generate the analysis JSON.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error rendering report: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

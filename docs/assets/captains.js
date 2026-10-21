// Shared JS for the captains pages (docs/captains/index.html + docs/captains/<slug>/index.html).
// Pages embed their data as <script type="application/json" id="captain-data|captains-data">.

// Umami custom events (never throws; silent when the script is blocked).
// captain is only present on per-captain pages, absent on the captains index.
let _captain;
function captainData() {
  return _captain ??= JSON.parse(document.getElementById('captain-data').textContent);
}
const CAP = document.getElementById('captain-data') ? captainData().name : undefined;
function trackEvt(name, props) {
  window.umami?.track(name, { ...(CAP && { captain: CAP }), ...props });
}

// Sortable table headers ([data-sort] cells, numeric via td.num)
function sortTable(th) {
  const table = th.closest('table'), tbody = table.querySelector('tbody');
  const idx = Array.from(th.parentNode.children).indexOf(th);
  const dir = th.dataset.dir === 'asc' ? -1 : 1;
  table.querySelectorAll('th').forEach(h => h.removeAttribute('data-dir'));
  th.dataset.dir = dir === 1 ? 'asc' : 'desc';
  trackEvt('table-sort', { table: table.id || 'captains',
                           column: th.dataset.sort, dir: th.dataset.dir });
  const rows = Array.from(tbody.rows);
  rows.sort((a, b) => {
    const av = a.cells[idx].dataset.v ?? a.cells[idx].textContent.trim();
    const bv = b.cells[idx].dataset.v ?? b.cells[idx].textContent.trim();
    const an = parseFloat(av), bn = parseFloat(bv);
    const cmp = (!isNaN(an) && !isNaN(bn) && /^[-\d.]/.test(av) && /^[-\d.]/.test(bv))
      ? an - bn : av.localeCompare(bv);
    return cmp * dir;
  });
  rows.forEach(r => tbody.appendChild(r));
}
document.querySelectorAll('th[data-sort]').forEach(th =>
  th.addEventListener('click', () => sortTable(th)));

// Deck-list filtering: archetype chips AND the text filter hide non-matching
// <details> rows. Month chips don't apply here (they drive Best Cards only).
let deckFilterTracked = false;
const deckFilter = document.getElementById('deck-filter');
let activeArch = '';
function applyDeckFilters() {
  const q = deckFilter ? deckFilter.value.trim().toLowerCase() : '';
  document.querySelectorAll('#deck-list details.deck').forEach(d => {
    const okArch = !activeArch || d.dataset.archetype === activeArch;
    const okText = !q || d.textContent.toLowerCase().includes(q);
    d.hidden = !(okArch && okText);
  });
}
if (deckFilter) {
  deckFilter.addEventListener('input', () => {
    if (!deckFilterTracked) { deckFilterTracked = true; trackEvt('deck-filter'); }
    applyDeckFilters();
  });
}
document.querySelectorAll('#arch-filter .arch-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    activeArch = chip.dataset.arch || '';
    document.querySelectorAll('#arch-filter .arch-chip').forEach(c =>
      c.setAttribute('aria-pressed', c === chip ? 'true' : 'false'));
    applyDeckFilters();
    trackEvt('deck-archetype-filter', { archetype: activeArch || 'all' });
  });
});
// <details> toggles don't bubble; capture-phase listener catches every open
document.addEventListener('toggle', e => {
  const d = e.target;
  if (d.matches?.('details.deck') && d.open) {
    trackEvt('decklist-open', { archetype: d.dataset.archetype });
  }
}, true);

// Best Cards table: recompute from raw decks of the checked months.
// Mirrors etl/scripts/analyze_event.py calculate_captain_stats: presence-count per
// card, sort by freq desc with alphabetical tie-break. Returns the full ranking;
// renderBest12() shows the top best12Limit (12 by default, "Show 12 more" extends).
function best12(decks) {
  const counts = {};
  decks.forEach(deck => new Set(deck).forEach(card => counts[card] = (counts[card] || 0) + 1));
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1));
}
let best12Limit = 12;
function selectedDecks(captain) {
  const selected = Array.from(document.querySelectorAll('#month-filter input:checked'))
    .map(cb => cb.dataset.month);
  return captain.months.filter(m => selected.includes(m.id)).flatMap(m => m.players.map(p => p.deck));
}
// Card cells link to the guide when the payload carries a slug (parity with the
// prerendered rows from render_captains.py _card_pill).
function cardCell(card, cardSlugs) {
  const td = document.createElement('td');
  const slug = cardSlugs?.[card];
  if (slug) {
    const a = document.createElement('a');
    a.className = 'deck-pill';
    a.href = 'https://guide.galaxy.fun/cards/' + slug + '/';
    a.target = '_blank';
    a.rel = 'noopener';
    a.textContent = card;
    td.appendChild(a);
  } else {
    const span = document.createElement('span');
    span.className = 'deck-pill';
    span.textContent = card;
    td.appendChild(span);
  }
  return td;
}
function updateMoreBtn(rankedLength) {
  const more = document.getElementById('best12-more');
  if (!more) return;
  const remaining = rankedLength - best12Limit;
  more.hidden = remaining <= 0;
  if (remaining > 0) more.textContent = `Show ${Math.min(12, remaining)} more`;
}
function renderBest12() {
  const captain = captainData();
  const decks = selectedDecks(captain);
  const ranked = best12(decks);
  const shown = ranked.slice(0, best12Limit);
  const tbody = document.querySelector('#best12-table tbody');
  tbody.innerHTML = '';
  shown.forEach(([card, freq]) => {
    const tr = document.createElement('tr');
    const tdFreq = document.createElement('td');
    tdFreq.className = 'num';
    tdFreq.textContent = freq;
    const tdPct = document.createElement('td');
    tdPct.className = 'num';
    tdPct.textContent = decks.length ? Math.round(freq / decks.length * 100) + '%' : '-';
    tr.append(cardCell(card, captain.cardSlugs), tdFreq, tdPct);
    tbody.appendChild(tr);
  });
  document.querySelector('#best12-count').textContent = decks.length;
  updateMoreBtn(ranked.length);
}

// Captains index: rebuild the captain table from the checked month chips.
// Rows with no decks in the selection are hidden unless every month is checked
// (which restores the full all-time view, matching the static fallback).
function renderIndex() {
  const captains = JSON.parse(document.getElementById('captains-data').textContent);
  const boxes = Array.from(document.querySelectorAll('#month-filter input'));
  const checked = boxes.filter(cb => cb.checked).map(cb => cb.dataset.month);
  const allChecked = checked.length === boxes.length;
  const rows = captains
    .map(c => {
      const ms = c.months.filter(m => checked.includes(m.id));
      return {
        name: c.name, slug: c.slug,
        months: ms.filter(m => m.decks > 0).length,
        decks: ms.reduce((sum, m) => sum + m.decks, 0),
      };
    })
    .sort((a, b) => b.decks - a.decks || a.name.localeCompare(b.name))
    .filter(r => allChecked || r.decks > 0);
  const tbody = document.querySelector('#index-table tbody');
  tbody.innerHTML = '';
  rows.forEach(r => {
    const tr = document.createElement('tr');
    const name = document.createElement('td');
    const a = document.createElement('a');
    a.href = r.slug + '/';
    a.textContent = r.name;
    name.appendChild(a);
    const months = document.createElement('td');
    months.className = 'num';
    months.textContent = r.months;
    const decks = document.createElement('td');
    decks.className = 'num';
    decks.textContent = r.decks;
    tr.append(name, months, decks);
    tbody.appendChild(tr);
  });
}

// Init: each page ships exactly one data payload; render it and wire its chips.
if (document.getElementById('captain-data')) {
  if (document.querySelector('#best12-table tbody')?.rows.length) {
    // Prerendered rows: keep the static HTML (no flicker), just reveal the
    // show-more button when the full ranking exceeds the top 12.
    updateMoreBtn(best12(selectedDecks(captainData())).length);
  } else {
    renderBest12();
  }
  document.querySelectorAll('#month-filter input')
    .forEach(cb => cb.addEventListener('change', () => {
      best12Limit = 12; renderBest12();
      trackEvt('month-filter', { months: Array.from(
        document.querySelectorAll('#month-filter input:checked'))
        .map(cb => cb.dataset.month).join(',') });
    }));
  document.getElementById('best12-more')
    ?.addEventListener('click', () => { best12Limit += 12; renderBest12();
      trackEvt('best12-more', { shown: best12Limit }); });
}
if (document.getElementById('captains-data')) {
  renderIndex();
  document.querySelectorAll('#month-filter input')
    .forEach(cb => cb.addEventListener('change', () => { renderIndex();
      trackEvt('month-filter', { months: Array.from(
        document.querySelectorAll('#month-filter input:checked'))
        .map(cb => cb.dataset.month).join(',') });
    }));
}

// Deck-pill card lookups open guide.galaxy.fun; one delegated listener covers all rows
document.addEventListener('click', e => {
  const a = e.target.closest('a.deck-pill[target=_blank]');
  if (a) trackEvt('card-lookup', { card: a.textContent.trim() });
});

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
// Card cells link to the guide when the payload carries a slug and take their
// type tint from cardColors (parity with _card_pill in render_captains.py).
function cardCell(card, cardSlugs, cardColors) {
  const td = document.createElement('td');
  const slug = cardSlugs?.[card];
  const color = cardColors?.[card];
  let pill;
  if (slug) {
    pill = document.createElement('a');
    pill.href = 'https://guide.galaxy.fun/cards/' + slug + '/';
    pill.target = '_blank';
    pill.rel = 'noopener';
  } else {
    pill = document.createElement('span');
  }
  pill.className = 'deck-pill';
  if (color) {
    pill.style.color = color + 'cc';
    pill.style.borderColor = color + '30';
  }
  pill.textContent = card;
  td.appendChild(pill);
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
    tr.dataset.card = card;
    // The chk cell is always present (empty outside build mode) so sortTable's
    // cell indexes never shift; the column is hidden via #best12-sec:not(.build).
    const tdChk = document.createElement('td');
    tdChk.className = 'chk-cell';
    if (buildMode) {
      const input = document.createElement('input');
      input.type = 'checkbox';
      input.checked = selection.has(card);
      input.setAttribute('aria-label', card);
      input.addEventListener('change', () => toggleCard(card, input, tr));
      tdChk.appendChild(input);
    }
    tr.classList.toggle('sel', buildMode && selection.has(card));
    const tdFreq = document.createElement('td');
    tdFreq.className = 'num';
    tdFreq.textContent = freq;
    const tdPct = document.createElement('td');
    tdPct.className = 'num';
    tdPct.textContent = decks.length ? Math.round(freq / decks.length * 100) + '%' : '-';
    tr.append(tdChk, cardCell(card, captain.cardSlugs, captain.cardColors), tdFreq, tdPct);
    tbody.appendChild(tr);
  });
  document.querySelector('#best12-count').textContent = decks.length;
  updateMoreBtn(ranked.length);
  syncBuilder(ranked.length, shown);
}

// --- Top-12 deck builder (per-captain pages only; context/specs/copy_decklists/top-12-copy-spec.md).
// Selection is name-keyed and held outside the DOM: renderBest12() rebuilds the tbody on
// every month-toggle, show-more and re-sort, so state must survive re-renders.
const bSec = document.getElementById('best12-sec');
let buildMode = false;
let base12 = [];        // top 12 at entry/reset; deck-copy's swap count drifts from this
let secInView = true;
let curRankedLen = 0;
let curShownSet = new Set();
const selection = new Set();

let toastEl, toastTimer;
function toast(msg) {
  toastEl ??= (() => {
    const el = document.createElement('div');
    el.className = 'toast';
    el.setAttribute('aria-live', 'polite');
    document.body.appendChild(el);
    return el;
  })();
  toastEl.textContent = msg;
  toastEl.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.remove('show'), 2200);
}

function top12Now() {
  return best12(selectedDecks(captainData())).slice(0, 12).map(([card]) => card);
}

function updateChip() {
  const chip = document.getElementById('best12-chip');
  if (chip) chip.hidden = !(buildMode && !secInView);
}

function syncBuilder(rankedLen, shown) {
  curRankedLen = rankedLen;
  curShownSet = new Set(shown.map(([card]) => card));
  const actions = document.getElementById('best12-actions');
  if (actions) actions.hidden = buildMode || rankedLen === 0;
  const building = document.getElementById('best12-building');
  if (building) building.hidden = !buildMode;
  if (buildMode) setBar();
  updateChip();
}

function setBar() {
  const status = document.getElementById('best12-status');
  if (!status) return;
  const n = selection.size;
  const over = n - 12;
  status.textContent = n === 12 ? '12/12 · ready to copy'
    : over > 0 ? `${n}/12 · remove ${over}` : `${n}/12 · add ${-over}`;
  const extra = document.getElementById('best12-extra');
  if (extra) {
    const notShown = [...selection].filter(c => !curShownSet.has(c)).length;
    extra.textContent = notShown ? `+${notShown} not shown`
      : curRankedLen < 12 ? `only ${curRankedLen} card${curRankedLen === 1 ? '' : 's'} available` : '';
  }
  const prog = document.getElementById('best12-prog');
  if (prog) {
    prog.style.width = Math.min(100, n / 12 * 100) + '%';
    prog.classList.toggle('over', over > 0);
  }
  const copyBtn = document.getElementById('best12-copy-deck');
  if (copyBtn) copyBtn.setAttribute('aria-disabled', n === 12 ? 'false' : 'true');
  const chip = document.getElementById('best12-chip');
  if (chip) chip.textContent = `Deck ${n}/12 · back to table`;
}

function toggleCard(card, input, tr) {
  if (selection.has(card)) selection.delete(card); else selection.add(card);
  const on = selection.has(card);
  if (input) input.checked = on;
  if (tr) tr.classList.toggle('sel', on);
  setBar();
}

function selectCards(cards) {
  selection.clear();
  cards.forEach(c => selection.add(c));
}

function enterBuild() {
  const top = top12Now();
  selectCards(top);
  base12 = top;
  buildMode = true;
  bSec?.classList.add('build');
  const bar = document.getElementById('best12-bar');
  if (bar) bar.hidden = false;
  renderBest12();
  trackEvt('deck-customize');
}

function exitBuild() {
  buildMode = false;
  selection.clear();
  bSec?.classList.remove('build');
  renderBest12();
  const bar = document.getElementById('best12-bar');
  if (bar) bar.hidden = true;
  updateChip();
}

// One clipboard path for both entry points. The 13-value captain-first cid line is
// pre-checked HERE — buildDeckExport's missing computation is index-shifted for
// captain-first arrays and must not be trusted (names-only fallback via cids=null).
function copyDeckCards(cards, evt, props) {
  const captain = captainData();
  const map = captain.cardCids || {};
  const cids = [map[captain.name], ...cards.map(c => map[c])];
  const complete = cids.every(Boolean);
  const { text } = buildDeckExport(captain.name, cards, complete ? cids : null);
  copyDeckText(text).then(ok => {
    if (!ok) { toast('Copy failed'); return; }
    toast(complete ? 'Copied' : 'Copied (no IDs)');
    trackEvt(evt, props);
  });
}

function copyTop12() {
  copyDeckCards(top12Now(), 'copy-top-12');
}

function copySelection() {
  if (selection.size !== 12) {
    // aria-disabled swallows nothing: a real disabled attribute would eat the tap
    toast(selection.size > 12 ? `Remove ${selection.size - 12} first` : `Add ${12 - selection.size} more`);
    return;
  }
  const base = new Set(base12);
  // Order by the current ranking, then append selected cards that dropped out of
  // it (month filter) — they stay selected and counted, so they must ship too.
  const ranked = best12(selectedDecks(captainData())).map(([c]) => c);
  const cards = [...ranked.filter(c => selection.has(c)), ...[...selection].filter(c => !ranked.includes(c))];
  copyDeckCards(cards, 'deck-copy', { swaps: cards.filter(c => !base.has(c)).length });
}

if (bSec) {
  document.getElementById('best12-copy-top')?.addEventListener('click', copyTop12);
  document.getElementById('best12-customize')?.addEventListener('click', enterBuild);
  document.getElementById('best12-cancel')?.addEventListener('click', exitBuild);
  document.getElementById('best12-reset')?.addEventListener('click', () => {
    // Reset recomputes from the current filter, not the one at entry.
    const top = top12Now();
    selectCards(top);
    base12 = top;
    renderBest12();
  });
  document.getElementById('best12-copy-deck')?.addEventListener('click', copySelection);
  document.getElementById('best12-chip')?.addEventListener('click', () => bSec.scrollIntoView({ behavior: 'smooth' }));
  // Row taps toggle in build mode; the checkbox's own change event handles itself,
  // and guide links are suppressed (pointer-events CSS + preventDefault for keyboard).
  document.getElementById('best12-table')?.addEventListener('click', e => {
    if (!buildMode) return;
    if (e.target.closest?.('a.deck-pill')) e.preventDefault?.();
    const tr = e.target.closest?.('tr');
    if (!tr) return;
    const input = tr.querySelector('input');
    if (input && e.target !== input) toggleCard(tr.dataset.card, input, tr);
  });
  if ('IntersectionObserver' in window) {
    new window.IntersectionObserver(entries => {
      secInView = entries[0]?.isIntersecting ?? true;
      updateChip();
    }).observe(bSec);
  }
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

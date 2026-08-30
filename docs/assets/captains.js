// Shared JS for the captains pages (docs/captains/index.html + docs/captains/<slug>/index.html).
// Pages embed their data as <script type="application/json" id="captain-data|captains-data">.

// Sortable table headers ([data-sort] cells, numeric via td.num)
function sortTable(th) {
  const table = th.closest('table'), tbody = table.querySelector('tbody');
  const idx = Array.from(th.parentNode.children).indexOf(th);
  const dir = th.dataset.dir === 'asc' ? -1 : 1;
  table.querySelectorAll('th').forEach(h => h.removeAttribute('data-dir'));
  th.dataset.dir = dir === 1 ? 'asc' : 'desc';
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

// Deck-list filtering (#deck-filter hides rows whose text doesn't match)
const deckFilter = document.getElementById('deck-filter');
if (deckFilter) {
  deckFilter.addEventListener('input', () => {
    const q = deckFilter.value.toLowerCase();
    document.querySelectorAll('#deck-table tbody tr').forEach(tr => {
      tr.style.display = tr.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  });
}

// Best 12 table: recompute from raw decks of the checked months.
// Mirrors etl/scripts/analyze_event.py calculate_captain_stats: presence-count per
// card, sort by freq desc with alphabetical tie-break, take top 12.
function best12(decks) {
  const counts = {};
  decks.forEach(deck => new Set(deck).forEach(card => counts[card] = (counts[card] || 0) + 1));
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1))
    .slice(0, 12);
}
function renderBest12() {
  const captain = JSON.parse(document.getElementById('captain-data').textContent);
  const selected = Array.from(document.querySelectorAll('#month-filter input:checked'))
    .map(cb => cb.dataset.month);
  const decks = captain.months.filter(m => selected.includes(m.id)).flatMap(m => m.players.map(p => p.deck));
  const tbody = document.querySelector('#best12-table tbody');
  tbody.innerHTML = '';
  best12(decks).forEach(([card, freq]) => {
    const tr = document.createElement('tr');
    const tdCard = document.createElement('td');
    tdCard.textContent = card;
    const tdFreq = document.createElement('td');
    tdFreq.className = 'num';
    tdFreq.textContent = freq;
    const tdPct = document.createElement('td');
    tdPct.className = 'num';
    tdPct.textContent = decks.length ? Math.round(freq / decks.length * 100) + '%' : '-';
    tr.append(tdCard, tdFreq, tdPct);
    tbody.appendChild(tr);
  });
  document.querySelector('#best12-count').textContent = decks.length;
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
  renderBest12();
  document.querySelectorAll('#month-filter input')
    .forEach(cb => cb.addEventListener('change', renderBest12));
}
if (document.getElementById('captains-data')) {
  renderIndex();
  document.querySelectorAll('#month-filter input')
    .forEach(cb => cb.addEventListener('change', renderIndex));
}

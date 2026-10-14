// Smoke test for Umami event tracking in docs/assets/*.js. Run: node etl/tests/test_tracking_smoke.mjs
// Loads each file in a vm sandbox with minimal DOM stubs and asserts trackEvt
// reaches window.umami.track with the expected event names and properties.
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert';

// Objects from the vm sandbox have a different Object prototype, so compare structurally
const same = (a, b) => assert.strictEqual(JSON.stringify(a), JSON.stringify(b));

const REPORT_JS = new URL('../../docs/assets/galaxy-report.js', import.meta.url);
const CAPTAINS_JS = new URL('../../docs/assets/captains.js', import.meta.url);

function el(overrides = {}) {
  return {
    classList: { add() {}, remove() {}, toggle() {}, contains: () => false },
    addEventListener() {},
    querySelector: () => null,
    querySelectorAll: () => [],
    dataset: {},
    style: {},
    textContent: '',
    appendChild() {},
    rows: [],
    ...overrides,
  };
}

function load(file, doc, extra = {}) {
  const calls = [];
  const ctx = {
    document: doc,
    requestAnimationFrame: (fn) => fn(),
    setTimeout: (fn) => fn(),
    window: { umami: { track: (name, props) => calls.push([name, props]) } },
    ...extra,
  };
  vm.createContext(ctx);
  vm.runInContext(readFileSync(file, 'utf8'), ctx);
  return { ctx, calls };
}

function docStub(overrides = {}) {
  const listeners = {};
  return {
    listeners,
    addEventListener(type, fn) { (listeners[type] ??= []).push(fn); },
    getElementById: () => null,
    querySelector: () => null,
    querySelectorAll: () => [],
    ...overrides,
  };
}

// --- galaxy-report.js ---
{
  const DATA = { event: { id: '2026-09' } };
  const clickTarget = el({ textContent: 'Pirate Ship ' });
  const doc = docStub();
  doc.getElementById = (id) => id === 'cap-0p0' ? row : el();
  const { ctx, calls } = load(REPORT_JS, doc, { DATA, CARDS: {} });

  ctx.showSection('captains', el());
  same(calls.at(-1), ['section-view', { report: '2026-09', section: 'captains' }]);

  const card = el({ querySelector: (sel) => sel === '.captain-name' ? { textContent: 'Hannibal ' } : null });
  ctx.switchView('cap-0', 'deck', el({ closest: () => card }));
  same(calls.at(-1), ['captain-view', { report: '2026-09', captain: 'Hannibal', view: 'deck' }]);

  const row = el({
    classList: { toggle() {}, contains: () => true },
    closest: () => card,
    dataset: { archetypes: 'Pirates' },
  });
  ctx.togglePlayer('cap-0p0');
  same(calls.at(-1), ['decklist-open', { report: '2026-09', captain: 'Hannibal', archetype: 'Pirates' }]);

  ctx.filterCaptains('mage', el());
  same(calls.at(-1), ['captain-filter', { report: '2026-09', archetype: 'mage' }]);

  doc.listeners.click[0]({ target: { closest: (sel) => sel === 'a.card-link[target=_blank]' ? clickTarget : null } });
  same(calls.at(-1), ['card-lookup', { report: '2026-09', card: 'Pirate Ship' }]);
  console.log('galaxy-report.js: 5 events OK');
}

// --- captains.js ---
{
  const recording = (o) => { o.listeners = {}; o.addEventListener = (t, fn) => { (o.listeners[t] ??= []).push(fn); }; return o; };
  const monthInputs = [
    recording(el({ dataset: { month: '2026-05' }, checked: true })),
    recording(el({ dataset: { month: '2026-06' }, checked: false })),
  ];
  const tbody = el();
  const byId = {
    'captain-data': { textContent: JSON.stringify({ name: 'Hannibal', months: [] }) },
    'deck-filter': recording(el({ value: '' })),
    'best12-more': recording(el()),
  };
  const doc = docStub({
    getElementById: (id) => byId[id] ?? null,
    querySelector: (sel) => sel === '#best12-table tbody' ? tbody : el(),
    querySelectorAll: (sel) => sel === '#month-filter input' ? monthInputs
      : sel === '#month-filter input:checked' ? monthInputs.filter(cb => cb.checked) : [],
  });
  const { ctx, calls } = load(CAPTAINS_JS, doc);

  // month chip change (captain page init block)
  monthInputs[0].listeners.change[0]();
  same(calls.at(-1), ['month-filter', { captain: 'Hannibal', months: '2026-05' }]);

  // best12-more click
  byId['best12-more'].listeners.click[0]();
  same(calls.at(-1), ['best12-more', { captain: 'Hannibal', shown: 24 }]);

  // sortTable
  const th = el({
    parentNode: { children: [{}] },
    closest: () => el({ id: 'best12-table', querySelector: () => tbody, querySelectorAll: () => [] }),
    dataset: {},
  });
  // el() shares one classList object across calls; give sortTable its own dataset/dir path
  th.dataset = {};
  ctx.sortTable(th);
  same(calls.at(-1),
    ['table-sort', { captain: 'Hannibal', table: 'best12-table', column: undefined, dir: 'asc' }]);

  // deck-filter fires once across two input events, with no query text
  doc.getElementById('deck-filter').listeners.input[0]();
  doc.getElementById('deck-filter').listeners.input[0]();
  const deckCalls = calls.filter(([name]) => name === 'deck-filter');
  assert.strictEqual(deckCalls.length, 1);
  assert.strictEqual(deckCalls[0][1].captain, 'Hannibal');
  assert.strictEqual(Object.keys(deckCalls[0][1]).join(','), 'captain');
  console.log('captains.js: 4 events OK');
}

console.log('all tracking smoke tests passed');

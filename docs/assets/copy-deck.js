// Copy-decklist button: shared by report + captain pages. Each generator tags the
// script with data-page ("report" | "captain") so copies can be attributed in Umami.
// Buttons baked by render_captains.py / renderCaptains() carry data-captain plus a
// captain-first data-cids ID line; rows with an incomplete cid set omit data-cids
// and copy names-only instead of risking a wrong ID line.

function buildDeckExport(captain, cards, cids) {
  const missing = cids ? cards.filter((_, i) => !cids[i]) : cards.slice();
  const lines = ['Once Upon a Galaxy - Galaxy Stats Decklist'];
  if (!missing.length) lines.push(cids.join('-'));
  lines.push(`Captain: ${captain}`, ...cards);
  return { text: lines.join('\n'), missing };
}

const COPY_DECK_PAGE = document.currentScript?.dataset?.page || 'unknown';

const COPY_ICON =
  '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="#9a9ca8" stroke-width="1.5"' +
  ' stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
  '<rect x="6" y="6" width="8.5" height="8.5" rx="1.3"/>' +
  '<path d="M3.5 10.5h-.8A1.3 1.3 0 0 1 1.4 9.2v-6.5A1.3 1.3 0 0 1 2.7 1.4h6.5a1.3 1.3 0 0 1 1.3 1.3v.8"/></svg>';
const CHECK_ICON =
  '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="#c8a96e" stroke-width="1.5"' +
  ' stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M13 4.5 6.5 11 3 7.5"/></svg>';
const FAIL_ICON =
  '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="#9a9ca8" stroke-width="1.5"' +
  ' stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 4 4 12M4 4l8 8"/></svg>';

function copyDeckText(text) {
  if (navigator.clipboard?.writeText) {
    return navigator.clipboard.writeText(text).then(() => true, () => copyDeckFallback(text));
  }
  return Promise.resolve(copyDeckFallback(text));
}

// execCommand fallback for non-HTTPS / older browsers
function copyDeckFallback(text) {
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.setAttribute('readonly', '');
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.select();
  let ok = false;
  try {
    ok = document.execCommand('copy');
  } catch {
    ok = false;
  }
  ta.remove();
  return ok;
}

function showCopyFeedback(btn, icon, title) {
  const original = btn.innerHTML;
  btn.innerHTML = icon;
  if (title) btn.setAttribute('title', title);
  setTimeout(() => {
    btn.innerHTML = original;
    if (title) btn.removeAttribute('title');
  }, 1500);
}

// Capture phase: report deck headers carry inline onclick (togglePlayer), which fires
// during bubble — a document-level bubble listener runs after it, too late to stop.
// preventDefault still cancels the <summary> default toggle on captain pages.
document.addEventListener('click', (e) => {
  const btn = e.target.closest('button.copy-deck');
  if (!btn) return;
  e.preventDefault();
  e.stopPropagation();
  const row = btn.closest('details.deck, .player-row');
  const cards = [...row.querySelectorAll('.deck-pill')].map(p => p.textContent.trim());
  const cids = btn.dataset.cids ? btn.dataset.cids.split('-').map(Number) : null;
  const { text, missing } = buildDeckExport(btn.dataset.captain, cards, cids);
  copyDeckText(text).then(ok => {
    if (ok) {
      if (missing.length) {
        // A plain checkmark would read as game-ready when the paste may not import
        console.warn('deck copied without card IDs (missing cids for):', missing.join(', '));
        showCopyFeedback(btn, CHECK_ICON, 'Copied (no IDs)');
      } else {
        showCopyFeedback(btn, CHECK_ICON);
      }
      window.umami?.track('deck-copy', { page: COPY_DECK_PAGE, captain: btn.dataset.captain });
    } else {
      showCopyFeedback(btn, FAIL_ICON, 'Copy failed');
    }
  });
}, true);

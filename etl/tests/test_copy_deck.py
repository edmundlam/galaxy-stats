"""Tests for the copy-decklist feature: export builder (JS) + name->cid inversion (Python)."""

import json
import subprocess
from pathlib import Path

import pytest

from scripts.render_captains import build_card_cids, deck_used_slugs

REPO = Path(__file__).resolve().parents[2]
JS = REPO / "docs" / "assets" / "copy-deck.js"

GOLDEN = """Once Upon a Galaxy - Galaxy Stats Decklist
4052-4036-4014-4005-4043-4039-4011-4049-2159-4048-4001-2006-4029
Captain: Bing Wu
Antiquitoy
Happy Little Painter
Blue Paintkin
The Mad Splatter
Yellow Paintkin
Mana Potion
Varnish
Crystal
Owlabaster
Selphiea
Cotton Candy Dandy
Rocky, the Roller"""

DOM_STUB = """
const listeners = {};
const document = {
  currentScript: { dataset: { page: 'report' } },
  addEventListener(type, fn) { (listeners[type] ??= []).push(fn); },
};
"""

CAPTURE_STUB = """
const navigator = { clipboard: { writeText: () => Promise.resolve() } };
const window = {};
const registrations = [];
const document = {
  currentScript: { dataset: { page: 'report' } },
  addEventListener(type, fn, opts) { registrations.push({ fn, capture: opts === true || !!opts?.capture }); },
};
"""


def run_builder(captain, cards, cids) -> dict:
    """Load copy-deck.js in node with DOM stubs, call buildDeckExport, return its result."""
    setup = (
        DOM_STUB
        + f"const result = buildDeckExport({json.dumps(captain)}, {json.dumps(cards)}, {json.dumps(cids)});\n"
        + "console.log(JSON.stringify(result));\n"
    )
    result = subprocess.run(["node", "-e", setup + JS.read_text()], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def test_golden_fixture_is_byte_exact():
    """The spec's in-game-verified decklist must come out byte-exact."""
    cards = GOLDEN.splitlines()[3:]
    cids = [int(x) for x in GOLDEN.splitlines()[1].split("-")]
    assert run_builder("Bing Wu", cards, cids) == {"text": GOLDEN, "missing": []}


def test_punctuation_names_survive():
    cards = ["Maverick & Icewing", "Rocky, the Roller", "Al-mi'raj"]
    out = run_builder("Hannibal", cards, [1, 2, 3, 4])["text"]
    for name in cards:
        assert name in out


def test_short_and_long_decks_emit_whatever_they_contain():
    one = run_builder("Cap", ["X"], [1, 2])["text"].splitlines()
    assert one == ["Once Upon a Galaxy - Galaxy Stats Decklist", "1-2", "Captain: Cap", "X"]
    many = run_builder("Cap", [f"C{i}" for i in range(15)], list(range(1, 17)))["text"].splitlines()
    assert len(many) == 18
    assert many[-1] == "C14"


def test_missing_cid_drops_id_line_and_reports_missing_names():
    out = run_builder("Cap", ["A", "B", "C"], [10, None, 30])
    assert out["text"] == "Once Upon a Galaxy - Galaxy Stats Decklist\nCaptain: Cap\nA\nB\nC"
    assert out["missing"] == ["B"]


def test_null_cids_go_names_only():
    out = run_builder("Cap", ["A", "B"], None)
    assert out["text"] == "Once Upon a Galaxy - Galaxy Stats Decklist\nCaptain: Cap\nA\nB"
    assert out["missing"] == ["A", "B"]


def test_collision_drops_ambiguous_name():
    """A display name mapping to two used slugs is dropped — never guess a cid."""
    cards = {
        "char_a": {"name": "Beanie Baby", "cid": 1036},
        "token_a": {"name": "Beanie Baby", "cid": 908},
        "solo": {"name": "Solo Card", "cid": 7},
    }
    assert build_card_cids(cards, {"char_a", "token_a", "solo"}) == {"Solo Card": 7}


def test_deck_used_variant_resolves_unique_name():
    cards = {
        "char_a": {"name": "Beanie Baby", "cid": 1036},
        "token_a": {"name": "Beanie Baby", "cid": 908},
    }
    assert build_card_cids(cards, {"char_a"}) == {"Beanie Baby": 1036}


def test_entries_without_cid_are_skipped():
    assert build_card_cids({"old": {"name": "Old Card"}}, {"old"}) == {}


def test_deck_used_slugs_collects_across_events(tmp_path):
    for event_id, decks in [("2026-01", [["a", "b"], ["c"]]), ("2026-02", [["b"]])]:
        event_dir = tmp_path / event_id
        event_dir.mkdir()
        (event_dir / "event.json").write_text(json.dumps({"players": [{"deck": d} for d in decks]}))
    assert deck_used_slugs(tmp_path) == {"a", "b", "c"}


def test_copy_click_stops_propagation_before_ancestor_handlers():
    """Report deck rows carry inline onclick on the header, which fires during bubble —
    before any document-level bubble listener. The copy handler must register in
    capture phase to stop the event before the ancestor toggles the row."""
    sim = """
let prevented = false;
let stopped = false;
const row = { querySelectorAll: (sel) => [{ textContent: 'Card A' }] };
const btn = {
  dataset: { captain: 'Cap', cids: '1-2' },
  closest: (sel) => sel === 'button.copy-deck' ? btn : row,
  innerHTML: '<svg/>',
  setAttribute() {},
  removeAttribute() {},
};
const e = {
  target: btn,
  preventDefault: () => { prevented = true; },
  stopPropagation: () => { stopped = true; },
};
const capture = registrations.filter((r) => r.capture);
const bubble = registrations.filter((r) => !r.capture);
// dispatch order for a click inside .player-row-header: document capture →
// target → ancestor inline onclick (bubble) → document bubble
capture[0].fn(e);
const ancestorFired = !stopped;
console.log(JSON.stringify({
  captureListeners: capture.length,
  prevented,
  ancestorFired,
  bubbleListeners: bubble.length,
}));
"""
    script = CAPTURE_STUB + JS.read_text() + sim
    result = json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout)
    assert result["captureListeners"] == 1
    assert result["bubbleListeners"] == 0, "a bubble-phase registration runs after the ancestor onclick"
    assert result["prevented"], "preventDefault must cancel the <summary> toggle on captain pages"
    assert not result["ancestorFired"], "inline onclick on the header must never fire"


@pytest.fixture(autouse=True)
def require_node():
    subprocess.run(["node", "--version"], capture_output=True, check=True)

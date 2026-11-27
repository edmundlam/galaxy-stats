"""Tests for captain links in the shared report JS (docs/assets/galaxy-report.js)."""

import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
JS = REPO / "docs" / "assets" / "galaxy-report.js"

DOM_STUB = """
let captured;
const listeners = {};
const document = {
  // galaxy-report.js registers a delegated click listener at load time
  addEventListener(type, fn) { (listeners[type] ??= []).push(fn); },
  getElementById: () => ({ set innerHTML(v) { captured = v; } }),
};
"""


def run_js(setup: str, call: str) -> str:
    """Load the shared report JS in node with stubs prepended, run `call`, return output."""
    script = setup + JS.read_text() + "\n" + call
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
    return result.stdout


def test_captain_href_maps_slug_to_page_url():
    out = run_js(DOM_STUB, "console.log(captainHref('galileo_galilei'));")
    assert out.strip() == "../../captains/galileo-galilei/"


def test_captain_bars_link_captain_pages():
    setup = DOM_STUB + (
        "const DATA = { top_captains: [{ slug: 'galileo_galilei', name: 'Galileo Galilei', freq: 5 }] };"
    )
    out = run_js(setup, "renderCaptainBars(); console.log(captured);")
    assert 'href="../../captains/galileo-galilei/"' in out
    assert ">Galileo Galilei</a>" in out


def test_captain_bars_without_slug_stay_plain():
    setup = DOM_STUB + "const DATA = { top_captains: [{ name: 'Galileo Galilei', freq: 5 }] };"
    out = run_js(setup, "renderCaptainBars(); console.log(captured);")
    assert "<a " not in out
    assert ">Galileo Galilei<" in out


def test_captain_cards_link_captain_pages():
    setup = DOM_STUB + (
        "const DATA = { clusters: [], captains: [{ slug: 'galileo_galilei',"
        " name: 'Galileo Galilei', n: 6, signature: [], best12: [], players: [] }] };"
    )
    out = run_js(setup, "renderCaptains(); console.log(captured);")
    assert 'href="../../captains/galileo-galilei/"' in out
    assert ">Galileo Galilei</a>" in out


@pytest.fixture(autouse=True)
def require_node():
    subprocess.run(["node", "--version"], capture_output=True, check=True)


# --- Copy-decklist button ---

DECK_DATA = (
    "const CARDS = {};"
    "const DATA = { clusters: [], captains: [{ slug: 'bing_wu', name: 'Bing Wu', n: 1, signature: [], best12: [],"
    " players: [{ username: 'u', archetype: 'Toys', deck: ['Antiquitoy', 'Rocky, the Roller'] }] }] };"
)


def test_deck_view_has_no_copy_button_without_card_cids():
    """Old reports lack the embedded CARD_CIDS const; the shared JS must stay button-free there."""
    out = run_js(DOM_STUB + DECK_DATA, "renderCaptains(); console.log(captured);")
    assert "copy-deck" not in out


def test_deck_view_bakes_copy_button_captain_first():
    setup = (
        DOM_STUB + DECK_DATA + " const CARD_CIDS = { 'Bing Wu': 4052, 'Antiquitoy': 4036, 'Rocky, the Roller': 4029 };"
    )
    out = run_js(setup, "renderCaptains(); console.log(captured);")
    assert (
        '<button type="button" class="copy-deck" data-captain="Bing Wu" data-cids="4052-4036-4029"'
        ' aria-label="Copy decklist">' in out
    )
    header = re.search(r'class="player-row-header"[^>]*>(.*?)<div class="player-deck">', out, re.DOTALL).group(1)
    assert header.index('class="tag"') < header.index('class="copy-deck"') < header.index('class="expand-icon"')


def test_deck_view_button_without_cids_when_a_card_is_unknown():
    setup = DOM_STUB + DECK_DATA + " const CARD_CIDS = { 'Bing Wu': 4052, 'Antiquitoy': 4036 };"
    out = run_js(setup, "renderCaptains(); console.log(captured);")
    assert "data-cids" not in out
    assert 'class="copy-deck"' in out

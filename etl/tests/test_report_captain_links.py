"""Tests for captain links in the shared report JS (docs/assets/galaxy-report.js)."""

import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
JS = REPO / "docs" / "assets" / "galaxy-report.js"

DOM_STUB = """
let captured;
const document = { getElementById: () => ({ set innerHTML(v) { captured = v; } }) };
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

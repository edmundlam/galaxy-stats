"""Tests for copy-decklist support in report pages (render_report.py)."""

import json
import re
from pathlib import Path

from scripts.render_report import render_report

REPO = Path(__file__).resolve().parents[2]
DIST = REPO / "etl" / "dist"


def card_cids_of(html: str) -> dict:
    m = re.search(r"const CARD_CIDS = (\{.*?\});", html, re.DOTALL)
    assert m, "CARD_CIDS not embedded"
    return json.loads(m.group(1))


def test_report_embeds_card_cids_next_to_cards():
    html = render_report("2026-11", DIST / "events")
    assert html.index("const CARDS = ") < html.index("const CARD_CIDS = ")
    assert all(isinstance(v, int) for v in card_cids_of(html).values())


def test_report_card_cids_pick_deck_used_variants():
    """Real duplicate-name case: beanie_baby (1036) is deck-used, treasure token beanie_baby_treasure (908) is not."""
    assert card_cids_of(render_report("2026-11", DIST / "events"))["Beanie Baby"] == 1036


def test_report_card_cids_include_captains():
    assert card_cids_of(render_report("2026-11", DIST / "events"))["Bing Wu"] == 4052


def test_report_without_cids_embeds_undefined_const(monkeypatch):
    """Old-shape cards.json (no cids) must leave CARD_CIDS undefined so the shared JS renders no buttons."""
    from scripts import render_report as rr

    monkeypatch.setattr(rr, "load_cards", lambda root: {"old_slug": {"name": "Old Card"}})
    html = rr.render_report("2026-11", DIST / "events")
    assert "const CARD_CIDS = undefined;" in html
    assert "const CARD_CIDS = {" not in html


def test_report_loads_copy_deck_script_with_page_attr():
    html = render_report("2026-11", DIST / "events")
    assert re.search(r'<script src="\.\./\.\./assets/copy-deck\.js\?v=\d+" data-page="report"></script>', html)

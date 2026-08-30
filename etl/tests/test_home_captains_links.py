"""Tests for captain discovery entry points on the home page (docs/index.html)."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HOME = REPO / "docs" / "index.html"


def home_html() -> str:
    return HOME.read_text(encoding="utf-8")


def test_home_links_captains_index():
    assert 'href="captains/"' in home_html()


def test_quick_links_section_precedes_reports_section():
    html = home_html()
    assert html.index('class="section-title">Quick Links') < html.index('class="section-title">Reports')

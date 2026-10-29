"""Tests for the leaderboard entry point on the home page (docs/index.html)."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HOME = REPO / "docs" / "index.html"


def home_html() -> str:
    return HOME.read_text(encoding="utf-8")


def test_home_links_leaderboard():
    assert 'href="leaderboard/"' in home_html()


def test_home_has_no_decklists_link_yet():
    assert 'href="decklists/"' not in home_html(), "the decklists page does not exist yet"

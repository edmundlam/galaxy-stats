"""Tests for captains-index discovery links in the report template (render_report.py)."""

from scripts.render_report import get_html_template


def section(html: str, marker: str) -> str:
    """Return the template chunk from `marker` to the next section comment."""
    start = html.index(marker)
    nxt = html.find("<!--", start + 1)
    return html[start : nxt if nxt != -1 else len(html)]


def test_captains_section_desc_links_captains_index():
    desc = section(get_html_template(), 'id="captains"')
    assert 'href="../../captains/"' in desc
    assert "all months" in desc


def test_captains_section_desc_mentions_captain_name_links():
    desc = section(get_html_template(), 'id="captains"')
    assert "Clicking a captain's name" in desc


def test_captain_popularity_links_captains_index():
    top = section(get_html_template(), 'id="top-cards"')
    desc = top[top.index("Captain Popularity") : top.index("captains-chart-container")]
    assert 'href="../../captains/"' in desc
    assert "all months" in desc

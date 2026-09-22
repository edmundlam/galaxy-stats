"""Tests for parse_event.py — champion entry extraction."""

import textwrap

from scripts.parse_event import parse_event


def _write_event(tmp_path, html: str) -> str:
    path = tmp_path / "event.html"
    path.write_text(html, encoding="utf-8")
    return str(path)


def test_skips_champ_with_missing_deck_info(tmp_path):
    """Champ entries with no captain and no cards ("deck info missing") are dropped."""
    html = textwrap.dedent(
        """\
        <html><body>
        <li class="champ-info">
          <div class="champ-name">adub</div>
          <div class="champ-captain"><a href="https://guide.galaxy.fun/cards/galileo_galilei/">Galileo Galilei</a></div>
          <ul class="cards-list"><a href="https://guide.galaxy.fun/cards/card_a/">Card A</a></ul>
        </li>
        <li class="champ-info" data-searchable="kvothedota  ">
          <div class="champ-name">Kvothedota</div>
          <div class="missing-info">deck info missing</div>
        </li>
        </body></html>
        """
    )
    event_data, _, _ = parse_event(_write_event(tmp_path, html), "2026-09")

    usernames = [p["username"] for p in event_data["players"]]
    assert usernames == ["adub"]
    assert event_data["event"]["total_champions"] == 1

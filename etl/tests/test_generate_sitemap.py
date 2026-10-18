"""Tests for generate_sitemap.py — captain URL inclusion and lastmod rules."""

import json

from scripts.generate_sitemap import generate_sitemap


def write_analysis(events_dir, event_id: str, date: str, captain_slugs: list[str]) -> None:
    """Write a minimal analysis.json with the fields the sitemap reads."""
    event_dir = events_dir / event_id
    event_dir.mkdir(parents=True)
    payload = {
        "event": {"id": event_id, "date": date},
        "captains": [{"slug": slug} for slug in captain_slugs],
    }
    (event_dir / "analysis.json").write_text(json.dumps(payload))


def lastmod_for(xml: str, url_path: str) -> str:
    """Return the lastmod value inside the <url> block for url_path."""
    block = xml[xml.index(f"<loc>https://example.com{url_path}</loc>") :]
    start = block.index("<lastmod>") + len("<lastmod>")
    return block[start : block.index("</lastmod>")]


def test_sitemap_includes_captains(tmp_path):
    docs = tmp_path / "docs"
    (docs / "captains" / "galileo-galilei").mkdir(parents=True)
    (docs / "captains" / "galileo-galilei" / "index.html").write_text("<html></html>")
    (docs / "captains" / "index.html").write_text("<html></html>")
    xml = generate_sitemap(docs, "https://example.com")
    assert "<loc>https://example.com/captains/</loc>" in xml
    assert "<loc>https://example.com/captains/galileo-galilei/</loc>" in xml


def test_report_lastmod_is_event_date_not_build_time(tmp_path):
    docs = tmp_path / "docs"
    (docs / "reports" / "2026-09").mkdir(parents=True)
    (docs / "reports" / "2026-09" / "index.html").write_text("<html></html>")
    events = tmp_path / "events"
    write_analysis(events, "2026-09", "2026-09-18", [])
    xml = generate_sitemap(docs, "https://example.com", events_dir=events)
    assert lastmod_for(xml, "/reports/2026-09/") == "2026-09-18"


def test_captain_lastmod_is_latest_event_appeared_in(tmp_path):
    docs = tmp_path / "docs"
    for slug in ("galileo-galilei", "ammit"):
        (docs / "captains" / slug).mkdir(parents=True)
        (docs / "captains" / slug / "index.html").write_text("<html></html>")
    (docs / "captains" / "index.html").write_text("<html></html>")
    events = tmp_path / "events"
    write_analysis(events, "2026-08", "2026-08-15", ["galileo_galilei", "ammit"])
    write_analysis(events, "2026-09", "2026-09-18", ["galileo_galilei"])
    xml = generate_sitemap(docs, "https://example.com", events_dir=events)
    assert lastmod_for(xml, "/captains/galileo-galilei/") == "2026-09-18"
    assert lastmod_for(xml, "/captains/ammit/") == "2026-08-15"
    # Captains index and root reflect the newest event site-wide
    assert lastmod_for(xml, "/captains/") == "2026-09-18"
    assert lastmod_for(xml, "/") == "2026-09-18"


def test_lastmod_falls_back_to_mtime_without_event_data(tmp_path):
    docs = tmp_path / "docs"
    (docs / "reports" / "2026-01").mkdir(parents=True)
    (docs / "reports" / "2026-01" / "index.html").write_text("<html></html>")
    xml = generate_sitemap(docs, "https://example.com", events_dir=tmp_path / "missing")
    assert "<lastmod>2" in xml  # mtime is a real date, not empty

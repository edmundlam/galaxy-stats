"""Tests for generate_sitemap.py — captain URL inclusion."""

from scripts.generate_sitemap import generate_sitemap


def test_sitemap_includes_captains(tmp_path):
    docs = tmp_path / "docs"
    (docs / "captains" / "galileo-galilei").mkdir(parents=True)
    (docs / "captains" / "galileo-galilei" / "index.html").write_text("<html></html>")
    (docs / "captains" / "index.html").write_text("<html></html>")
    xml = generate_sitemap(docs, "https://example.com")
    assert "<loc>https://example.com/captains/</loc>" in xml
    assert "<loc>https://example.com/captains/galileo-galilei/</loc>" in xml

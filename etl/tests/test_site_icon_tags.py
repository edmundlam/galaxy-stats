"""Tests for site icon, manifest, and social-preview tags on report and static pages."""

from pathlib import Path

from scripts.render_report import render_report

REPO = Path(__file__).resolve().parents[2]
DIST = REPO / "etl" / "dist"
DOCS = REPO / "docs"

SNIPPET = [
    '<link rel="icon" href="/favicon.ico" sizes="32x32">',
    '<link rel="icon" href="/icon.svg" type="image/svg+xml">',
    '<link rel="apple-touch-icon" href="/apple-touch-icon.png">',
    '<link rel="manifest" href="/manifest.webmanifest">',
    '<meta name="theme-color" content="#1c1747">',
    '<meta property="og:image" content="https://www.galaxy-stats.com/og-image.png">',
    '<meta name="twitter:card" content="summary_large_image">',
]


def test_report_page_has_icon_and_social_tags():
    html = render_report("2026-08", DIST / "events")
    for tag in SNIPPET:
        assert tag in html, tag
    assert '<meta property="og:url" content="https://www.galaxy-stats.com/reports/2026-08/">' in html


def test_static_pages_have_icon_and_social_tags():
    for page in ("index.html", "about.html"):
        html = (DOCS / page).read_text()
        for tag in SNIPPET:
            assert tag in html, f"{page}: {tag}"

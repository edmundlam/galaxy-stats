"""Tests for render_captains.py — captain page aggregation and rendering."""

import json
import re
from pathlib import Path

import pytest

from scripts.render_captains import (
    ASSET_VERSION,
    aggregate_captains,
    compute_best12,
    render_captain_page,
    render_index_page,
    slug_to_dash,
)

REPO = Path(__file__).resolve().parents[2]
DIST = REPO / "etl" / "dist"


@pytest.fixture()
def events_dir(tmp_path):
    """Two synthetic events with overlapping captains."""
    for event_id, name, date, captains in [
        (
            "2026-01",
            "January Monthly",
            "2026-01-16",
            [
                {
                    "slug": "galileo_galilei",
                    "name": "Galileo Galilei",
                    "n": 2,
                    "signature": [],
                    "best12": [],
                    "players": [
                        {"username": "adub", "archetype": "Treasures", "deck": ["Card A", "Card B", "Card C"]},
                        {"username": "bee", "archetype": "Candy", "deck": ["Card A", "Card D", "Card E"]},
                    ],
                }
            ],
        ),
        (
            "2026-02",
            "February Monthly",
            "2026-02-20",
            [
                {
                    "slug": "galileo_galilei",
                    "name": "Galileo Galilei",
                    "n": 1,
                    "signature": [],
                    "best12": [],
                    "players": [{"username": "cy", "archetype": "Mage", "deck": ["Card A", "Card F", "Card G"]}],
                },
                {
                    "slug": "mystery_captain",
                    "name": "Mystery Captain",
                    "n": 1,
                    "signature": [],
                    "best12": [],
                    "players": [{"username": "dee", "archetype": "Toys", "deck": ["Card H"]}],
                },
            ],
        ),
    ]:
        event_dir = tmp_path / event_id
        event_dir.mkdir()
        (event_dir / "analysis.json").write_text(
            json.dumps({"event": {"id": event_id, "name": name, "date": date}, "captains": captains})
        )
    return tmp_path


@pytest.fixture()
def captains_file(tmp_path):
    p = tmp_path / "captains.json"
    p.write_text(json.dumps({"galileo_galilei": "Galileo Galilei", "loki": "Loki"}))
    return p


def test_slug_to_dash():
    assert slug_to_dash("galileo_galilei") == "galileo-galilei"


def test_all_captain_keys_roundtrip_to_safe_slugs():
    keys = json.loads((DIST / "captains.json").read_text())
    assert len(keys) > 0
    for key in keys:
        assert re.fullmatch(r"[a-z0-9-]+", slug_to_dash(key)), key


def test_aggregation_groups_across_events_and_sorts_months(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    galileo = caps["galileo-galilei"]
    assert galileo["name"] == "Galileo Galilei"
    assert [m["id"] for m in galileo["months"]] == ["2026-01", "2026-02"]
    assert [p["username"] for m in galileo["months"] for p in m["players"]] == ["adub", "bee", "cy"]
    month = galileo["months"][0]
    assert month["date"] == "2026-01-16"
    assert month["event"] == "January Monthly"


def test_players_pass_through_unchanged(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    expected = {"username": "adub", "archetype": "Treasures", "deck": ["Card A", "Card B", "Card C"]}
    assert caps["galileo-galilei"]["months"][0]["players"][0] == expected


def test_captain_without_events_gets_empty_months(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    assert caps["loki"] == {"slug": "loki", "name": "Loki", "months": []}


def test_unknown_captain_falls_back_to_slug_name(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    assert caps["mystery-captain"]["name"] == "mystery_captain"


def test_best12_matches_analyze_event_parity():
    """Python mirror of the client-side algorithm must reproduce analyze_event.py's best12."""
    analysis = json.loads((DIST / "events" / "2026-08" / "analysis.json").read_text())
    captain = next(c for c in analysis["captains"] if c["slug"] == "galileo_galilei")
    decks = [p["deck"] for p in captain["players"]]
    mirror = [(r["card"], r["freq"]) for r in compute_best12(decks)]
    precomputed = [(r["card"], r["freq"]) for r in captain["best12"]]
    assert mirror == precomputed


def test_best12_caps_at_twelve():
    decks = [[f"Card {i}"] for i in range(20)]
    assert len(compute_best12(decks)) == 12


def extract_payload(html: str) -> dict:
    m = re.search(r'<script type="application/json" id="captain-data">(.*?)</script>', html, re.DOTALL)
    assert m, "captain-data payload not found"
    return json.loads(m.group(1))


def test_captain_page_embeds_payload_and_deck_rows(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    html = render_captain_page(caps["galileo-galilei"], "https://example.com/galaxy-stats")
    payload = extract_payload(html)
    assert payload["slug"] == "galileo-galilei"
    assert len(payload["months"]) == 2
    for username in ("adub", "bee", "cy"):
        assert f"<td>{username}</td>" in html
    assert '<link rel="canonical" href="https://example.com/galaxy-stats/captains/galileo-galilei/">' in html


def test_captain_page_escapes_closing_tag_sequences():
    captain = {
        "slug": "x",
        "name": "X",
        "months": [
            {
                "id": "2026-01",
                "date": "2026-01-16",
                "event": "E",
                "players": [{"username": "u", "archetype": "a", "deck": ["</script><b>"]}],
            }
        ],
    }
    html = render_captain_page(captain, "https://example.com")
    m = re.search(r'<script type="application/json" id="captain-data">(.*?)</script>', html, re.DOTALL)
    assert "</" not in m.group(1)
    assert extract_payload(html)["months"][0]["players"][0]["deck"] == ["</script><b>"]


def test_captain_page_empty_state(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    html = render_captain_page(caps["loki"], "https://example.com/galaxy-stats")
    assert "No winning decks recorded yet." in html
    extract_payload(html)


def test_captain_page_has_no_raw_json_section(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    for captain in (caps["galileo-galilei"], caps["loki"]):
        html = render_captain_page(captain, "https://example.com")
        assert "Raw JSON" not in html
        assert "<details" not in html


def test_pages_style_anchor_links_with_accent(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    for html in (
        render_index_page(caps, "https://example.com"),
        render_captain_page(caps["galileo-galilei"], "https://example.com"),
    ):
        assert "a { color:var(--accent)" in html


def test_index_links_every_captain(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    html = render_index_page(caps, "https://example.com/galaxy-stats")
    assert '<a href="galileo-galilei/">Galileo Galilei</a>' in html
    assert '<a href="loki/">Loki</a>' in html
    assert '<a href="mystery-captain/">mystery_captain</a>' in html
    assert '<link rel="canonical" href="https://example.com/galaxy-stats/captains/">' in html


@pytest.fixture()
def three_events_dir(tmp_path):
    """Three events so "last two months" is distinguishable from "all"."""
    decks = {
        "2026-01": [{"slug": "alpha", "players": [{"username": "u1", "archetype": "X", "deck": ["C"]}]}],
        "2026-02": [{"slug": "alpha", "players": [{"username": "u2", "archetype": "X", "deck": ["C"]}]}],
        "2026-03": [
            {"slug": "alpha", "players": [{"username": "u3", "archetype": "X", "deck": ["C"]}]},
            {"slug": "beta", "players": [{"username": "u4", "archetype": "X", "deck": ["C"]}]},
        ],
    }
    for event_id, captains in decks.items():
        event_dir = tmp_path / event_id
        event_dir.mkdir()
        (event_dir / "analysis.json").write_text(
            json.dumps({"event": {"id": event_id, "name": event_id, "date": event_id}, "captains": captains})
        )
    return tmp_path


def extract_index_payload(html: str) -> list[dict]:
    m = re.search(r'<script type="application/json" id="captains-data">(.*?)</script>', html, re.DOTALL)
    assert m, "captains-data payload not found"
    return json.loads(m.group(1))


def month_chip_state(html: str) -> tuple[set[str], set[str]]:
    """Return (all chip months, checked chip months) from an index page."""
    return (
        set(re.findall(r'data-month="([^"]+)"', html)),
        set(re.findall(r'checked data-month="([^"]+)"', html)),
    )


def test_index_embeds_compact_payload_with_monthly_deck_counts(three_events_dir, captains_file):
    caps = aggregate_captains(three_events_dir, captains_file)
    html = render_index_page(caps, "https://example.com")
    by_slug = {c["slug"]: c for c in extract_index_payload(html)}
    assert by_slug["alpha"]["months"] == [
        {"id": "2026-01", "decks": 1},
        {"id": "2026-02", "decks": 1},
        {"id": "2026-03", "decks": 1},
    ]
    assert by_slug["beta"]["months"] == [{"id": "2026-03", "decks": 1}]
    assert "username" not in html, "decklist/player data must not leak onto the index page"


def test_index_payload_includes_zero_deck_captains(three_events_dir, captains_file):
    caps = aggregate_captains(three_events_dir, captains_file)
    by_slug = {c["slug"]: c for c in extract_index_payload(render_index_page(caps, "https://example.com"))}
    assert by_slug["loki"]["months"] == []


def test_index_chips_default_to_last_two_months(three_events_dir, captains_file):
    caps = aggregate_captains(three_events_dir, captains_file)
    html = render_index_page(caps, "https://example.com")
    all_months, checked = month_chip_state(html)
    assert all_months == {"2026-01", "2026-02", "2026-03"}
    assert checked == {"2026-02", "2026-03"}


def test_index_table_is_js_rerenderable(three_events_dir, captains_file):
    caps = aggregate_captains(three_events_dir, captains_file)
    html = render_index_page(caps, "https://example.com")
    assert 'id="index-table"' in html
    assert f'<script src="../assets/captains.js?v={ASSET_VERSION}"></script>' in html


def test_pages_use_shared_captains_js(events_dir, captains_file):
    """JS lives in docs/assets/captains.js; only the JSON payload stays inline."""
    caps = aggregate_captains(events_dir, captains_file)
    index = render_index_page(caps, "https://example.com")
    page = render_captain_page(caps["galileo-galilei"], "https://example.com")
    empty = render_captain_page(caps["loki"], "https://example.com")
    assert f'<script src="../assets/captains.js?v={ASSET_VERSION}"></script>' in index
    assert f'<script src="../../assets/captains.js?v={ASSET_VERSION}"></script>' in page
    for html in (index, page):
        assert "function sortTable" not in html
        assert "function renderBest12" not in html
        assert "function renderIndex" not in html
    assert "captains.js" not in empty, "empty-state pages embed no JS"


def test_captain_page_chips_stay_all_checked(events_dir, captains_file):
    html = render_captain_page(aggregate_captains(events_dir, captains_file)["galileo-galilei"], "https://example.com")
    all_months, checked = month_chip_state(html)
    assert all_months == checked == {"2026-01", "2026-02"}


def test_captain_page_month_cells_link_to_reports(events_dir, captains_file):
    html = render_captain_page(aggregate_captains(events_dir, captains_file)["galileo-galilei"], "https://example.com")
    for month in ("2026-01", "2026-02"):
        assert f'<td data-v="{month}"><a href="../../reports/{month}/">{month}</a></td>' in html


def test_captain_page_month_cells_stay_plain_when_report_missing(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    html = render_captain_page(caps["galileo-galilei"], "https://example.com", report_ids={"2026-01"})
    assert '<td data-v="2026-01"><a href="../../reports/2026-01/">2026-01</a></td>' in html
    assert '<td data-v="2026-02">2026-02</td>' in html

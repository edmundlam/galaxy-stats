"""Tests for render_captains.py — captain page aggregation and rendering."""

import json
import re
from html import escape
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


def test_captain_page_with_image_uses_two_column_header(events_dir, captains_file):
    """Portrait pages wrap the header in .header-cols and point at the shared image."""
    caps = aggregate_captains(events_dir, captains_file)
    html = render_captain_page(caps["galileo-galilei"], "https://example.com", image="galileo-galilei__300.webp")
    assert '<div class="header-cols">' in html
    assert 'src="../../assets/captains-img/galileo-galilei__300.webp"' in html
    assert 'class="captain-portrait"' in html


def test_captain_page_without_image_keeps_flat_header(events_dir, captains_file):
    """No image → no portrait markup and no header-cols wrapper."""
    caps = aggregate_captains(events_dir, captains_file)
    html = render_captain_page(caps["galileo-galilei"], "https://example.com", image=None)
    assert '<img class="captain-portrait"' not in html
    assert '<div class="header-cols">' not in html
    assert "<h1>Galileo Galilei</h1>" in html


def test_captain_page_has_show_more_button(events_dir, captains_file):
    """Data pages ship the Best Cards show-more button; empty pages ship nothing."""
    caps = aggregate_captains(events_dir, captains_file)
    page = render_captain_page(caps["galileo-galilei"], "https://example.com")
    empty = render_captain_page(caps["loki"], "https://example.com")
    assert '<button type="button" id="best12-more" class="more-btn" hidden>Show 12 more</button>' in page
    assert "Best Cards" in page
    assert "best12-more" not in empty


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


@pytest.fixture()
def rules_file(tmp_path):
    p = tmp_path / "captain_rules.json"
    p.write_text(json.dumps({"galileo_galilei": "Stars align.\nTwice."}))
    return p


def test_aggregation_attaches_rules_text(events_dir, captains_file, rules_file):
    caps = aggregate_captains(events_dir, captains_file, rules_file=rules_file)
    assert caps["galileo-galilei"]["rules"] == "Stars align.\nTwice."
    assert "rules" not in caps["loki"]


def test_captain_page_renders_rules_line_in_header(events_dir, captains_file, rules_file):
    html = render_captain_page(
        aggregate_captains(events_dir, captains_file, rules_file=rules_file)["galileo-galilei"], "https://example.com"
    )
    assert 'class="rules-line"' in html
    assert "Stars align.<br>Twice." in html
    assert 'href="https://guide.galaxy.fun/cards/galileo_galilei/"' in html


def test_captain_page_without_rules_omits_line_and_guide_link(events_dir, captains_file, rules_file):
    html = render_captain_page(
        aggregate_captains(events_dir, captains_file, rules_file=rules_file)["loki"], "https://example.com"
    )
    assert 'class="rules-line"' not in html
    assert "guide.galaxy.fun" not in html


def test_captain_page_title_includes_game_name(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    html = render_captain_page(caps["galileo-galilei"], "https://example.com")
    assert "<title>Galileo Galilei Deck Stats &amp; Best Cards | Once Upon a Galaxy</title>" in html


def test_index_page_title_includes_game_name(events_dir, captains_file):
    html = render_index_page(aggregate_captains(events_dir, captains_file), "https://example.com")
    assert "<title>Captains Deck Stats | Once Upon a Galaxy</title>" in html


def test_captain_page_has_open_graph_and_twitter_tags(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    html = render_captain_page(caps["galileo-galilei"], "https://example.com", image="galileo_galilei__300.webp")
    assert '<meta property="og:type" content="website">' in html
    assert '<meta property="og:site_name" content="Galaxy Stats">' in html
    assert (
        '<meta property="og:title" content="Galileo Galilei Deck Stats &amp; Best Cards | Once Upon a Galaxy">' in html
    )
    assert '<meta property="og:url" content="https://example.com/captains/galileo-galilei/">' in html
    assert (
        '<meta property="og:image" content="https://example.com/assets/captains-img/galileo_galilei__300.webp">' in html
    )
    assert '<meta name="twitter:card" content="summary">' in html


def test_captain_page_og_description_matches_meta_description(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    html = render_captain_page(caps["galileo-galilei"], "https://example.com")
    m = re.search(r'<meta name="description" content="([^"]+)">', html)
    assert m
    assert f'<meta property="og:description" content="{m.group(1)}">' in html


def test_captain_page_without_image_omits_og_image(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    html = render_captain_page(caps["galileo-galilei"], "https://example.com", image=None)
    assert "og:image" not in html


def test_index_page_has_open_graph_tags(events_dir, captains_file):
    html = render_index_page(aggregate_captains(events_dir, captains_file), "https://example.com")
    assert '<meta property="og:type" content="website">' in html
    assert '<meta property="og:site_name" content="Galaxy Stats">' in html
    assert '<meta property="og:title" content="Captains Deck Stats | Once Upon a Galaxy">' in html
    assert '<meta property="og:url" content="https://example.com/captains/">' in html
    assert "og:image" not in html


def test_section_titles_are_h2(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    html = render_captain_page(caps["galileo-galilei"], "https://example.com")
    assert '<h2 class="section-title">Best Cards</h2>' in html
    assert "Decklists</h2>" in html
    assert '<div class="section-title">' not in html
    assert "h2.section-title" in html, "h2 default margins must be reset so the look is unchanged"


def test_header_links_use_canonical_directory_urls(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    page = render_captain_page(caps["galileo-galilei"], "https://example.com")
    index = render_index_page(caps, "https://example.com")
    assert '<a href="../../" class="event-label">' in page
    assert '<a href="../" class="event-label">' in index
    for html in (page, index):
        assert 'href="../index.html"' not in html
        assert 'href="../../index.html"' not in html


def test_portrait_reserves_layout_space(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    html = render_captain_page(caps["galileo-galilei"], "https://example.com", image="galileo_galilei__300.webp")
    assert "aspect-ratio:300/453" in html, "all portraits are 300x453; reserving the ratio avoids layout shift"


def test_deck_pills_link_to_card_guide_when_slug_known(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    html = render_captain_page(caps["galileo-galilei"], "https://example.com", card_slugs={"Card A": "card_a"})
    assert (
        '<a class="deck-pill" href="https://guide.galaxy.fun/cards/card_a/" target="_blank" rel="noopener">Card A</a>'
        in html
    )


def test_deck_pills_stay_plain_when_slug_unknown(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    html = render_captain_page(caps["galileo-galilei"], "https://example.com", card_slugs={"Card A": "card_a"})
    assert '<span class="deck-pill">Card B</span>' in html


def test_deck_pills_plain_without_slug_map(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    html = render_captain_page(caps["galileo-galilei"], "https://example.com")
    assert '<span class="deck-pill">Card A</span>' in html
    assert "guide.galaxy.fun" not in html


def test_captain_page_escapes_rules_text(events_dir, captains_file, tmp_path):
    rules = tmp_path / "captain_rules.json"
    rules.write_text(json.dumps({"galileo_galilei": "KO'd <strong>captains</strong>"}))
    html = render_captain_page(
        aggregate_captains(events_dir, captains_file, rules_file=rules)["galileo-galilei"], "https://example.com"
    )
    assert "<strong>" not in html.split("rules-line")[1].split("</div>")[0]
    assert "&lt;strong&gt;" in html


def best12_tbody(html: str) -> str:
    """Return the inner HTML of the Best Cards table tbody."""
    m = re.search(r'id="best12-table".*?<tbody>(.*?)</tbody>', html, re.DOTALL)
    assert m, "best12 tbody not found"
    return m.group(1)


def forty_deck_captain() -> dict:
    """One 40-deck month: 'Solo' in a single deck, 'Workhorse' in the other 39."""
    players = [{"username": "solo", "archetype": "a", "deck": ["Solo"]}]
    players += [{"username": f"u{i}", "archetype": "a", "deck": ["Workhorse"]} for i in range(39)]
    return {"slug": "x", "name": "X", "months": [{"id": "2026-01", "date": "d", "event": "E", "players": players}]}


def test_best12_pct_rounds_half_up_like_js():
    """JS uses Math.round (half-up); Python round() is banker's — 2.5% must render as 3."""
    by_card = {r["card"]: r for r in compute_best12([["A"]] + [["B"] for _ in range(39)])}
    assert by_card["A"]["pct"] == 3
    assert by_card["B"]["pct"] == 98


def test_captain_page_best12_pct_renders_half_up():
    html = render_captain_page(forty_deck_captain(), "https://example.com")
    rows = best12_tbody(html)
    assert '<td class="num">3%</td>' in rows, "1 of 40 decks = 2.5%: half-up says 3, banker's says 2"
    assert '<td class="num">98%</td>' in rows


def test_captain_page_prerenders_twelve_best12_rows():
    captain = {
        "slug": "x",
        "name": "X",
        "months": [
            {
                "id": "2026-01",
                "date": "d",
                "event": "E",
                "players": [{"username": f"u{i}", "archetype": "a", "deck": [f"Card {i}"]} for i in range(13)],
            }
        ],
    }
    assert best12_tbody(render_captain_page(captain, "https://example.com")).count("<tr>") == 12


def test_captain_page_best12_first_row_matches_compute_best12(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    captain = caps["galileo-galilei"]
    decks = [p["deck"] for m in captain["months"] for p in m["players"]]
    top = compute_best12(decks)[0]
    first = re.search(r"<tr>(.*?)</tr>", best12_tbody(render_captain_page(captain, "https://example.com")), re.DOTALL)
    assert first
    assert escape(top["card"]) in first.group(1)
    assert f'<td class="num">{top["freq"]}</td>' in first.group(1)
    assert f'<td class="num">{top["pct"]}%</td>' in first.group(1)


def test_captain_page_best12_count_shows_total_decks(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    html = render_captain_page(caps["galileo-galilei"], "https://example.com")
    assert '<span id="best12-count">3</span>' in html


def test_best12_card_cells_link_to_guide_when_slug_known(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    html = render_captain_page(caps["galileo-galilei"], "https://example.com", card_slugs={"Card A": "card_a"})
    rows = best12_tbody(html)
    assert (
        '<a class="deck-pill" href="https://guide.galaxy.fun/cards/card_a/" target="_blank" rel="noopener">Card A</a>'
        in rows
    )
    assert '<span class="deck-pill">Card B</span>' in rows


def test_best12_card_cells_plain_without_slug_map(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    rows = best12_tbody(render_captain_page(caps["galileo-galilei"], "https://example.com"))
    assert '<span class="deck-pill">Card A</span>' in rows
    assert "guide.galaxy.fun" not in rows


def test_captain_page_payload_card_slugs_cover_only_deck_cards(events_dir, captains_file):
    caps = aggregate_captains(events_dir, captains_file)
    html = render_captain_page(
        caps["galileo-galilei"],
        "https://example.com",
        card_slugs={"Card A": "card_a", "Card F": "card_f", "Unrelated": "unrelated"},
    )
    assert extract_payload(html)["cardSlugs"] == {"Card A": "card_a", "Card F": "card_f"}

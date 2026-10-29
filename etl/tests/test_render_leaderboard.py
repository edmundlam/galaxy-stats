"""Tests for render_leaderboard.py — cross-event player aggregation and page rendering."""

import json
import re
from pathlib import Path

import pytest

from scripts.generate_sitemap import generate_sitemap
from scripts.render_leaderboard import (
    build_event_list,
    compute_leaderboard,
    load_events,
    normalize_username,
    render_page,
    trim_embed,
)

REPO = Path(__file__).resolve().parents[2]


_SHORT = {
    "01": "Jan",
    "02": "Feb",
    "03": "Mar",
    "04": "Apr",
    "05": "May",
    "06": "Jun",
    "07": "Jul",
    "08": "Aug",
    "09": "Sep",
    "10": "Oct",
    "11": "Nov",
    "12": "Dec",
}


def raw_event(event_id: str, date: str, players: list[dict], total_champions: int | None = None) -> dict:
    """One event.json-shaped dict (players have username/captain/deck)."""
    event = {"id": event_id, "name": event_id, "date": date}
    if total_champions is not None:
        event["total_champions"] = total_champions
    return {"event": event, "players": players}


def make_event(event_id: str, date: str, players: list[dict]) -> dict:
    """One load_events-shaped event: fields flattened, short label and total derived."""
    event = raw_event(event_id, date, players)["event"]
    return {**event, "short": _SHORT[date[5:7]], "total": len(players), "players": players}


def player(username: str, captain: str) -> dict:
    return {"username": username, "captain": captain, "deck": ["Card A", "Card B", "Card C"]}


@pytest.fixture()
def events() -> list[dict]:
    """Four events; alice rides a 4-event streak, bob skips two, carol is loyal to cap_c."""
    return [
        make_event(
            "2026-01", "2026-01-17", [player("alice", "cap_a"), player("bob", "cap_a"), player("carol", "cap_c")]
        ),
        make_event(
            "2026-02", "2026-02-21", [player("Alice", "cap_b"), player("carol", "cap_c"), player("eve", "cap_a")]
        ),
        make_event(
            "2026-03",
            "2026-03-21",
            [player("alice", "cap_b"), player("carol", "cap_c"), player("dave", "cap_d"), player("eve", "cap_a")],
        ),
        make_event(
            "2026-04",
            "2026-04-18",
            [player("alice", "cap_c"), player("bob", "cap_a"), player("eve", "cap_b"), player("frank", "cap_e")],
        ),
    ]


@pytest.fixture()
def events_dir(tmp_path, events):
    """Same four events written as event.json files, directories out of order."""
    for event in reversed(events):
        raw = {
            "event": {k: v for k, v in event.items() if k not in ("short", "total", "players")},
            "players": event["players"],
        }
        event_dir = tmp_path / event["id"]
        event_dir.mkdir()
        (event_dir / "event.json").write_text(json.dumps(raw))
    return tmp_path


# --- Event list building ---


def test_load_events_orders_chronologically_and_labels_months(events_dir):
    board_events = load_events(events_dir)
    assert [(e["id"], e["short"]) for e in board_events] == [
        ("2026-01", "Jan"),
        ("2026-02", "Feb"),
        ("2026-03", "Mar"),
        ("2026-04", "Apr"),
    ]
    assert board_events[0]["date"] == "2026-01-17"


def test_event_totals_use_player_count_not_total_champions(tmp_path):
    """event.json's total_champions lies (2026-02 claims 183, holds 138); count players."""
    events_dir = tmp_path
    for event in (raw_event("2026-02", "2026-02-20", [player("a", "c")], total_champions=183),):
        (events_dir / event["event"]["id"]).mkdir()
        (events_dir / event["event"]["id"] / "event.json").write_text(json.dumps(event))
    assert [e["total"] for e in load_events(events_dir)] == [1]


def test_build_event_list_is_the_compact_source_of_truth(events):
    assert build_event_list(events) == [
        {"id": "2026-01", "short": "Jan", "total": 3},
        {"id": "2026-02", "short": "Feb", "total": 3},
        {"id": "2026-03", "short": "Mar", "total": 4},
        {"id": "2026-04", "short": "Apr", "total": 4},
    ]


# --- Username normalization + aliases ---


def test_normalize_username_trims_and_casefolds():
    assert normalize_username("  Bob ") == "bob"
    assert normalize_username("MIRABEL") == "mirabel"


def test_alias_map_maps_rename_to_canonical():
    aliases = {"old name": "New Name"}
    assert normalize_username("old name", aliases) == "new name"
    assert normalize_username("OLD NAME", aliases) == "new name"
    assert normalize_username("unrelated", aliases) == "unrelated"


def test_alias_map_unifies_player_across_events_with_canonical_display():
    two = [
        make_event("2026-01", "2026-01-17", [player("mirabel", "cap_a")]),
        make_event("2026-02", "2026-02-21", [player("Mira B", "cap_b")]),
    ]
    board = compute_leaderboard(two, aliases={"mira b": "Mirabel"})
    assert board["most_wins"] == [{"name": "Mirabel", "wins": 2}]
    assert board["stats"]["players"] == 1


# --- Header stats + most wins ---


def test_header_stats(events):
    board = compute_leaderboard(events)
    assert board["stats"] == {"players": 6, "events": 4, "longest_streak": 4, "repeat_pct": 67}


def test_most_wins_counts_events_per_normalized_player(events):
    board = compute_leaderboard(events)
    assert board["most_wins"][:3] == [
        {"name": "alice", "wins": 4},
        {"name": "carol", "wins": 3},
        {"name": "eve", "wins": 3},
    ]


def test_most_wins_ties_break_alphabetically(events):
    names = [r["name"] for r in compute_leaderboard(events)["most_wins"] if r["wins"] == 1]
    assert names == ["dave", "frank"]


# --- Streaks ---


def test_longest_streaks_ordered_by_length_then_name(events):
    board = compute_leaderboard(events)
    top = board["longest_streaks"][:3]
    assert [(r["name"], r["length"]) for r in top] == [("alice", 4), ("carol", 3), ("eve", 3)]
    assert top[0]["start"] == 0 and top[0]["end"] == 3


def test_longest_streaks_same_player_ties_break_by_start(events):
    """bob wins Jan and Apr: two length-1 runs, ordered by start index after the name."""
    runs = [(r["name"], r["start"]) for r in compute_leaderboard(events)["longest_streaks"] if r["name"] == "bob"]
    assert runs == [("bob", 0), ("bob", 3)]


def test_active_streaks_end_at_latest_event_with_min_two(events):
    board = compute_leaderboard(events)
    assert [(r["name"], r["length"]) for r in board["active_streaks"]] == [("alice", 4), ("eve", 3)]


def test_active_streak_history_is_actual_not_last_n_filled(events):
    """bob won Jan and Apr, so his grid must show the real gaps, not a trailing fill."""
    board = compute_leaderboard(events)
    bob = next(r for r in board["most_wins"] if r["name"] == "bob")
    assert bob["wins"] == 2
    # bob's runs are both length 1, so he is absent from active streaks; check via a dedicated run scan
    runs = [(r["name"], r["length"]) for r in board["longest_streaks"]]
    assert ("bob", 1) in runs and ("bob", 2) not in runs


def test_active_streak_cap_split_between_artifact_and_page():
    """Artifact keeps all (≤100); the page embed stops at 20."""
    events = [
        make_event("2026-01", "2026-01-17", [player(f"p{i:02d}", "c") for i in range(25)]),
        make_event("2026-02", "2026-02-21", [player(f"p{i:02d}", "c") for i in range(25)]),
    ]
    board = compute_leaderboard(events)
    assert len(board["active_streaks"]) == 25
    assert len(trim_embed(board)["active_streaks"]) == 20


# --- Records ---


def test_records_most_captains_piloted(events):
    board = compute_leaderboard(events)
    assert board["records"]["captains"][:2] == [{"name": "alice", "captains": 3}, {"name": "eve", "captains": 2}]


def test_records_most_loyal_requires_three_finishes(events):
    board = compute_leaderboard(events, captain_names={"cap_c": "The Candyman"})
    assert board["records"]["loyal"] == [{"name": "carol", "wins": 3, "captain": "The Candyman", "slug": "cap_c"}]


def test_records_most_loyal_falls_back_to_slug_without_names(events):
    board = compute_leaderboard(events)
    assert board["records"]["loyal"][0]["captain"] == "cap_c"
    assert board["records"]["loyal"][0]["slug"] == "cap_c"


def test_records_longest_comeback_counts_missed_events(events):
    """bob finished Jan and Apr: two events missed in between."""
    board = compute_leaderboard(events)
    assert board["records"]["comeback"] == [{"name": "bob", "gap": 2}]


# --- Cutoffs and embed trimming ---


def hundred_player_events(count: int = 120) -> list[dict]:
    return [
        make_event("2026-01", "2026-01-17", [player(f"p{i:03d}", "c") for i in range(count)]),
        make_event("2026-02", "2026-02-21", [player(f"q{i:03d}", "c") for i in range(count)]),
    ]


def test_artifact_keeps_generous_top_100_per_list():
    board = compute_leaderboard(hundred_player_events())
    assert len(board["most_wins"]) == 100
    assert len(board["longest_streaks"]) == 100


def test_embed_trims_to_what_the_page_displays(events):
    embed = trim_embed(compute_leaderboard(events))
    assert len(embed["most_wins"]) <= 10
    assert len(embed["longest_streaks"]) <= 10
    assert len(embed["active_streaks"]) <= 20
    assert len(embed["records"]["captains"]) <= 3
    for row in embed["active_streaks"]:
        assert len(row["wins"]) == len(embed["events"])


def test_embed_streak_rows_carry_month_ranges(events):
    embed = trim_embed(compute_leaderboard(events))
    assert embed["longest_streaks"][0] == {"name": "alice", "length": 4, "from": "Jan", "to": "Apr"}


def test_embed_histories_window_to_last_twelve_events():
    events = [make_event(f"2026-{m:02d}", f"2026-{m:02d}-20", [player("alice", "c")]) for m in range(1, 13)]
    embed = trim_embed(compute_leaderboard(events))
    assert len(embed["events"]) == 12
    assert embed["events"][0]["short"] == "Jan"
    assert [r["name"] for r in embed["active_streaks"]] == ["alice"]
    assert len(embed["active_streaks"][0]["wins"]) == 12


# --- Page rendering ---


@pytest.fixture()
def page(events) -> str:
    return render_page(
        trim_embed(compute_leaderboard(events, captain_names={"cap_c": "The Candyman"})), "https://example.com"
    )


def extract_payload(html: str) -> dict:
    m = re.search(r'<script type="application/json" id="leaderboard-data">(.*?)</script>', html, re.DOTALL)
    assert m, "leaderboard-data payload not found"
    return json.loads(m.group(1))


def test_page_renders_four_cards(page):
    for title in ("Most wins", "Longest streaks", "Active streaks", "Records"):
        assert f"<h2>{title}</h2>" in page


def test_page_header_stats_row(page):
    assert '<div class="stat-value">6</div><div class="stat-label">Players tracked</div>' in page
    assert '<div class="stat-value">4</div><div class="stat-label">Events</div>' in page
    assert '<div class="stat-value">4</div><div class="stat-label">Longest streak</div>' in page
    assert '<div class="stat-value">67%</div><div class="stat-label">Win again</div>' in page


def test_page_notes_name_matching(page):
    assert "matched case-insensitively" in page.split('class="note"', 1)[1]


def test_page_most_wins_bar_shares_of_total(page):
    assert '<div class="bar-name" title="alice">alice</div>' in page
    assert '<div class="bar-pct">4 / 4</div>' in page
    assert 'style="width:100.0%"' in page


def test_page_streak_bars_carry_date_range_overlay(page):
    assert '<span class="bar-sub">Jan–Apr</span>' in page
    assert '<div class="bar-pct">4</div>' in page


def test_page_win_history_grid_renders_actual_wins(page):
    """alice's 4-event streak renders 4 gold cells; the header row shows month labels."""
    row = page.split('class="hist-row"', 1)[1].split("</div>", 1)[0]
    assert '<i class="w"></i>' in row
    assert "<span>Jan</span>" in page.split('class="hist-head"', 1)[1]
    assert row.count("<i") == 4


def test_page_records_podium_rows(page):
    assert "3 captains" in page, "alice piloted cap_a, cap_b and cap_c"
    assert "3 wins with " in page and '<a href="../captains/cap-c/">The Candyman</a>' in page, (
        "carol won three events on one captain"
    )
    assert "back after 2 events" in page, "bob came back two events later"


def test_page_loyal_captain_links_to_detail_page(page):
    """extra_notes #4: captain names link to the captain detail page (dashed slug)."""
    assert '<a href="../captains/cap-c/">The Candyman</a>' in page


def test_page_embeds_trimmed_payload(page):
    payload = extract_payload(page)
    assert len(payload["most_wins"]) == 6
    assert payload["stats"]["players"] == 6
    assert set(payload) == {"events", "stats", "most_wins", "longest_streaks", "active_streaks", "records"}


def test_page_escapes_closing_tag_sequences(events):
    tricky = [make_event("2026-01", "2026-01-17", [player("</script><b>", "cap_a")])]
    html = render_page(trim_embed(compute_leaderboard(tricky)), "https://example.com")
    assert "</script><b>" not in html.split('id="leaderboard-data">', 1)[1].split("</script>", 1)[0]
    assert "&lt;/script&gt;&lt;b&gt;" in html


def test_page_meta_canonical_and_shared_assets(page):
    assert '<link rel="canonical" href="https://example.com/leaderboard/">' in page
    assert '<link rel="stylesheet" href="../assets/galaxy-report.css?v=' in page


def test_page_nav_links_existing_pages_only(page):
    assert '<a href="../captains/"' in page
    assert '<a href="../about.html"' in page
    assert "decklists" not in page.lower(), "the decklists page does not exist yet"


def test_page_leaderboard_link_is_active_in_nav(page):
    assert '<a href="./" class="active"' in page


# --- Site wiring ---


def test_sitemap_includes_leaderboard_page(tmp_path):
    docs = tmp_path / "docs"
    (docs / "leaderboard").mkdir(parents=True)
    (docs / "leaderboard" / "index.html").write_text("<html></html>")
    xml = generate_sitemap(docs, "https://example.com")
    assert "<loc>https://example.com/leaderboard/</loc>" in xml


def test_generated_page_exists_with_four_cards():
    """The committed page must exist and carry all four cards once generated."""
    page = REPO / "docs" / "leaderboard" / "index.html"
    assert page.exists(), "run `make leaderboard` from the repo root"
    html = page.read_text(encoding="utf-8")
    for title in ("Most wins", "Longest streaks", "Active streaks", "Records"):
        assert f"<h2>{title}</h2>" in html

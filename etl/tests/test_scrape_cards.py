"""Tests for scrape_cards.py — extracting card cids from the guide cards list page."""

from scripts.scrape_cards import extract_cards, merge_cards

SAMPLE_HTML = """
<li class="card-item" data-searchable="antiquitoy when you buff slots toy">
  <db-card
    data-card-name="Antiquitoy"
    data-card-type="character"
    data-card-key="antiquitoy"
    data-card-set="4"
    data-card-cid="4036"
    data-view="list">
    <a href="/cards/antiquitoy/">Antiquitoy</a>
  </db-card>
</li>
<li class="card-item" data-searchable="barbosa pirate villain">
  <db-card
    data-card-name="Barbosa"
    data-card-type="character"
    data-card-key="barbosa"
    data-card-cid="2156"
    data-view="list">
    <a href="/cards/barbosa/">Barbosa</a>
  </db-card>
</li>
<li class="card-item" data-searchable="mystery card without cid">
  <db-card
    data-card-name="Mystery"
    data-card-key="mystery"
    data-view="list">
    <a href="/cards/mystery/">Mystery</a>
  </db-card>
</li>
"""


def test_extract_cards_names_and_cids():
    cards = extract_cards(SAMPLE_HTML)
    assert cards == {
        "antiquitoy": {"name": "Antiquitoy", "cid": 4036},
        "barbosa": {"name": "Barbosa", "cid": 2156},
    }


def test_merge_cards_scraped_wins_and_normalizes_legacy_strings():
    existing = {"antiquitoy": "Antiquitoy", "legacy_card": "Legacy Card"}
    merged = merge_cards(existing, {"antiquitoy": {"name": "Antiquitoy", "cid": 4036}})
    assert merged == {
        "antiquitoy": {"name": "Antiquitoy", "cid": 4036},
        "legacy_card": {"name": "Legacy Card"},
    }


def test_merge_cards_round_trips_json(tmp_path):
    import json

    path = tmp_path / "cards.json"
    path.write_text(json.dumps({"antiquitoy": "Antiquitoy"}))
    existing = json.loads(path.read_text(encoding="utf-8"))
    merged = merge_cards(existing, {"antiquitoy": {"name": "Antiquitoy", "cid": 4036}})
    path.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    assert json.loads(path.read_text(encoding="utf-8")) == {"antiquitoy": {"name": "Antiquitoy", "cid": 4036}}

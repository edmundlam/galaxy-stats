"""Tests for scrape_captain_rules.py — extracting rules text from the guide cards list page."""

import json

from scripts.scrape_captain_rules import extract_rules, merge_rules

SAMPLE_HTML = """
<li class="card-item" data-searchable="baldr you start with 4 hearts captain">
  <db-card
    data-card-name="Baldr"
    data-card-type="captain"
    data-card-text="You start with 4 Hearts."
    data-card-key="baldr"
    data-view="list">
    <a href="/cards/baldr/">Baldr</a>
  </db-card>
</li>
<li class="card-item" data-searchable="ammit hunts captain">
  <db-card
    data-card-name="Ammit"
    data-card-type="character"
    data-card-text="Should be ignored."
    data-card-key="ammit"
    data-view="list">
    <a href="/cards/ammit/">Ammit</a>
  </db-card>
</li>
<li class="card-item" data-searchable="anagolay treasure captain">
  <db-card
    data-card-name="Anagolay"
    data-card-type="captain"
    data-card-text="When you discover a treasure, I lose one or two of them but get to keep the rest."
    data-card-key="anagolay"
    data-view="list">
    <a href="/cards/anagolay/">Anagolay</a>
  </db-card>
</li>
"""


def test_extract_rules_captains_only():
    rules = extract_rules(SAMPLE_HTML)
    assert rules == {
        "baldr": "You start with 4 Hearts.",
        "anagolay": "When you discover a treasure, I lose one or two of them but get to keep the rest.",
    }


def test_extract_rules_unescapes_entities():
    rules = extract_rules(
        '<db-card data-card-type="captain" data-card-text="When one is KO&apos;d..." data-card-key="athena">'
    )
    assert rules == {"athena": "When one is KO'd..."}


def test_merge_rules_never_overwrites():
    existing = {"baldr": "Old text."}
    merged = merge_rules(existing, {"baldr": "New text.", "ammit": "Fresh."})
    assert merged == {"baldr": "Old text.", "ammit": "Fresh."}


def test_merge_rules_round_trips_json(tmp_path):
    path = tmp_path / "captain_rules.json"
    path.write_text(json.dumps({"baldr": "You start with 4 Hearts."}))
    existing = json.loads(path.read_text(encoding="utf-8"))
    merged = merge_rules(existing, {"baldr": "You start with 4 Hearts.", "ammit": "Hunts."})
    path.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    assert json.loads(path.read_text(encoding="utf-8")) == {"baldr": "You start with 4 Hearts.", "ammit": "Hunts."}

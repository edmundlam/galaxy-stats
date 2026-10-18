"""Tests for analyze_event.py best12 pct rounding."""

from scripts.analyze_event import _pct


def test_pct_rounds_half_up():
    """Half-up at .5 boundaries matches render_captains._pct / captains.js Math.round.

    Python's round() is banker's rounding and would give 2 for _pct(1, 40).
    """
    assert _pct(1, 40) == 3  # 2.5 -> 3
    assert _pct(3, 8) == 38  # 37.5 -> 38
    assert _pct(1, 200) == 1  # 0.5 -> 1
    assert _pct(0, 40) == 0
    assert _pct(40, 40) == 100

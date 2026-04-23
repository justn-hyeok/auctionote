from datetime import date

import pytest

from crawler.live import default_targets, sliding_date_windows


def test_sliding_date_windows_keeps_each_window_within_limit() -> None:
    start = date(2026, 4, 24)

    windows = sliding_date_windows(start, 30)

    assert windows == [
        (date(2026, 4, 24), date(2026, 5, 8)),
        (date(2026, 5, 9), date(2026, 5, 23)),
        (date(2026, 5, 24), date(2026, 5, 24)),
    ]
    assert all((end - begin).days <= 14 for begin, end in windows)


def test_sliding_date_windows_handles_single_day_horizon() -> None:
    start = date(2026, 4, 24)

    assert sliding_date_windows(start, 0) == [(start, start)]


def test_sliding_date_windows_rejects_invalid_bounds() -> None:
    with pytest.raises(ValueError, match="total_days"):
        sliding_date_windows(date(2026, 4, 24), -1)

    with pytest.raises(ValueError, match="max_window_days"):
        sliding_date_windows(date(2026, 4, 24), 14, max_window_days=0)


def test_default_targets_cover_seoul_courts_and_requested_property_types() -> None:
    targets = default_targets()
    courts = {target.court for target in targets}
    expected_properties = {
        ("건물", "주거용건물", "아파트"),
        ("건물", "주거용건물", "다세대주택"),
        ("건물", "주거용건물", "오피스텔"),
        ("건물", "상업용및업무용건물", "근린생활시설"),
        ("토지", "", ""),
    }

    assert len(courts) == 5
    assert len(targets) == 25
    for court in courts:
        assert {
            (target.lcl, target.mcl, target.scl)
            for target in targets
            if target.court == court
        } == expected_properties

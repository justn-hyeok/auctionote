from datetime import date

import pytest

from analysis.market import (
    HEURISTIC_NOTICE,
    confidence_for_sample_size,
    estimate_market_prices_per_m2,
    market_signals,
)
from analysis.schema import AuctionItem


def make(
    case_no: str,
    minbid: int,
    area: float | None,
    address: str = "서울특별시 강남구 역삼동 1",
    use_type: str = "아파트",
) -> AuctionItem:
    return AuctionItem(
        case_no=case_no,
        item_no=1,
        court="서울중앙지방법원",
        auction_date=date(2026, 5, 1),
        appraisal_price=1_000_000_000,
        min_bid_price=minbid,
        failed_count=0,
        address=address,
        use_type=use_type,
        area_m2=area,
        status="유찰",
        source_url="https://example.test",
    )


def test_estimate_market_prices_per_m2_groups_by_region_and_use_type():
    items = [
        make("A", minbid=1_000, area=10),
        make("B", minbid=3_000, area=10),
        make("C", minbid=2_000, area=10),
        make("D", minbid=9_000, area=30, use_type="토지"),
        make("E", minbid=6_000, area=20, address="서울특별시 서초구 반포동 1"),
        make("ignored", minbid=6_000, area=None),
    ]

    estimates = estimate_market_prices_per_m2(items)

    apt = estimates[("서울특별시 강남구", "아파트")]
    assert apt.estimated_price_per_m2 == pytest.approx(200.0)
    assert apt.sample_size == 3
    assert apt.confidence == "medium"

    land = estimates[("서울특별시 강남구", "토지")]
    assert land.estimated_price_per_m2 == pytest.approx(300.0)
    assert land.sample_size == 1
    assert land.confidence == "low"


def test_market_signals_compute_value_gap_from_heuristic_estimate():
    items = [
        make("cheap", minbid=1_000, area=10),
        make("middle", minbid=2_000, area=10),
        make("expensive", minbid=3_000, area=10),
    ]

    signals = {signal.item.case_no: signal for signal in market_signals(items)}

    cheap = signals["cheap"]
    assert cheap.estimated_market_price_per_m2 == pytest.approx(200.0)
    assert cheap.estimated_market_value == pytest.approx(2_000.0)
    assert cheap.value_gap_rate == pytest.approx(0.5)
    assert cheap.confidence == "medium"
    assert "Heuristic only" in cheap.heuristic_notice
    assert "not real appraisal" in HEURISTIC_NOTICE


def test_market_signals_leave_unknown_values_when_item_data_is_not_usable():
    items = [
        make("peer", minbid=2_000, area=10),
        make("missing-area", minbid=1_000, area=None),
        make("missing-minbid", minbid=0, area=10),
    ]

    signals = {signal.item.case_no: signal for signal in market_signals(items)}

    missing_area = signals["missing-area"]
    assert missing_area.estimated_market_price_per_m2 == pytest.approx(200.0)
    assert missing_area.estimated_market_value is None
    assert missing_area.value_gap_rate is None

    missing_minbid = signals["missing-minbid"]
    assert missing_minbid.estimated_market_price_per_m2 == pytest.approx(200.0)
    assert missing_minbid.estimated_market_value == pytest.approx(2_000.0)
    assert missing_minbid.value_gap_rate is None


def test_confidence_label_is_based_on_sample_size():
    assert confidence_for_sample_size(0) == "low"
    assert confidence_for_sample_size(2) == "low"
    assert confidence_for_sample_size(3) == "medium"
    assert confidence_for_sample_size(5) == "high"

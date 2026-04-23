from datetime import date

import pytest

from analysis.insights import (
    discount_rate,
    min_bid_price_per_m2,
    quality_flags,
    quality_summary,
    region_key,
    screen_items,
)
from analysis.schema import AuctionItem


def make(
    case_no: str = "2024타경00001",
    failed: int = 0,
    appraisal: int = 1_000_000_000,
    minbid: int = 800_000_000,
    area: float | None = 84.0,
    address: str = "서울특별시 강남구 역삼동 1",
    status: str = "유찰",
) -> AuctionItem:
    return AuctionItem(
        case_no=case_no,
        item_no=1,
        court="서울중앙지방법원",
        auction_date=date(2026, 5, 1),
        appraisal_price=appraisal,
        min_bid_price=minbid,
        failed_count=failed,
        address=address,
        use_type="아파트",
        area_m2=area,
        status=status,
        source_url="https://example.test",
    )


def test_price_helpers():
    item = make(appraisal=1_000, minbid=700, area=10)

    assert discount_rate(item) == pytest.approx(0.3)
    assert min_bid_price_per_m2(item) == pytest.approx(70.0)
    assert region_key(item.address) == "서울특별시 강남구"


def test_quality_flags_catches_inconsistent_discount():
    item = make(failed=3, appraisal=1_000, minbid=1_000, area=None)

    assert quality_flags(item) == ("면적 누락", "유찰 대비 할인율 낮음")


def test_screen_items_ranks_discounted_relative_value_higher():
    cheap = make("A", failed=2, minbid=600, area=100)
    expensive = make("B", failed=0, minbid=1_000, area=50)

    ranked = screen_items([expensive, cheap], today=date(2026, 4, 28))

    assert ranked[0].item.case_no == "A"
    assert ranked[0].screening_score > ranked[1].screening_score
    assert ranked[0].region_price_per_m2_ratio is not None


def test_quality_summary_counts_flags():
    items = [
        make("A", failed=8),
        make("B", failed=1, appraisal=1_000, minbid=1_000, area=None),
    ]

    summary = {row["flag"]: row["count"] for row in quality_summary(items)}

    assert summary["장기 유찰"] == 1
    assert summary["면적 누락"] == 1
    assert summary["유찰 대비 할인율 낮음"] == 1

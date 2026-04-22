from datetime import date

import pytest

pytest.importorskip("analysis.schema", reason="Phase B not complete: analysis.schema missing")
pytest.importorskip("analysis.stats", reason="Phase B not complete: analysis.stats missing")

from analysis.schema import AuctionItem  # noqa: E402
from analysis.stats import (  # noqa: E402
    by_region,
    by_use_type,
    failed_count_discount_stats,
)


def make(
    failed: int = 0,
    appraisal: int = 1_000_000_000,
    minbid: int = 1_000_000_000,
    address: str = "서울특별시 강남구 역삼동 1",
    use_type: str = "아파트",
) -> AuctionItem:
    return AuctionItem(
        case_no=f"2024타경{failed:05d}",
        item_no=1,
        court="서울중앙지방법원",
        auction_date=date(2026, 5, 1),
        appraisal_price=appraisal,
        min_bid_price=minbid,
        failed_count=failed,
        address=address,
        use_type=use_type,
        area_m2=None,
        status="유찰",
        source_url="",
    )


def test_discount_stats_groups_by_failed_count():
    items = [
        make(0, 1000, 1000),
        make(1, 1000, 800),
        make(1, 1000, 700),
        make(2, 1000, 500),
    ]
    stats = {s["failed_count"]: s for s in failed_count_discount_stats(items)}

    assert stats[0]["count"] == 1
    assert stats[0]["mean_discount"] == pytest.approx(0.0)

    assert stats[1]["count"] == 2
    assert stats[1]["mean_discount"] == pytest.approx(0.25)

    assert stats[2]["count"] == 1
    assert stats[2]["mean_discount"] == pytest.approx(0.5)


def test_discount_stats_empty():
    assert failed_count_discount_stats([]) == []


def test_by_region_groups_first_two_tokens():
    items = [
        make(address="서울특별시 강남구 역삼동 1"),
        make(address="서울특별시 강남구 삼성동 2"),
        make(address="서울특별시 서초구 반포동 3"),
    ]
    regions = {r["region"]: r for r in by_region(items)}
    assert regions["서울특별시 강남구"]["count"] == 2
    assert regions["서울특별시 서초구"]["count"] == 1


def test_by_use_type():
    items = [make(use_type="아파트"), make(use_type="아파트"), make(use_type="토지")]
    d = {r["use_type"]: r["count"] for r in by_use_type(items)}
    assert d == {"아파트": 2, "토지": 1}

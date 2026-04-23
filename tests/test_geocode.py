from datetime import date

import pytest

from analysis.geocode import (
    GeoPoint,
    geocode_address,
    geocode_item,
    parse_seoul_district,
)
from analysis.schema import AuctionItem


def make_item(address: str) -> AuctionItem:
    return AuctionItem(
        case_no="2024타경00001",
        item_no=1,
        court="서울중앙지방법원",
        auction_date=date(2026, 5, 1),
        appraisal_price=1_000_000_000,
        min_bid_price=800_000_000,
        failed_count=1,
        address=address,
        use_type="아파트",
        area_m2=84.0,
        status="유찰",
        source_url="https://example.test",
    )


def test_parse_seoul_district_from_standard_address():
    assert parse_seoul_district("서울특별시 강남구 역삼동 1") == "강남구"
    assert parse_seoul_district("서울 서초구 반포동 20") == "서초구"


def test_parse_seoul_district_from_leading_district_address():
    assert parse_seoul_district("송파구 잠실동 40-1") == "송파구"


def test_parse_seoul_district_rejects_non_seoul_region_marker():
    assert parse_seoul_district("부산광역시 강서구 명지동 1") is None
    assert geocode_address("경기도 광주시 중부면 산1") is None


def test_geocode_address_returns_centroid_metadata():
    point = geocode_address("서울특별시 마포구 공덕동 100")

    assert point == GeoPoint(
        district="마포구",
        latitude=pytest.approx(37.5663),
        longitude=pytest.approx(126.9019),
        confidence=pytest.approx(0.68),
        source="offline:seoul-district-centroid:v1",
    )


def test_geocode_item_uses_auction_item_address():
    item = make_item("서울특별시 용산구 한남동 1")

    point = geocode_item(item)

    assert point is not None
    assert point.district == "용산구"
    assert point.latitude == pytest.approx(37.5326)
    assert point.longitude == pytest.approx(126.9900)


def test_geocode_address_returns_none_for_unknown_or_empty_address():
    assert geocode_address("") is None
    assert geocode_address("제주특별자치도 제주시 이도동 1") is None

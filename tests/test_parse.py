from datetime import date

import pytest

pytest.importorskip("crawler.parse", reason="Phase B not complete: crawler.parse missing")

from tests.conftest import (  # noqa: E402
    list_detail_cases,
    list_list_cases,
    load_expected,
    load_raw,
)

DETAIL_CASES = list_detail_cases()
LIST_CASES = list_list_cases()


@pytest.mark.skipif(not DETAIL_CASES, reason="Phase A not complete: no detail fixtures")
@pytest.mark.parametrize("name", DETAIL_CASES)
def test_parse_detail(name):
    from crawler.parse import parse_detail

    html = load_raw(name)
    expected = load_expected(name)

    item = parse_detail(html)

    assert item.case_no == expected["case_no"]
    assert item.item_no == expected["item_no"]
    assert item.court == expected["court"]
    assert item.auction_date == date.fromisoformat(expected["auction_date"])
    assert item.appraisal_price == expected["appraisal_price"]
    assert item.min_bid_price == expected["min_bid_price"]
    assert item.failed_count == expected["failed_count"]
    assert item.use_type == expected["use_type"]
    assert item.status == expected["status"]
    assert item.address == expected["address"]
    if expected.get("area_m2") is not None:
        assert item.area_m2 == pytest.approx(expected["area_m2"], rel=1e-3)
    else:
        assert item.area_m2 is None


@pytest.mark.skipif(not LIST_CASES, reason="Phase A not complete: no list fixtures")
@pytest.mark.parametrize("name", LIST_CASES)
def test_parse_list(name):
    from crawler.parse import parse_list

    html = load_raw(name)
    expected = load_expected(name)

    items = parse_list(html)

    assert len(items) == len(expected["items"])
    for got, exp in zip(items, expected["items"], strict=True):
        assert got["case_no"] == exp["case_no"]
        assert got["detail_url"] == exp["detail_url"]

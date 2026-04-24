from datetime import date

from analysis.schema import AuctionItem
from storage.postgres import _from_row, _to_row_dict, AuctionItemRow


def _item() -> AuctionItem:
    return AuctionItem(
        case_no="2024타경00001",
        item_no=1,
        court="서울중앙지방법원",
        auction_date=date(2026, 5, 1),
        appraisal_price=1_000_000_000,
        min_bid_price=800_000_000,
        failed_count=2,
        address="서울특별시 강남구 역삼동",
        use_type="아파트",
        area_m2=84.93,
        status="유찰",
        source_url="https://example.test/item",
    )


def test_postgres_row_roundtrip():
    item = _item()

    row = AuctionItemRow(**_to_row_dict(item))
    loaded = _from_row(row)

    assert loaded == item

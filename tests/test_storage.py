from datetime import date

import pytest

pytest.importorskip("analysis.schema", reason="Phase B not complete: analysis.schema missing")
pytest.importorskip("storage.sqlite", reason="Phase B not complete: storage.sqlite missing")

from analysis.schema import AuctionItem  # noqa: E402
from storage.sqlite import init_db, load_all, load_by_filter, save  # noqa: E402


def _item(case_no: str, failed: int = 0, use_type: str = "아파트", court: str = "서울중앙지방법원") -> AuctionItem:
    return AuctionItem(
        case_no=case_no, item_no=1, court=court,
        auction_date=date(2026, 5, 1),
        appraisal_price=1_000_000_000, min_bid_price=800_000_000,
        failed_count=failed, address="서울특별시 강남구 역삼동",
        use_type=use_type, area_m2=84.93, status="유찰", source_url="",
    )


def test_save_and_load_roundtrip(tmp_path):
    db = tmp_path / "t.db"
    init_db(db)
    items = [_item("2024타경00001"), _item("2024타경00002", failed=2)]
    save(items, db)
    loaded = load_all(db)
    assert {i.case_no for i in loaded} == {"2024타경00001", "2024타경00002"}


def test_save_is_upsert(tmp_path):
    db = tmp_path / "t.db"
    init_db(db)
    save([_item("X", failed=0)], db)
    save([_item("X", failed=2)], db)
    loaded = load_all(db)
    assert len(loaded) == 1
    assert loaded[0].failed_count == 2


def test_load_by_filter(tmp_path):
    db = tmp_path / "t.db"
    init_db(db)
    save([
        _item("A", use_type="아파트", failed=0),
        _item("B", use_type="아파트", failed=2),
        _item("C", use_type="토지", failed=1),
    ], db)
    assert {i.case_no for i in load_by_filter(db, use_type="아파트")} == {"A", "B"}
    assert {i.case_no for i in load_by_filter(db, min_failed=1)} == {"B", "C"}

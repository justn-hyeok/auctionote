"""SQLite persistence for AuctionItem."""
from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

from analysis.schema import AuctionItem

_SCHEMA = """
CREATE TABLE IF NOT EXISTS auction_items (
    case_no TEXT NOT NULL,
    item_no INTEGER NOT NULL,
    court TEXT NOT NULL,
    auction_date TEXT NOT NULL,
    appraisal_price INTEGER NOT NULL,
    min_bid_price INTEGER NOT NULL,
    failed_count INTEGER NOT NULL,
    address TEXT NOT NULL,
    use_type TEXT NOT NULL,
    area_m2 REAL,
    status TEXT NOT NULL,
    source_url TEXT NOT NULL,
    PRIMARY KEY (case_no, item_no)
)
"""


def init_db(path: str | Path) -> None:
    with sqlite3.connect(str(path)) as conn:
        conn.execute(_SCHEMA)


def _to_row(item: AuctionItem) -> tuple[Any, ...]:
    return (
        item.case_no,
        item.item_no,
        item.court,
        item.auction_date.isoformat(),
        item.appraisal_price,
        item.min_bid_price,
        item.failed_count,
        item.address,
        item.use_type,
        item.area_m2,
        item.status,
        item.source_url,
    )


def _from_row(row: sqlite3.Row) -> AuctionItem:
    return AuctionItem(
        case_no=row["case_no"],
        item_no=row["item_no"],
        court=row["court"],
        auction_date=date.fromisoformat(row["auction_date"]),
        appraisal_price=row["appraisal_price"],
        min_bid_price=row["min_bid_price"],
        failed_count=row["failed_count"],
        address=row["address"],
        use_type=row["use_type"],
        area_m2=row["area_m2"],
        status=row["status"],
        source_url=row["source_url"],
    )


_INSERT_SQL = """
INSERT OR REPLACE INTO auction_items
(case_no, item_no, court, auction_date, appraisal_price,
 min_bid_price, failed_count, address, use_type, area_m2,
 status, source_url)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def save(items: list[AuctionItem], path: str | Path) -> None:
    if not items:
        return
    with sqlite3.connect(str(path)) as conn:
        conn.executemany(_INSERT_SQL, [_to_row(it) for it in items])


def load_all(path: str | Path) -> list[AuctionItem]:
    with sqlite3.connect(str(path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM auction_items ORDER BY case_no, item_no"
        ).fetchall()
    return [_from_row(r) for r in rows]


def load_by_filter(
    path: str | Path,
    *,
    use_type: str | None = None,
    min_failed: int | None = None,
    court: str | None = None,
) -> list[AuctionItem]:
    clauses: list[str] = []
    params: list[Any] = []
    if use_type is not None:
        clauses.append("use_type = ?")
        params.append(use_type)
    if min_failed is not None:
        clauses.append("failed_count >= ?")
        params.append(min_failed)
    if court is not None:
        clauses.append("court = ?")
        params.append(court)
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    with sqlite3.connect(str(path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"SELECT * FROM auction_items{where} ORDER BY case_no, item_no",
            params,
        ).fetchall()
    return [_from_row(r) for r in rows]

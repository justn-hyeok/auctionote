"""PostgreSQL persistence for AuctionItem using SQLAlchemy ORM."""
from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import Date, Float, Integer, String, create_engine, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from analysis.schema import AuctionItem

DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://auctionote:auctionote@localhost:5432/auctionote"
)


class Base(DeclarativeBase):
    pass


class AuctionItemRow(Base):
    __tablename__ = "auction_items"

    case_no: Mapped[str] = mapped_column(String, primary_key=True)
    item_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    court: Mapped[str] = mapped_column(String, nullable=False)
    auction_date: Mapped[date] = mapped_column(Date, nullable=False)
    appraisal_price: Mapped[int] = mapped_column(Integer, nullable=False)
    min_bid_price: Mapped[int] = mapped_column(Integer, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    use_type: Mapped[str] = mapped_column(String, nullable=False)
    area_m2: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str] = mapped_column(String, nullable=False)


def _engine(database_url: str = DEFAULT_DATABASE_URL) -> Any:
    return create_engine(database_url, pool_pre_ping=True)


def init_db(database_url: str = DEFAULT_DATABASE_URL) -> None:
    Base.metadata.create_all(_engine(database_url))


def _to_row_dict(item: AuctionItem) -> dict[str, Any]:
    return {
        "case_no": item.case_no,
        "item_no": item.item_no,
        "court": item.court,
        "auction_date": item.auction_date,
        "appraisal_price": item.appraisal_price,
        "min_bid_price": item.min_bid_price,
        "failed_count": item.failed_count,
        "address": item.address,
        "use_type": item.use_type,
        "area_m2": item.area_m2,
        "status": item.status,
        "source_url": item.source_url,
    }


def _from_row(row: AuctionItemRow) -> AuctionItem:
    return AuctionItem(
        case_no=row.case_no,
        item_no=row.item_no,
        court=row.court,
        auction_date=row.auction_date,
        appraisal_price=row.appraisal_price,
        min_bid_price=row.min_bid_price,
        failed_count=row.failed_count,
        address=row.address,
        use_type=row.use_type,
        area_m2=row.area_m2,
        status=row.status,
        source_url=row.source_url,
    )


def save(
    items: list[AuctionItem], database_url: str = DEFAULT_DATABASE_URL
) -> None:
    if not items:
        return

    rows = [_to_row_dict(item) for item in items]
    stmt = insert(AuctionItemRow).values(rows)
    update_columns = {
        column.name: getattr(stmt.excluded, column.name)
        for column in AuctionItemRow.__table__.columns
        if column.name not in {"case_no", "item_no"}
    }
    stmt = stmt.on_conflict_do_update(
        index_elements=["case_no", "item_no"],
        set_=update_columns,
    )

    engine = _engine(database_url)
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def load_all(database_url: str = DEFAULT_DATABASE_URL) -> list[AuctionItem]:
    engine = _engine(database_url)
    with Session(engine) as session:
        rows = session.scalars(
            select(AuctionItemRow).order_by(AuctionItemRow.case_no, AuctionItemRow.item_no)
        ).all()
    return [_from_row(row) for row in rows]


def load_by_filter(
    database_url: str = DEFAULT_DATABASE_URL,
    *,
    use_type: str | None = None,
    min_failed: int | None = None,
    court: str | None = None,
) -> list[AuctionItem]:
    stmt = select(AuctionItemRow)
    if use_type is not None:
        stmt = stmt.where(AuctionItemRow.use_type == use_type)
    if min_failed is not None:
        stmt = stmt.where(AuctionItemRow.failed_count >= min_failed)
    if court is not None:
        stmt = stmt.where(AuctionItemRow.court == court)
    stmt = stmt.order_by(AuctionItemRow.case_no, AuctionItemRow.item_no)

    engine = _engine(database_url)
    with Session(engine) as session:
        rows = session.scalars(stmt).all()
    return [_from_row(row) for row in rows]


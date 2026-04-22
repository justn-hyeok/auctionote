from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class AuctionItem:
    case_no: str
    item_no: int
    court: str
    auction_date: date
    appraisal_price: int
    min_bid_price: int
    failed_count: int
    address: str
    use_type: str
    area_m2: float | None
    status: str
    source_url: str

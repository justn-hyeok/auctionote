"""Collect auction data into ``data/auctionote.db``.

Runs ``crawler.live.scrape_auctions`` against the real courtauction.go.kr
site. Falls back to parsing the synthetic fixtures under
``fixtures/raw/detail_*.html`` if the live scrape raises or returns zero
records (e.g. during an outage or a WebSquare layout change).
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.schema import AuctionItem  # noqa: E402
from crawler.live import scrape_auctions  # noqa: E402
from crawler.parse import parse_detail  # noqa: E402
from storage.sqlite import init_db, save  # noqa: E402

DB = ROOT / "data" / "auctionote.db"
FIXTURES_RAW = ROOT / "fixtures" / "raw"

logger = logging.getLogger(__name__)


def _collect_from_fixtures() -> list[AuctionItem]:
    return [
        parse_detail(p.read_text(encoding="utf-8"))
        for p in sorted(FIXTURES_RAW.glob("detail_*.html"))
    ]


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    DB.parent.mkdir(parents=True, exist_ok=True)
    init_db(DB)

    source = "live"
    try:
        items = scrape_auctions()
    except Exception:
        logger.exception("live scrape raised")
        items = []

    if not items:
        logger.warning("no live records; falling back to synthetic fixtures")
        items = _collect_from_fixtures()
        source = "fixtures (fallback)"

    save(items, DB)
    print(f"saved: {len(items)} items from {source} → {DB}")
    if not items:
        raise SystemExit("no items collected")


if __name__ == "__main__":
    main()

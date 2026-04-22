"""Collect auction data into ``data/auctionote.db``.

Attempts a live crawl through ``crawler.live`` first. Because Phase A abandoned
live collection against courtauction.go.kr (WebSquare SPA — see
``fixtures/LIVE_CRAWL_ABANDONED.md``), the live path currently raises
``LiveCrawlAbandoned`` on first call. We catch that and fall back to seeding the
DB from the synthetic fixtures in ``fixtures/raw/``. The source of each run is
printed so later phases (or a future live implementation) can tell them apart.
"""
from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.schema import AuctionItem  # noqa: E402
from crawler.live import LiveCrawlAbandoned, fetch_detail, fetch_list  # noqa: E402
from crawler.parse import parse_detail, parse_list  # noqa: E402
from storage.sqlite import init_db, save  # noqa: E402
DB = ROOT / "data" / "auctionote.db"
FIXTURES_RAW = ROOT / "fixtures" / "raw"

logger = logging.getLogger(__name__)

REGION_CODES = ["11", "41", "28"]  # 서울 / 경기 / 인천
MAX_ITEMS = 100


async def _collect_live() -> list[AuctionItem]:
    items: list[AuctionItem] = []
    for region in REGION_CODES:
        list_htmls = await fetch_list(region_code=region, max_pages=3)
        for list_html in list_htmls:
            for entry in parse_list(list_html):
                detail_html = await fetch_detail(entry["detail_url"])
                try:
                    items.append(parse_detail(detail_html))
                except Exception as exc:
                    logger.warning(
                        "skip %s: %s", entry.get("case_no"), exc
                    )
                if len(items) >= MAX_ITEMS:
                    return items
    return items


def _collect_from_fixtures() -> list[AuctionItem]:
    return [
        parse_detail(p.read_text(encoding="utf-8"))
        for p in sorted(FIXTURES_RAW.glob("detail_*.html"))
    ]


async def _async_main() -> int:
    DB.parent.mkdir(parents=True, exist_ok=True)
    init_db(DB)

    source: str
    try:
        items = await _collect_live()
        source = "live"
    except LiveCrawlAbandoned as exc:
        logger.warning("live crawl abandoned: %s", exc)
        logger.warning(
            "falling back to synthetic fixtures (fixtures/raw/detail_*.html)"
        )
        items = _collect_from_fixtures()
        source = "fixtures (synthetic)"

    save(items, DB)
    print(f"saved: {len(items)} items from {source} → {DB}")
    return len(items)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    count = asyncio.run(_async_main())
    if count == 0:
        raise SystemExit("no items collected")


if __name__ == "__main__":
    main()

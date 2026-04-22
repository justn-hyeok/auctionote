"""Live crawler for Korean court auction data.

Phase A status: live collection ABANDONED. See `fixtures/LIVE_CRAWL_ABANDONED.md`.
courtauction.go.kr is a WebSquare SPA that cannot be crawled with plain HTTP fetches
and requires Playwright + WebSquare XHR/session reverse-engineering beyond Phase A
scope.

Fixtures under `fixtures/` were produced via `scripts/seed_fixtures.py` (plan B,
synthetic) to unblock Phase B. This module retains the async API shape required by
the Phase A spec so a future live implementation (or a switch to the data.go.kr
public API) can slot in without breaking callers.
"""
from __future__ import annotations

SOURCE_BASE_URL = "https://www.courtauction.go.kr"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
RATE_LIMIT_SECONDS = 2.0
TIMEOUT_SECONDS = 30.0
MAX_RETRIES = 2


class LiveCrawlAbandoned(NotImplementedError):
    """Raised when live crawl is invoked. Plan-B synthesis is used instead."""


async def fetch_list(region_code: str, max_pages: int) -> list[str]:
    raise LiveCrawlAbandoned(
        "Live list fetch not implemented. See fixtures/LIVE_CRAWL_ABANDONED.md. "
        "Use fixtures/raw/list_page_*.html for Phase B parser development."
    )


async def fetch_detail(detail_url: str) -> str:
    raise LiveCrawlAbandoned(
        "Live detail fetch not implemented. See fixtures/LIVE_CRAWL_ABANDONED.md. "
        "Use fixtures/raw/detail_*.html for Phase B parser development."
    )


if __name__ == "__main__":
    import sys

    sys.stderr.write(
        "crawler.live: live crawl abandoned. See fixtures/LIVE_CRAWL_ABANDONED.md.\n"
        "Run `uv run python scripts/seed_fixtures.py` to regenerate synthetic fixtures.\n"
    )
    sys.exit(1)

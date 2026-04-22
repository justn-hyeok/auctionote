"""Parsers for court auction list and detail HTML pages."""
from __future__ import annotations

import logging
import re
from datetime import date
from typing import Any

from bs4 import BeautifulSoup

from analysis.schema import AuctionItem

logger = logging.getLogger(__name__)

_NON_DIGIT_RE = re.compile(r"[^\d]")
_NUMERIC_RE = re.compile(r"[\d.]+")


def _digits_to_int(text: str, *, field: str) -> int:
    digits = _NON_DIGIT_RE.sub("", text)
    if not digits:
        raise ValueError(f"{field}: no digits in {text!r}")
    return int(digits)


def _area_to_float_or_none(text: str) -> float | None:
    cleaned = text.strip()
    if not cleaned or cleaned == "-":
        return None
    match = _NUMERIC_RE.search(cleaned)
    if match is None:
        return None
    return float(match.group(0))


def _text_of(soup: BeautifulSoup, selector: str, *, field: str) -> str:
    element = soup.select_one(selector)
    if element is None:
        raise ValueError(f"{field}: selector not found: {selector}")
    return element.get_text(strip=True)


def _attr_of(
    soup: BeautifulSoup, selector: str, attr: str, *, field: str
) -> str:
    element = soup.select_one(selector)
    if element is None:
        raise ValueError(f"{field}: selector not found: {selector}")
    value = element.get(attr)
    if value is None:
        raise ValueError(f"{field}: attribute {attr!r} missing on {selector}")
    if isinstance(value, list):
        value = " ".join(value)
    return str(value)


def parse_detail(html: str) -> AuctionItem:
    soup = BeautifulSoup(html, "lxml")

    item_no = int(_attr_of(soup, ".item-no", "data-item-no", field="item_no"))

    source_el = soup.select_one('meta[name="source-url"]')
    source_url = ""
    if source_el is not None:
        content = source_el.get("content")
        if isinstance(content, list):
            content = " ".join(content)
        if content is not None:
            source_url = str(content)

    return AuctionItem(
        case_no=_text_of(soup, ".case-title", field="case_no"),
        item_no=item_no,
        court=_text_of(soup, ".court", field="court"),
        auction_date=date.fromisoformat(
            _text_of(soup, ".auction-date", field="auction_date")
        ),
        appraisal_price=_digits_to_int(
            _text_of(soup, ".appraisal-price", field="appraisal_price"),
            field="appraisal_price",
        ),
        min_bid_price=_digits_to_int(
            _text_of(soup, ".min-bid-price", field="min_bid_price"),
            field="min_bid_price",
        ),
        failed_count=_digits_to_int(
            _text_of(soup, ".failed-count", field="failed_count"),
            field="failed_count",
        ),
        address=_text_of(soup, ".address", field="address"),
        use_type=_text_of(soup, ".use-type", field="use_type"),
        area_m2=_area_to_float_or_none(
            _text_of(soup, ".area-m2", field="area_m2")
        ),
        status=_text_of(soup, ".status", field="status"),
        source_url=source_url,
    )


def parse_list(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    rows: list[dict[str, Any]] = []
    for row in soup.select("tr.result-row"):
        case_el = row.select_one(".case-no")
        link_el = row.select_one("a.detail-link")
        if case_el is None or link_el is None:
            logger.warning("list row skipped: missing case-no or detail-link")
            continue
        href = link_el.get("href")
        if href is None:
            logger.warning("list row skipped: anchor has no href")
            continue
        if isinstance(href, list):
            href = " ".join(href)
        rows.append(
            {
                "case_no": case_el.get_text(strip=True),
                "detail_url": str(href),
            }
        )
    return rows

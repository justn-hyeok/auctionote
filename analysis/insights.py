"""Screening and data-quality helpers for auction items."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from statistics import median

from analysis.schema import AuctionItem


@dataclass(frozen=True)
class ScreeningResult:
    item: AuctionItem
    region: str
    discount_rate: float
    min_bid_price_per_m2: float | None
    region_price_per_m2_ratio: float | None
    screening_score: float
    flags: tuple[str, ...]


def discount_rate(item: AuctionItem) -> float:
    if item.appraisal_price <= 0:
        return 0.0
    return (item.appraisal_price - item.min_bid_price) / item.appraisal_price


def min_bid_price_per_m2(item: AuctionItem) -> float | None:
    if item.area_m2 is None or item.area_m2 <= 0:
        return None
    if item.min_bid_price <= 0:
        return None
    return item.min_bid_price / item.area_m2


def region_key(address: str) -> str:
    tokens = address.split()
    return " ".join(tokens[:2]) if tokens else ""


def _region_price_medians(items: list[AuctionItem]) -> dict[tuple[str, str], float]:
    groups: dict[tuple[str, str], list[float]] = defaultdict(list)
    for item in items:
        price = min_bid_price_per_m2(item)
        if price is None:
            continue
        groups[(region_key(item.address), item.use_type)].append(price)
    return {
        key: median(prices)
        for key, prices in groups.items()
        if prices
    }


def quality_flags(item: AuctionItem) -> tuple[str, ...]:
    flags: list[str] = []
    item_discount = discount_rate(item)
    if item.appraisal_price <= 0:
        flags.append("감정가 누락")
    if item.min_bid_price <= 0:
        flags.append("최저가 누락")
    if item.appraisal_price > 0 and item.min_bid_price > item.appraisal_price:
        flags.append("최저가가 감정가 초과")
    if item.area_m2 is None or item.area_m2 <= 0:
        flags.append("면적 누락")
    if item.failed_count > 0 and item_discount <= 0.01:
        flags.append("유찰 대비 할인율 낮음")
    if item.failed_count >= 7:
        flags.append("장기 유찰")
    if item.status not in {"진행", "유찰"}:
        flags.append(f"상태 확인 필요: {item.status}")
    return tuple(flags)


def _discount_score(item_discount: float) -> float:
    capped = max(0.0, min(item_discount, 0.7))
    return capped / 0.7 * 45.0


def _relative_value_score(ratio: float | None) -> float:
    if ratio is None:
        return 5.0
    if ratio <= 0.75:
        return 25.0
    if ratio <= 0.90:
        return 18.0
    if ratio <= 1.00:
        return 10.0
    if ratio <= 1.15:
        return 4.0
    return 0.0


def _failed_count_score(failed_count: int) -> float:
    if failed_count == 0:
        return 8.0
    if failed_count <= 3:
        return 15.0
    if failed_count <= 6:
        return 10.0
    return 3.0


def _completeness_score(item: AuctionItem) -> float:
    score = 0.0
    if item.address:
        score += 3.0
    if item.area_m2 is not None and item.area_m2 > 0:
        score += 4.0
    if item.source_url:
        score += 3.0
    return score


def _urgency_score(item: AuctionItem, today: date | None) -> float:
    if today is None:
        return 0.0
    days_left = (item.auction_date - today).days
    if 0 <= days_left <= 7:
        return 5.0
    if 8 <= days_left <= 14:
        return 3.0
    return 0.0


def screen_items(
    items: list[AuctionItem],
    *,
    today: date | None = None,
) -> list[ScreeningResult]:
    medians = _region_price_medians(items)
    results: list[ScreeningResult] = []
    for item in items:
        price = min_bid_price_per_m2(item)
        median_price = medians.get((region_key(item.address), item.use_type))
        ratio = (
            price / median_price
            if price is not None and median_price is not None and median_price > 0
            else None
        )
        item_discount = discount_rate(item)
        score = (
            _discount_score(item_discount)
            + _relative_value_score(ratio)
            + _failed_count_score(item.failed_count)
            + _completeness_score(item)
            + _urgency_score(item, today)
        )
        results.append(
            ScreeningResult(
                item=item,
                region=region_key(item.address),
                discount_rate=item_discount,
                min_bid_price_per_m2=price,
                region_price_per_m2_ratio=ratio,
                screening_score=round(min(score, 100.0), 1),
                flags=quality_flags(item),
            )
        )
    return sorted(
        results,
        key=lambda result: (
            result.screening_score,
            result.discount_rate,
            -len(result.flags),
        ),
        reverse=True,
    )


def quality_summary(items: list[AuctionItem]) -> list[dict[str, int | str]]:
    counts: dict[str, int] = defaultdict(int)
    for item in items:
        for flag in quality_flags(item):
            counts[flag] += 1
    return [
        {"flag": flag, "count": count}
        for flag, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ]

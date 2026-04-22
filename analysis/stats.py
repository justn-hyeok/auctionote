"""Pure aggregate statistics over AuctionItem collections."""
from __future__ import annotations

from collections import defaultdict
from statistics import mean, median
from typing import Any

from analysis.schema import AuctionItem


def _discount(item: AuctionItem) -> float:
    if item.appraisal_price <= 0:
        return 0.0
    return (item.appraisal_price - item.min_bid_price) / item.appraisal_price


def failed_count_discount_stats(
    items: list[AuctionItem],
) -> list[dict[str, Any]]:
    if not items:
        return []
    groups: dict[int, list[float]] = defaultdict(list)
    for item in items:
        groups[item.failed_count].append(_discount(item))
    return [
        {
            "failed_count": failed_count,
            "count": len(discounts),
            "mean_discount": mean(discounts),
            "median_discount": median(discounts),
        }
        for failed_count, discounts in sorted(groups.items())
    ]


def _region_key(address: str) -> str:
    tokens = address.split()
    return " ".join(tokens[:2]) if tokens else ""


def by_region(items: list[AuctionItem]) -> list[dict[str, Any]]:
    counts: dict[str, int] = defaultdict(int)
    for item in items:
        counts[_region_key(item.address)] += 1
    return [
        {"region": region, "count": count}
        for region, count in sorted(counts.items())
    ]


def by_use_type(items: list[AuctionItem]) -> list[dict[str, Any]]:
    counts: dict[str, int] = defaultdict(int)
    for item in items:
        counts[item.use_type] += 1
    return [
        {"use_type": use_type, "count": count}
        for use_type, count in sorted(counts.items())
    ]

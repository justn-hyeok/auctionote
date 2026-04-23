"""Offline heuristic market-signal helpers for auction items.

These helpers derive rough per-m2 price signals only from the currently loaded
auction dataset. They are useful for screening, but they are not appraisals.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from statistics import median
from typing import Literal

from analysis.insights import min_bid_price_per_m2, region_key
from analysis.schema import AuctionItem

MarketConfidence = Literal["low", "medium", "high"]

HEURISTIC_NOTICE = (
    "Heuristic only: estimated from this auction dataset's observed minimum bid "
    "price per m2, not real appraisal or market-price advice."
)


@dataclass(frozen=True)
class MarketPriceEstimate:
    region: str
    use_type: str
    estimated_price_per_m2: float
    sample_size: int
    confidence: MarketConfidence
    heuristic_notice: str = HEURISTIC_NOTICE


@dataclass(frozen=True)
class MarketSignal:
    item: AuctionItem
    region: str
    use_type: str
    estimated_market_price_per_m2: float | None
    estimated_market_value: float | None
    value_gap_rate: float | None
    sample_size: int
    confidence: MarketConfidence
    heuristic_notice: str = HEURISTIC_NOTICE


def confidence_for_sample_size(sample_size: int) -> MarketConfidence:
    if sample_size >= 5:
        return "high"
    if sample_size >= 3:
        return "medium"
    return "low"


def estimate_market_prices_per_m2(
    items: list[AuctionItem],
) -> dict[tuple[str, str], MarketPriceEstimate]:
    groups: dict[tuple[str, str], list[float]] = defaultdict(list)
    for item in items:
        price = min_bid_price_per_m2(item)
        if price is None:
            continue
        groups[(region_key(item.address), item.use_type)].append(price)

    return {
        key: MarketPriceEstimate(
            region=key[0],
            use_type=key[1],
            estimated_price_per_m2=median(prices),
            sample_size=len(prices),
            confidence=confidence_for_sample_size(len(prices)),
        )
        for key, prices in sorted(groups.items())
        if prices
    }


def market_signals(items: list[AuctionItem]) -> list[MarketSignal]:
    estimates = estimate_market_prices_per_m2(items)
    signals: list[MarketSignal] = []

    for item in items:
        region = region_key(item.address)
        estimate = estimates.get((region, item.use_type))
        estimated_price_per_m2: float | None = None
        estimated_market_value: float | None = None
        value_gap_rate: float | None = None
        sample_size = 0
        confidence: MarketConfidence = "low"

        if estimate is not None:
            estimated_price_per_m2 = estimate.estimated_price_per_m2
            sample_size = estimate.sample_size
            confidence = estimate.confidence
            if item.area_m2 is not None and item.area_m2 > 0:
                estimated_market_value = estimated_price_per_m2 * item.area_m2

        if (
            estimated_market_value is not None
            and estimated_market_value > 0
            and item.min_bid_price > 0
        ):
            value_gap_rate = (estimated_market_value - item.min_bid_price) / estimated_market_value

        signals.append(
            MarketSignal(
                item=item,
                region=region,
                use_type=item.use_type,
                estimated_market_price_per_m2=estimated_price_per_m2,
                estimated_market_value=estimated_market_value,
                value_gap_rate=value_gap_rate,
                sample_size=sample_size,
                confidence=confidence,
            )
        )

    return signals

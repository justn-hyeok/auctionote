"""Offline geocoding helpers for Seoul court-auction addresses."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from analysis.schema import AuctionItem


@dataclass(frozen=True)
class GeoPoint:
    district: str
    latitude: float
    longitude: float
    confidence: float
    source: str


SEOUL_DISTRICT_CENTROIDS: Final[dict[str, tuple[float, float]]] = {
    "강남구": (37.5172, 127.0473),
    "강동구": (37.5301, 127.1238),
    "강북구": (37.6396, 127.0257),
    "강서구": (37.5509, 126.8495),
    "관악구": (37.4784, 126.9516),
    "광진구": (37.5384, 127.0823),
    "구로구": (37.4955, 126.8877),
    "금천구": (37.4569, 126.8958),
    "노원구": (37.6542, 127.0568),
    "도봉구": (37.6688, 127.0471),
    "동대문구": (37.5744, 127.0396),
    "동작구": (37.5124, 126.9393),
    "마포구": (37.5663, 126.9019),
    "서대문구": (37.5791, 126.9368),
    "서초구": (37.4837, 127.0324),
    "성동구": (37.5633, 127.0369),
    "성북구": (37.5894, 127.0167),
    "송파구": (37.5145, 127.1059),
    "양천구": (37.5169, 126.8664),
    "영등포구": (37.5264, 126.8963),
    "용산구": (37.5326, 126.9900),
    "은평구": (37.6176, 126.9227),
    "종로구": (37.5735, 126.9788),
    "중구": (37.5636, 126.9976),
    "중랑구": (37.6063, 127.0927),
}

_SEOUL_MARKER_RE: Final[re.Pattern[str]] = re.compile(r"\b서울(?:특별시|시)?\b")
_NON_SEOUL_REGION_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(?:"
    r"부산|부산광역시|대구|대구광역시|인천|인천광역시|광주|광주광역시|"
    r"대전|대전광역시|울산|울산광역시|세종|세종특별자치시|"
    r"경기|경기도|강원|강원도|충북|충청북도|충남|충청남도|"
    r"전북|전라북도|전남|전라남도|경북|경상북도|경남|경상남도|"
    r"제주|제주특별자치도"
    r")\b"
)
_ADDRESS_BOUNDARY: Final[str] = r"(?=$|\s|,|\(|\)|\[|\]|-|번지)"
_DISTRICT_PATTERN: Final[str] = "|".join(
    sorted((re.escape(district) for district in SEOUL_DISTRICT_CENTROIDS), key=len, reverse=True)
)
_SEOUL_DISTRICT_RE: Final[re.Pattern[str]] = re.compile(
    rf"\b서울(?:특별시|시)?\s+(?P<district>{_DISTRICT_PATTERN}){_ADDRESS_BOUNDARY}"
)
_LEADING_DISTRICT_RE: Final[re.Pattern[str]] = re.compile(
    rf"^(?P<district>{_DISTRICT_PATTERN}){_ADDRESS_BOUNDARY}"
)

_CENTROID_SOURCE: Final[str] = "offline:seoul-district-centroid:v1"
_EXPLICIT_SEOUL_CONFIDENCE: Final[float] = 0.68
_LEADING_DISTRICT_CONFIDENCE: Final[float] = 0.58


def _normalized_address(address: str) -> str:
    return " ".join(address.strip().split())


def parse_seoul_district(address: str) -> str | None:
    """Return a Seoul district name parsed from an address, if one is recognizable."""
    normalized = _normalized_address(address)
    if not normalized:
        return None

    explicit_match = _SEOUL_DISTRICT_RE.search(normalized)
    if explicit_match is not None:
        return explicit_match.group("district")

    if _SEOUL_MARKER_RE.search(normalized) is not None:
        for district in SEOUL_DISTRICT_CENTROIDS:
            if re.search(rf"\b{re.escape(district)}{_ADDRESS_BOUNDARY}", normalized):
                return district
        return None

    if _NON_SEOUL_REGION_RE.search(normalized) is not None:
        return None

    leading_match = _LEADING_DISTRICT_RE.search(normalized)
    if leading_match is None:
        return None
    return leading_match.group("district")


def geocode_address(address: str) -> GeoPoint | None:
    """Resolve a Korean address to an approximate Seoul district centroid."""
    district = parse_seoul_district(address)
    if district is None:
        return None

    latitude, longitude = SEOUL_DISTRICT_CENTROIDS[district]
    confidence = (
        _EXPLICIT_SEOUL_CONFIDENCE
        if _SEOUL_MARKER_RE.search(_normalized_address(address)) is not None
        else _LEADING_DISTRICT_CONFIDENCE
    )
    return GeoPoint(
        district=district,
        latitude=latitude,
        longitude=longitude,
        confidence=confidence,
        source=_CENTROID_SOURCE,
    )


def geocode_item(item: AuctionItem) -> GeoPoint | None:
    """Resolve an auction item address to an approximate Seoul district centroid."""
    return geocode_address(item.address)


__all__ = [
    "GeoPoint",
    "SEOUL_DISTRICT_CENTROIDS",
    "geocode_address",
    "geocode_item",
    "parse_seoul_district",
]

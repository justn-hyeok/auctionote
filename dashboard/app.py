"""auctionote Streamlit dashboard."""
from __future__ import annotations

import logging
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import folium  # noqa: E402
import pandas as pd  # noqa: E402
import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402
from streamlit_folium import st_folium  # noqa: E402

from analysis.geocode import geocode_item  # noqa: E402
from analysis.insights import quality_summary, screen_items  # noqa: E402
from analysis.market import market_signals  # noqa: E402
from analysis.schema import AuctionItem  # noqa: E402
from analysis.stats import failed_count_discount_stats  # noqa: E402
from crawler.parse import parse_detail  # noqa: E402
from storage.sqlite import init_db, load_all, save  # noqa: E402

DB_PATH = ROOT / "data" / "auctionote.db"
FIXTURES_RAW = ROOT / "fixtures" / "raw"
ELASTIC_URL = os.getenv("AUCTIONOTE_ELASTIC_URL")
DATABASE_URL = os.getenv("AUCTIONOTE_DATABASE_URL")

logger = logging.getLogger(__name__)


def _pct(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.1%}"


def _won(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f"{value:,.0f}원"


def _item_key(item: AuctionItem) -> tuple[str, int]:
    return (item.case_no, item.item_no)


def _seed_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    init_db(db_path)
    items = [
        parse_detail(p.read_text(encoding="utf-8"))
        for p in sorted(FIXTURES_RAW.glob("detail_*.html"))
    ]
    save(items, db_path)
    logger.info("seeded %d items into %s", len(items), db_path)


@st.cache_data
def _load_items(db_path_str: str, database_url: str | None) -> list[AuctionItem]:
    if database_url:
        try:
            from storage.postgres import load_all as load_all_postgres

            return load_all_postgres(database_url)
        except Exception as exc:
            logger.info("PostgreSQL unavailable, falling back to SQLite: %s", exc)

    p = Path(db_path_str)
    if not p.exists():
        _seed_db(p)
    return load_all(p)


def _filter_items_in_memory(
    items: list[AuctionItem],
    *,
    query: str,
    selected_uses: list[str],
    min_failed: int,
    selected_courts: list[str],
) -> list[AuctionItem]:
    query_terms = query.strip().lower().split()
    filtered: list[AuctionItem] = []
    for item in items:
        if item.use_type not in selected_uses:
            continue
        if item.failed_count < min_failed:
            continue
        if item.court not in selected_courts:
            continue
        if query_terms:
            haystack = " ".join(
                [
                    item.case_no,
                    item.court,
                    item.address,
                    item.use_type,
                    item.status,
                ]
            ).lower()
            if not all(term in haystack for term in query_terms):
                continue
        filtered.append(item)
    return filtered


def _render() -> None:
    st.set_page_config(page_title="auctionote", layout="wide")
    st.title("auctionote")

    items = _load_items(str(DB_PATH), DATABASE_URL)
    if not items:
        st.info("데이터 없음")
        return

    all_use_types = sorted({it.use_type for it in items})
    all_courts = sorted({it.court for it in items})

    with st.sidebar:
        st.header("필터")
        query = st.text_input("키워드 검색", placeholder="예: 강남 아파트 유찰")
        selected_uses = st.multiselect(
            "물건용도", all_use_types, default=all_use_types
        )
        min_failed_raw = st.number_input(
            "최소 유찰횟수", min_value=0, max_value=20, value=0, step=1
        )
        min_failed = int(min_failed_raw)
        selected_courts = st.multiselect(
            "법원", all_courts, default=all_courts
        )

    if not selected_uses or not selected_courts:
        filtered = []
        search_backend = "필터"
    elif ELASTIC_URL:
        from search.elastic import create_client, try_search_items

        elastic_results = try_search_items(
            create_client(ELASTIC_URL),
            query=query,
            use_types=selected_uses,
            courts=selected_courts,
            min_failed=min_failed,
            size=500,
        )
        if elastic_results is None:
            filtered = _filter_items_in_memory(
                items,
                query=query,
                selected_uses=selected_uses,
                min_failed=min_failed,
                selected_courts=selected_courts,
            )
            search_backend = "SQLite fallback"
        else:
            filtered = elastic_results
            search_backend = "Elasticsearch"
    else:
        filtered = _filter_items_in_memory(
            items,
            query=query,
            selected_uses=selected_uses,
            min_failed=min_failed,
            selected_courts=selected_courts,
        )
        search_backend = "SQLite demo"

    if not filtered:
        st.warning("필터 결과 없음")
        return

    st.caption(f"검색 백엔드: {search_backend}")

    screened = screen_items(filtered, today=date.today())
    market_by_key = {
        _item_key(signal.item): signal
        for signal in market_signals(filtered)
    }
    flagged_count = sum(1 for result in screened if result.flags)
    discount_values = [result.discount_rate for result in screened]
    price_per_m2_values = [
        result.min_bid_price_per_m2
        for result in screened
        if result.min_bid_price_per_m2 is not None
    ]
    value_gap_count = sum(
        1
        for signal in market_by_key.values()
        if signal.value_gap_rate is not None and signal.value_gap_rate >= 0.15
    )

    st.subheader("요약")
    kpi_cols = st.columns(5)
    kpi_cols[0].metric("물건 수", f"{len(filtered):,}건")
    kpi_cols[1].metric("평균 할인율", _pct(sum(discount_values) / len(discount_values)))
    kpi_cols[2].metric(
        "중앙 ㎡당 최저가",
        _won(pd.Series(price_per_m2_values).median() if price_per_m2_values else None),
    )
    kpi_cols[3].metric("시세갭 15%+", f"{value_gap_count:,}건")
    kpi_cols[4].metric("품질 확인 필요", f"{flagged_count:,}건")

    st.subheader("검토 우선순위")
    rows: list[dict[str, Any]] = []
    for result in screened[:15]:
        signal = market_by_key.get(_item_key(result.item))
        value_gap = (
            signal.value_gap_rate * 100
            if signal is not None and signal.value_gap_rate is not None
            else None
        )
        rows.append(
            {
                "점수": result.screening_score,
                "사건": result.item.case_no,
                "법원": result.item.court,
                "매각기일": result.item.auction_date,
                "유찰": result.item.failed_count,
                "할인율": result.discount_rate * 100,
                "㎡당 최저가": result.min_bid_price_per_m2,
                "지역 대비": result.region_price_per_m2_ratio,
                "시세갭": value_gap,
                "시세신뢰": signal.confidence if signal is not None else "low",
                "용도": result.item.use_type,
                "확인": ", ".join(result.flags),
                "주소": result.item.address,
            }
        )
    df_screened = pd.DataFrame(rows)
    st.dataframe(
        df_screened,
        use_container_width=True,
        column_config={
            "할인율": st.column_config.NumberColumn(format="%.1f%%"),
            "㎡당 최저가": st.column_config.NumberColumn(format="%,.0f원"),
            "지역 대비": st.column_config.NumberColumn(format="%.2f배"),
            "시세갭": st.column_config.NumberColumn(format="%.1f%%"),
        },
    )

    summary = quality_summary(filtered)
    if summary:
        st.subheader("데이터 품질 체크")
        st.dataframe(pd.DataFrame(summary), use_container_width=True)

    st.subheader("유찰횟수별 평균 할인율")
    stats = failed_count_discount_stats(filtered)
    df_stats = pd.DataFrame(stats)
    fig = px.bar(
        df_stats,
        x="failed_count",
        y="mean_discount",
        hover_data=["count", "median_discount"],
        labels={
            "failed_count": "유찰 횟수",
            "mean_discount": "평균 할인율",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("물건 목록")
    df_items = pd.DataFrame(
        [
            {
                "사건": it.case_no,
                "물건": it.item_no,
                "법원": it.court,
                "매각기일": it.auction_date,
                "감정가": it.appraisal_price,
                "최저가": it.min_bid_price,
                "유찰": it.failed_count,
                "용도": it.use_type,
                "면적(㎡)": it.area_m2,
                "상태": it.status,
                "주소": it.address,
            }
            for it in filtered
        ]
    )
    st.dataframe(df_items, use_container_width=True)

    st.subheader("물건 위치 분포")
    fmap = folium.Map(location=(37.56, 126.98), zoom_start=11)
    district_counts: dict[str, int] = {}
    district_points: dict[str, tuple[float, float]] = {}
    for it in filtered:
        point = geocode_item(it)
        if point is None:
            logger.warning(
                "no approximate coordinates mapped for address: %s", it.address
            )
            continue
        district_counts[point.district] = district_counts.get(point.district, 0) + 1
        district_points[point.district] = (point.latitude, point.longitude)
    for district, count in district_counts.items():
        coord = district_points[district]
        folium.CircleMarker(
            location=coord,
            radius=6 + count * 2,
            popup=f"{district}: {count}건",
            color="#1f77b4",
            fill=True,
            fill_opacity=0.6,
        ).add_to(fmap)
    st_folium(fmap, width=None, height=500)


_render()

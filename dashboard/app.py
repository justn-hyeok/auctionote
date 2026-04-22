"""auctionote Streamlit dashboard."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import folium  # noqa: E402
import pandas as pd  # noqa: E402
import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402
from streamlit_folium import st_folium  # noqa: E402

from analysis.schema import AuctionItem  # noqa: E402
from analysis.stats import failed_count_discount_stats  # noqa: E402
from crawler.parse import parse_detail  # noqa: E402
from storage.sqlite import init_db, load_all, save  # noqa: E402

DB_PATH = ROOT / "data" / "auctionote.db"
FIXTURES_RAW = ROOT / "fixtures" / "raw"

COURT_COORDS: dict[str, tuple[float, float]] = {
    "서울중앙지방법원": (37.4944, 127.0075),
    "서울동부지방법원": (37.5274, 127.1289),
    "서울남부지방법원": (37.5152, 126.8696),
    "서울북부지방법원": (37.6393, 127.0168),
    "서울서부지방법원": (37.5655, 126.9083),
    "수원지방법원": (37.2683, 127.0287),
    "인천지방법원": (37.4472, 126.7052),
    "대전지방법원": (36.3395, 127.4310),
    "대구지방법원": (35.8557, 128.5823),
    "부산지방법원": (35.1547, 129.0619),
    "광주지방법원": (35.1581, 126.8508),
    "의정부지방법원": (37.7380, 127.0368),
    "춘천지방법원": (37.8813, 127.7298),
}

logger = logging.getLogger(__name__)


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
def _load_items(db_path_str: str) -> list[AuctionItem]:
    p = Path(db_path_str)
    if not p.exists():
        _seed_db(p)
    return load_all(p)


def _render() -> None:
    st.set_page_config(page_title="auctionote", layout="wide")
    st.title("auctionote")

    items = _load_items(str(DB_PATH))
    if not items:
        st.info("데이터 없음")
        return

    all_use_types = sorted({it.use_type for it in items})
    all_courts = sorted({it.court for it in items})

    with st.sidebar:
        st.header("필터")
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

    filtered = [
        it
        for it in items
        if it.use_type in selected_uses
        and it.failed_count >= min_failed
        and it.court in selected_courts
    ]

    if not filtered:
        st.warning("필터 결과 없음")
        return

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

    st.subheader("법원별 물건 분포")
    fmap = folium.Map(location=(36.5, 127.8), zoom_start=7)
    court_counts: dict[str, int] = {}
    for it in filtered:
        court_counts[it.court] = court_counts.get(it.court, 0) + 1
    for court, count in court_counts.items():
        coord = COURT_COORDS.get(court)
        if coord is None:
            logger.warning("no coordinates mapped for court: %s", court)
            continue
        folium.CircleMarker(
            location=coord,
            radius=6 + count * 2,
            popup=f"{court}: {count}건",
            color="#1f77b4",
            fill=True,
            fill_opacity=0.6,
        ).add_to(fmap)
    st_folium(fmap, width=None, height=500)


_render()

"""Live scraper for courtauction.go.kr via Playwright.

Executes 물건상세검색 (property detail search) against a list of
``SearchTarget`` (court × property subtype) combinations and builds
``AuctionItem`` records directly from the rendered result grid. The list
view already contains the 전용면적 value (embedded inside the 소재지+내역
cell), so detail pages are not fetched. Phase A's synthetic fixtures remain
as parser regression tests under ``fixtures/``.

Selectors were discovered manually against the live WebSquare UI and are
recorded at module scope. If the site's WebSquare layout changes, the
selectors are the first thing to re-probe.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, timedelta

from playwright.sync_api import Page, sync_playwright

from analysis.schema import AuctionItem

logger = logging.getLogger(__name__)

INDEX_URL = "https://www.courtauction.go.kr/pgj/index.on"

_SEARCH_MENU = "#mf_wfm_header_anc_auctnGdsMain"
_COURT_SELECT = "#mf_wfm_mainFrame_sbx_rletCortOfc"
_DATE_START = "#mf_wfm_mainFrame_cal_rletPerdStr_input"
_DATE_END = "#mf_wfm_mainFrame_cal_rletPerdEnd_input"
_LCL = "#mf_wfm_mainFrame_sbx_rletLclLst"
_MCL = "#mf_wfm_mainFrame_sbx_rletMclLst"
_SCL = "#mf_wfm_mainFrame_sbx_rletSclLst"
_SEARCH_BTN = "#mf_wfm_mainFrame_btn_gdsDtlSrch"
_RESULT_TABLE = "#mf_wfm_mainFrame_grd_gdsDtlSrchResult_body_table"

SEOUL_COURTS = [
    "서울중앙지방법원",
    "서울동부지방법원",
    "서울서부지방법원",
    "서울남부지방법원",
    "서울북부지방법원",
]


@dataclass(frozen=True)
class SearchTarget:
    court: str
    lcl: str
    mcl: str
    scl: str


def default_targets() -> list[SearchTarget]:
    return [
        SearchTarget(court=c, lcl="건물", mcl="주거용건물", scl="아파트")
        for c in SEOUL_COURTS
    ]


_USE_TYPE_MAP = {
    "아파트": "아파트",
    "단독주택": "단독",
    "다가구주택": "단독",
    "다중주택": "단독",
    "다세대주택": "다세대",
    "연립주택": "연립",
    "빌라": "다세대",
    "오피스텔": "오피스텔",
    "상가주택": "기타",
    "주상복합": "아파트",
    "기숙사": "기타",
}

_CASE_RE = re.compile(r"\d{4}타경\d+")
_AREA_RE = re.compile(r"([\d]+\.?\d*)\s*㎡")
_DATE_RE = re.compile(r"(\d{4})\.(\d{1,2})\.(\d{1,2})")
_FAILED_RE = re.compile(r"유찰\s*(\d+)")


def _first_case_no(text: str) -> str | None:
    m = _CASE_RE.search(text)
    return m.group(0) if m else None


def _first_area(text: str) -> float | None:
    m = _AREA_RE.search(text)
    try:
        return float(m.group(1)) if m else None
    except ValueError:
        return None


def _parse_int(text: str) -> int:
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else 0


def _status_bucket(text: str) -> str:
    for key in ("유찰", "낙찰", "변경", "취하", "기각"):
        if key in text:
            return key
    return "진행"


def _failed_count(text: str) -> int:
    m = _FAILED_RE.search(text)
    return int(m.group(1)) if m else 0


def _select_and_settle(
    page: Page, selector: str, label: str, pause_ms: int = 1200
) -> None:
    page.select_option(selector, label=label)
    page.wait_for_timeout(pause_ms)


def _run_search(
    page: Page, target: SearchTarget, start: str, end: str
) -> list[list[str]]:
    page.goto(INDEX_URL, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(6_000)
    page.click(_SEARCH_MENU)
    page.wait_for_timeout(5_000)
    _select_and_settle(page, _COURT_SELECT, target.court, 600)
    page.fill(_DATE_START, start)
    page.fill(_DATE_END, end)
    page.wait_for_timeout(500)
    _select_and_settle(page, _LCL, target.lcl, 1500)
    _select_and_settle(page, _MCL, target.mcl, 1500)
    _select_and_settle(page, _SCL, target.scl, 500)
    page.click(_SEARCH_BTN)
    page.wait_for_timeout(9_000)
    return page.evaluate(
        """(sel) => {
            const tbl = document.querySelector(sel);
            if (!tbl) return [];
            return Array.from(tbl.querySelectorAll('tbody tr')).map(tr =>
                Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim())
            );
        }""",
        _RESULT_TABLE,
    )


def _rows_to_items(
    rows: list[list[str]], target: SearchTarget
) -> list[AuctionItem]:
    items: list[AuctionItem] = []
    i = 0
    while i + 1 < len(rows):
        main, sub = rows[i], rows[i + 1]
        i += 2
        if len(main) < 8 or len(sub) < 3:
            continue
        combo_cell = main[1] if len(main) > 1 else ""
        case_no = _first_case_no(combo_cell) or _first_case_no(main[0])
        if not case_no:
            logger.warning("row skipped: no case_no in %r", main[:2])
            continue
        court_line = (combo_cell.splitlines() or [target.court])[0].strip() or target.court
        try:
            item_no = int(main[2]) if main[2].strip().isdigit() else 1
        except Exception:
            item_no = 1
        loc_text = main[3] if len(main) > 3 else ""
        address = (loc_text.splitlines()[0] if loc_text else "").strip()
        area = _first_area(loc_text)
        appraisal = _parse_int(main[6] if len(main) > 6 else "")
        date_cell = main[7] if len(main) > 7 else ""
        date_match = _DATE_RE.search(date_cell)
        if not date_match:
            logger.warning("row skipped: no date in %r", date_cell)
            continue
        auction_date = date(
            int(date_match.group(1)),
            int(date_match.group(2)),
            int(date_match.group(3)),
        )
        use_type_raw = sub[0].strip()
        use_type = _USE_TYPE_MAP.get(use_type_raw, use_type_raw or "기타")
        minbid_first_line = (sub[1].splitlines() or [""])[0]
        min_bid_price = _parse_int(minbid_first_line)
        status_text = sub[2] if len(sub) > 2 else ""
        items.append(
            AuctionItem(
                case_no=case_no,
                item_no=item_no,
                court=court_line,
                auction_date=auction_date,
                appraisal_price=appraisal,
                min_bid_price=min_bid_price,
                failed_count=_failed_count(status_text),
                address=address,
                use_type=use_type,
                area_m2=area,
                status=_status_bucket(status_text),
                source_url=INDEX_URL,
            )
        )
    return items


def scrape_auctions(
    targets: list[SearchTarget] | None = None,
    *,
    days_window: int = 14,
) -> list[AuctionItem]:
    targets = targets or default_targets()
    today = date.today()
    start = today.strftime("%Y.%m.%d")
    end = (today + timedelta(days=days_window)).strftime("%Y.%m.%d")

    all_items: list[AuctionItem] = []
    seen: set[tuple[str, int]] = set()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1600, "height": 1000},
            locale="ko-KR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        )
        page = ctx.new_page()
        page.set_default_timeout(60_000)

        for target in targets:
            logger.info(
                "scraping %s | %s > %s > %s",
                target.court, target.lcl, target.mcl, target.scl,
            )
            try:
                rows = _run_search(page, target, start, end)
            except Exception as exc:  # noqa: BLE001
                logger.warning("search failed for %s: %s", target.court, exc)
                continue
            items = _rows_to_items(rows, target)
            fresh = [
                it for it in items
                if (it.case_no, it.item_no) not in seen
            ]
            for it in fresh:
                seen.add((it.case_no, it.item_no))
            logger.info(
                "→ %d rows, %d records (%d new)",
                len(rows), len(items), len(fresh),
            )
            all_items.extend(fresh)
        browser.close()
    return all_items

"""One-shot synthetic fixture generator — Phase A plan B.

Live crawling of courtauction.go.kr was abandoned (see
``fixtures/LIVE_CRAWL_ABANDONED.md``). This script produces hand-authored HTML
fixtures + 1:1 expected JSON oracles so Phase B (parser / stats / storage /
dashboard) can be implemented against a fixed contract.

Not a parser. Phase B must write ``crawler/parse.py`` independently.
"""
from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "fixtures" / "raw"
EXP_DIR = ROOT / "fixtures" / "expected"

DETAILS: list[dict[str, Any]] = [
    {
        "name": "detail_apt_1",
        "case_no": "2024타경10001", "item_no": 1,
        "court": "서울중앙지방법원", "auction_date": "2026-05-14",
        "appraisal_price": 1_000_000_000, "min_bid_price": 1_000_000_000,
        "failed_count": 0, "use_type": "아파트", "status": "진행",
        "address": "서울특별시 강남구 역삼동 123-4", "area_m2": 84.93,
        "source_url": "/pgj/detail/2024-10001/1",
    },
    {
        "name": "detail_apt_2",
        "case_no": "2024타경10002", "item_no": 1,
        "court": "서울중앙지방법원", "auction_date": "2026-05-21",
        "appraisal_price": 900_000_000, "min_bid_price": 720_000_000,
        "failed_count": 1, "use_type": "아파트", "status": "유찰",
        "address": "서울특별시 송파구 잠실동 45-6", "area_m2": 59.82,
        "source_url": "/pgj/detail/2024-10002/1",
    },
    {
        "name": "detail_apt_3",
        "case_no": "2024타경10003", "item_no": 1,
        "court": "서울동부지방법원", "auction_date": "2026-06-04",
        "appraisal_price": 1_500_000_000, "min_bid_price": 960_000_000,
        "failed_count": 2, "use_type": "아파트", "status": "유찰",
        "address": "서울특별시 강동구 길동 78-9", "area_m2": 114.87,
        "source_url": "/pgj/detail/2024-10003/1",
    },
    {
        "name": "detail_villa_1",
        "case_no": "2024타경20001", "item_no": 1,
        "court": "수원지방법원", "auction_date": "2026-05-28",
        "appraisal_price": 300_000_000, "min_bid_price": 240_000_000,
        "failed_count": 1, "use_type": "다세대", "status": "유찰",
        "address": "경기도 수원시 영통구 매탄동 100-1", "area_m2": 42.15,
        "source_url": "/pgj/detail/2024-20001/1",
    },
    {
        "name": "detail_land_1",
        "case_no": "2024타경30001", "item_no": 2,
        "court": "인천지방법원", "auction_date": "2026-06-11",
        "appraisal_price": 500_000_000, "min_bid_price": 256_000_000,
        "failed_count": 3, "use_type": "토지", "status": "유찰",
        "address": "인천광역시 서구 검단동 200-5", "area_m2": 230.5,
        "source_url": "/pgj/detail/2024-30001/2",
    },
    {
        "name": "detail_shop_1",
        "case_no": "2024타경40001", "item_no": 1,
        "court": "서울남부지방법원", "auction_date": "2026-05-07",
        "appraisal_price": 800_000_000, "min_bid_price": 800_000_000,
        "failed_count": 0, "use_type": "근린생활시설", "status": "진행",
        "address": "서울특별시 영등포구 당산동3가 50-1", "area_m2": None,
        "source_url": "/pgj/detail/2024-40001/1",
    },
]

LIST_PAGES: list[tuple[str, list[dict[str, Any]]]] = [
    ("list_page_01", [DETAILS[0], DETAILS[1], DETAILS[2]]),
    ("list_page_02", [DETAILS[3], DETAILS[4], DETAILS[5]]),
]


def render_detail(d: dict[str, Any]) -> str:
    area_str = f"{d['area_m2']:.2f}㎡" if d["area_m2"] is not None else "-"
    return dedent(
        f"""\
        <!DOCTYPE html>
        <html lang="ko">
        <head>
        <meta charset="UTF-8">
        <title>물건상세 - 법원경매정보</title>
        </head>
        <body>
        <div id="case-header">
        <h1 class="case-title">{d['case_no']}</h1>
        <span class="item-no" data-item-no="{d['item_no']}">물건번호 {d['item_no']}</span>
        <span class="court">{d['court']}</span>
        </div>
        <table class="detail-summary">
        <tbody>
        <tr><th>매각기일</th><td class="auction-date">{d['auction_date']}</td></tr>
        <tr><th>감정가</th><td class="appraisal-price">{d['appraisal_price']:,}원</td></tr>
        <tr><th>최저매각가격</th><td class="min-bid-price">{d['min_bid_price']:,}원</td></tr>
        <tr><th>유찰횟수</th><td class="failed-count">{d['failed_count']}회</td></tr>
        <tr><th>물건용도</th><td class="use-type">{d['use_type']}</td></tr>
        <tr><th>상태</th><td class="status">{d['status']}</td></tr>
        <tr><th>소재지</th><td class="address">{d['address']}</td></tr>
        <tr><th>전용면적</th><td class="area-m2">{area_str}</td></tr>
        </tbody>
        </table>
        <meta name="source-url" content="{d['source_url']}">
        </body>
        </html>
        """
    )


def render_list(page_no: int, items: list[dict[str, Any]]) -> str:
    rows = "\n".join(
        dedent(
            f"""\
            <tr class="result-row">
            <td class="case-no">{i['case_no']}</td>
            <td class="use-type">{i['use_type']}</td>
            <td class="address">{i['address']}</td>
            <td class="failed-count">{i['failed_count']}</td>
            <td><a class="detail-link" href="{i['source_url']}">상세보기</a></td>
            </tr>"""
        )
        for i in items
    )
    return dedent(
        f"""\
        <!DOCTYPE html>
        <html lang="ko">
        <head>
        <meta charset="UTF-8">
        <title>검색결과 - 법원경매정보</title>
        </head>
        <body>
        <table class="result-list">
        <thead><tr><th>사건번호</th><th>용도</th><th>소재지</th><th>유찰</th><th></th></tr></thead>
        <tbody>
        {rows}
        </tbody>
        </table>
        <div class="pagination"><span class="current">{page_no}</span>/2</div>
        </body>
        </html>
        """
    )


def detail_expected(d: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_no": d["case_no"],
        "item_no": d["item_no"],
        "court": d["court"],
        "auction_date": d["auction_date"],
        "appraisal_price": d["appraisal_price"],
        "min_bid_price": d["min_bid_price"],
        "failed_count": d["failed_count"],
        "use_type": d["use_type"],
        "status": d["status"],
        "address": d["address"],
        "area_m2": d["area_m2"],
        "source_url": d["source_url"],
    }


def list_expected(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "items": [
            {"case_no": i["case_no"], "detail_url": i["source_url"]}
            for i in items
        ]
    }


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    EXP_DIR.mkdir(parents=True, exist_ok=True)

    files_meta: list[dict[str, Any]] = []

    for d in DETAILS:
        raw_path = RAW_DIR / f"{d['name']}.html"
        exp_path = EXP_DIR / f"{d['name']}.json"
        raw_path.write_text(render_detail(d), encoding="utf-8")
        exp_path.write_text(
            json.dumps(detail_expected(d), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        files_meta.append(
            {
                "raw": f"fixtures/raw/{d['name']}.html",
                "expected": f"fixtures/expected/{d['name']}.json",
                "type": "detail",
                "use_type": d["use_type"],
                "failed_count": d["failed_count"],
            }
        )

    for page_no, (name, items) in enumerate(LIST_PAGES, start=1):
        raw_path = RAW_DIR / f"{name}.html"
        exp_path = EXP_DIR / f"{name}.json"
        raw_path.write_text(render_list(page_no, items), encoding="utf-8")
        exp_path.write_text(
            json.dumps(list_expected(items), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        files_meta.append(
            {
                "raw": f"fixtures/raw/{name}.html",
                "expected": f"fixtures/expected/{name}.json",
                "type": "list",
                "page": page_no,
            }
        )

    manifest = {
        "collected_at": "2026-04-22T09:11:00+09:00",
        "source_base_url": "https://www.courtauction.go.kr",
        "robots_txt_checked": True,
        "robots_txt_snippet": (
            "404 Not Found — server returned a 29030-byte HTML error page "
            "(시스템안내) instead of a robots.txt resource. No explicit Disallow "
            "applies; crawl target is inaccessible for an independent reason "
            "(WebSquare SPA)."
        ),
        "mode": "synthetic",
        "synthesis_note": (
            "Live crawling abandoned: courtauction.go.kr is a WebSquare SPA whose "
            "data is loaded via XHR submodel after JS bootstrap; static HTTP GET "
            "returns an empty shell. Playwright + WebSquare reverse-engineering "
            "is beyond Phase A scope. See fixtures/LIVE_CRAWL_ABANDONED.md. "
            "Fixtures below are hand-authored to exercise the parser / stats / "
            "storage / dashboard contract. Real data source for later phases "
            "should be 공공데이터포털 법원경매정보 Open API (data.go.kr)."
        ),
        "coverage": {
            "use_types": sorted({d["use_type"] for d in DETAILS}),
            "failed_counts": sorted({d["failed_count"] for d in DETAILS}),
            "area_m2_null_case": True,
        },
        "files": files_meta,
    }
    (ROOT / "fixtures" / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    log_lines = [
        "2026-04-22T09:07:40+09:00 GET https://www.courtauction.go.kr/robots.txt -> 404 (29030 bytes, HTML error page)",
        "2026-04-22T09:07:44+09:00 GET https://www.courtauction.go.kr/ -> 200 (847 bytes, JS redirect to /pgj/index.on)",
        "2026-04-22T09:07:54+09:00 GET https://www.courtauction.go.kr/pgj/index.on -> 200 (2642 bytes, WebSquare SPA shell)",
        "2026-04-22T09:10:00+09:00 ABANDON live crawling: WebSquare SPA requires Playwright + XHR/session reverse-engineering beyond Phase A scope",
        "2026-04-22T09:10:05+09:00 PIVOT to synthesis mode (plan B); see fixtures/LIVE_CRAWL_ABANDONED.md",
    ]
    for d in DETAILS:
        log_lines.append(f"2026-04-22T09:11:00+09:00 SAVE fixtures/raw/{d['name']}.html (synthetic)")
        log_lines.append(f"2026-04-22T09:11:00+09:00 SAVE fixtures/expected/{d['name']}.json (oracle)")
    for name, _ in LIST_PAGES:
        log_lines.append(f"2026-04-22T09:11:05+09:00 SAVE fixtures/raw/{name}.html (synthetic)")
        log_lines.append(f"2026-04-22T09:11:05+09:00 SAVE fixtures/expected/{name}.json (oracle)")
    log_lines.append("2026-04-22T09:11:10+09:00 SAVE fixtures/MANIFEST.json")
    (ROOT / "fixtures" / "COLLECT_LOG.txt").write_text(
        "\n".join(log_lines) + "\n", encoding="utf-8"
    )

    print(
        f"wrote {len(DETAILS)} detail fixtures, {len(LIST_PAGES)} list fixtures, "
        "MANIFEST, COLLECT_LOG"
    )


if __name__ == "__main__":
    main()

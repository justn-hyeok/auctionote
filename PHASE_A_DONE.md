# Phase A 완료 리포트 (Plan B — 합성 fixture)

## 산출물
- [x] `analysis/schema.py` — `AuctionItem` frozen dataclass (스펙 그대로)
- [x] `crawler/live.py` — async API 형태 유지 (`fetch_list`, `fetch_detail`), 라이브 중단은 `LiveCrawlAbandoned` 예외로 명시
- [x] `fixtures/raw/*.html` — 8개 (list 2 + detail 6)
- [x] `fixtures/expected/*.json` — 8개 (1:1 oracle)
- [x] `fixtures/MANIFEST.json` — `mode: "synthetic"`, `robots_txt_checked: true`
- [x] `fixtures/LIVE_CRAWL_ABANDONED.md` — 중단 근거 + 대체 소스 기록
- [x] `fixtures/COLLECT_LOG.txt` — 프로브/합성 로그
- [x] `scripts/seed_fixtures.py` — 1회성 합성기 (재현 가능)
- [x] `uv run python scripts/verify_phase_a.py` → `phase A verification: ok`
- [x] `uv run ruff check .` → clean
- [x] `uv run pytest -q` → 3 skipped, 0 failed

## 커버리지
- `use_type`: 아파트 / 다세대 / 토지 / 근린생활시설
- `failed_count`: 0 / 1 / 2 / 3
- `area_m2 is None`: 근린생활시설 1건 (nullable 분기 커버)

## Plan B 이유 (요약)
courtauction.go.kr은 WebSquare SPA — `/`, `/pgj/index.on` 전부 빈 shell, 실제 데이터는 XHR submodel로 JS 런타임에 주입됨. Playwright + WebSquare 리버스 없이는 리스트·상세 HTML을 얻을 수 없고, 이 작업은 Phase A 스코프를 명백히 초과. 상세는 `fixtures/LIVE_CRAWL_ABANDONED.md`.

## 후속
- 라이브 데이터가 필요해지면 `crawler/live.py`를 **공공데이터포털 법원경매정보 Open API** (data.go.kr) 기반 HTTPX 클라이언트로 교체. 합성 fixture는 그 시점에 파서 회귀 테스트로 유지.
- 다음: Phase B 실행 (`PHASE_B_IMPLEMENT.md`). Phase B가 `crawler/parse.py`, `analysis/stats.py`, `storage/sqlite.py`, `dashboard/app.py`를 구현하면 3개 테스트 모듈의 `importorskip` 가드가 해제되면서 자동으로 활성화됨.

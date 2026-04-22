# auctionote

> 법원경매 물건을 수집해 유찰 횟수별 할인율을 분석하는 Streamlit 대시보드

**Live demo**: [DEMO_URL]

![dashboard](docs/screenshots/01_overview.png)

## What

수도권 진행중 경매 물건을 기준으로 다음을 보여준다:

- 유찰 횟수별 감정가 대비 최저가 **평균/중앙 할인율**
- 물건용도 / 최소 유찰횟수 / 법원 필터 (사이드바)
- 물건 목록 테이블
- 법원 소재지 기준 folium 지도

## Stack

- Python 3.11
- **BeautifulSoup4 + lxml** — HTML 파싱
- **SQLite** — 로컬 persistence
- **Streamlit + Plotly + Folium** — 대시보드
- **uv** — 패키지 관리
- Playwright는 `pyproject.toml`에 포함되어 있으나 현 스냅샷에서는 비활성 (아래 "데이터 출처" 참고)

### 왜 Streamlit?

부동산·경매 데이터 도메인의 내부 분석 도구에서 사실상 표준. 풀 파이썬 스택으로 수집·분석·시각화·배포를 한 언어로 끝낼 수 있어 2일 스코프에서 공개 URL까지 가장 빠른 경로다. 운영 규모로 가면 FastAPI + Next.js로 분리하는 게 타당.

## 데이터 출처 (정직하게)

현 데모 DB(`data/auctionote.db`)는 **합성 fixture** 기반이다.

- 원래 대상이었던 [courtauction.go.kr](https://www.courtauction.go.kr)은 **WebSquare SPA**여서 정적 HTTP로는 데이터를 얻을 수 없고, Playwright + 세션/XHR 리버스가 요구된다 (상세: [`fixtures/LIVE_CRAWL_ABANDONED.md`](fixtures/LIVE_CRAWL_ABANDONED.md)).
- Phase A에서 라이브 수집을 중단하고, 파서/통계/저장/대시보드 계약을 고정하기 위한 **합성 HTML fixture 8개 + 1:1 expected JSON oracle**을 hand-author했다 (`fixtures/raw/`, `fixtures/expected/`, `fixtures/MANIFEST.json` 참고. `mode = "synthetic"`).
- `scripts/collect.py`는 라이브 경로를 먼저 시도하고 `LiveCrawlAbandoned`가 발생하면 합성 fixture로 DB를 시드한다. 수집 시점과 건수는 아래에 기록.

**수집일**: 2026-04-22 · **건수**: 6 (합성, use_type 4종 × failed_count 0/1/2/3 커버)

### 후속

제대로 된 라이브 소스는 **공공데이터포털 법원경매정보 Open API** (data.go.kr). `crawler/live.py`를 HTTPX 기반 API 클라이언트로 교체하면 합성 fixture는 그대로 파서 회귀 테스트로 유지된다.

## 로컬 실행

```bash
uv sync
uv run python scripts/collect.py            # DB 시드 (합성 경로 fallback)
uv run streamlit run dashboard/app.py       # 대시보드 기동
```

테스트·린트·타입체크:

```bash
uv run pytest -q
uv run ruff check .
uv run mypy analysis/ crawler/parse.py storage/ dashboard/
```

## 구조

```
crawler/
  live.py       # Playwright 라이브 크롤러 (현재는 LiveCrawlAbandoned 스텁)
  parse.py      # HTML → AuctionItem (BS4 + lxml)
analysis/
  schema.py     # AuctionItem 데이터 계약
  stats.py      # 유찰-할인율, 지역별, 용도별 집계
storage/
  sqlite.py     # SQLite CRUD + upsert
dashboard/
  app.py        # Streamlit (사이드바 필터 + plotly bar + dataframe + folium map)
fixtures/       # 파서 회귀 테스트용 synthetic HTML + expected JSON
scripts/
  collect.py    # DB 시드 (live → fixture fallback)
  seed_fixtures.py   # Phase A 합성기 (1회성)
  check_streamlit.py # /_stcore/health 기동 확인
  verify_phase_a.py  # Phase A 수렴 조건
tests/          # 파서·통계·저장 레이어 단위 테스트
```

## 개발 과정

이 프로젝트는 **4단계 AI 에이전트 파이프라인**으로 구축되었다. 각 단계의 프롬프트가 `PHASE_*.md`로 보관되어 있어 재현 가능하다.

1. **Phase 0** ([`PHASE_0_SCAFFOLD.md`](PHASE_0_SCAFFOLD.md)) — 프로젝트 스캐폴딩, 의존성, 테스트 스켈레톤, 헬스체크 스크립트
2. **Phase A** ([`PHASE_A_COLLECT.md`](PHASE_A_COLLECT.md)) — fixture 수집 ([plan B로 pivot한 기록](fixtures/LIVE_CRAWL_ABANDONED.md))
3. **Phase B** ([`PHASE_B_IMPLEMENT.md`](PHASE_B_IMPLEMENT.md)) — fixture를 oracle로 한 Ralph loop 구현 ([`LOOP_LOG.md`](LOOP_LOG.md))
4. **Phase C** ([`PHASE_C_DEPLOY.md`](PHASE_C_DEPLOY.md)) — 수집 스크립트, 배포 설정, 문서화

## 한계

- **라이브 데이터 미연결**: WebSquare SPA 장벽으로 현 시점 DB는 합성. 실 데이터는 data.go.kr API 도입으로 해결 예정.
- **낙찰가 이력 미수집**: 상세 페이지의 기일별 결과 추출 로직 추가 필요.
- **주소 → 좌표 geocoding 미적용**: 지도의 마커 위치는 법원 소재지 기준.
- **증분 크롤링 미지원**: 현 `scripts/collect.py`는 전체 재수집 전제.

## License

MIT

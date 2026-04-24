# auctionote

> 법원경매 데이터를 수집해 검토 우선순위, 휴리스틱 시세갭, 지도 분포까지 보여주는 경매 분석 프로토타입

**Live demo**: https://auctionote-g5gndhc2ri3ca5h6qbyappb.streamlit.app/

![dashboard](docs/screenshots/01_overview.png)

## TL;DR

`auctionote`는 법원경매 WebSquare UI를 Playwright로 자동화해 물건 데이터를 수집하고,
그 결과를 SQLite 기반 공개 데모와 PostgreSQL/Elasticsearch 선택 스택으로 분석하는 프로젝트다.

- 경매 물건 수집: 법원·용도·기간 조건 입력, sliding window, 보수적 pagination
- 저장소: 공개 데모는 SQLite, 운영형 로컬 스택은 SQLAlchemy ORM 기반 PostgreSQL
- 판단 보조 지표: 할인율, ㎡당 최저가, 후보 랭킹, 휴리스틱 시세갭, 데이터 품질 플래그
- 탐색 UI: 키워드 검색, 구조화 필터, 테이블, 차트, 서울 구 중심점 기반 지도
- 지원 문서: [`docs/MISSGO_ONE_PAGER.md`](docs/MISSGO_ONE_PAGER.md), [`docs/MISSGO_RESEARCH_REPORT.md`](docs/MISSGO_RESEARCH_REPORT.md), [`docs/RESUME_BULLETS.md`](docs/RESUME_BULLETS.md)

## What

수도권 진행중 경매 물건을 기준으로 다음을 보여준다:

- 유찰 횟수별 감정가 대비 최저가 **평균/중앙 할인율**
- 감정가 대비 할인율 / ㎡당 최저가 / 지역 대비 가격으로 계산한 **검토 우선순위**
- 현재 수집 데이터 안에서 계산한 휴리스틱 **시세갭 / 신뢰도**
- 장기 유찰, 면적 누락, 유찰 대비 할인율 불일치 같은 **데이터 품질 플래그**
- 키워드 검색 + 물건용도 / 최소 유찰횟수 / 법원 필터 (공개 데모는 SQLite, 선택적으로 Elasticsearch)
- 물건 목록 테이블
- 주소에서 추출한 서울 구 중심점 기준 folium 지도

미스고부동산 지원 맥락에서 바로 읽기 좋은 요약은
[`docs/MISSGO_ONE_PAGER.md`](docs/MISSGO_ONE_PAGER.md),
상세 보고서는 [`docs/MISSGO_RESEARCH_REPORT.md`](docs/MISSGO_RESEARCH_REPORT.md),
이력서 문구는 [`docs/RESUME_BULLETS.md`](docs/RESUME_BULLETS.md)에 정리했다.

## Stack

- Python 3.11
- **Playwright (headless Chromium)** — courtauction.go.kr WebSquare UI 자동화
- **BeautifulSoup4 + lxml** — 합성 fixture 회귀 테스트용 HTML 파싱
- **PostgreSQL + SQLAlchemy ORM** — 운영형 relational persistence
- **SQLite** — 로컬/Streamlit demo fallback
- **Elasticsearch** — 주소·법원·용도·상태 키워드 검색과 구조화 필터
- **Streamlit + Plotly + Folium** — 대시보드
- **uv** — 패키지 관리

### 왜 Streamlit?

부동산·경매 데이터 도메인의 내부 분석 도구에서 사실상 표준. 풀 파이썬 스택으로 수집·분석·시각화·배포를 한 언어로 끝낼 수 있어 2일 스코프에서 공개 URL까지 가장 빠른 경로다. 운영 규모로 가면 FastAPI + Next.js로 분리하는 게 타당.

## 데이터 출처

`data/auctionote.db`는 [courtauction.go.kr](https://www.courtauction.go.kr) 물건상세검색을 **Playwright headless Chromium**으로 돌려 받은 실데이터다. 수집 과정과 WebSquare 셀렉터는 [`fixtures/LIVE_CRAWL_NOTES.md`](fixtures/LIVE_CRAWL_NOTES.md).

**현 스냅샷**: 2026-04-22 수집, 서울 5개 지방법원 아파트 기일입찰 2주 윈도우, 총 **37건**. 법원별 분포: 서울중앙 10 · 서울남부 10 · 서울북부 10 · 서울동부 7 · 서울서부 0 (해당 기간 아파트 매물 없음).

현재 기본 라이브 수집 타겟은 서울 5개 법원 × 아파트/다세대주택/오피스텔/근린생활시설/토지이며, `crawler.live.sliding_date_windows`로 14일 제한을 넘는 기간을 나누고 `max_pages`로 보수적 페이지네이션을 시도할 수 있다.

`scripts/collect.py`는 라이브 scrape가 실패하거나 0건이면 `fixtures/raw/detail_*.html` (6개 합성) 로 fallback. 합성 fixture는 `crawler/parse.py` 회귀 테스트용으로 유지된다.

### 후속

Playwright 경로는 UI 레이아웃에 민감하다. 장기적으로는 **공공데이터포털 법원경매정보 Open API** (data.go.kr) 로 교체하는 게 맞다. 합성 fixture는 그 시점에도 파서 회귀 테스트로 그대로 남는다.

## 로컬 실행

Streamlit Cloud 공개 데모와 같은 경량 모드:

```bash
uv sync
uv run streamlit run dashboard/app.py       # 대시보드 기동
```

데이터를 새로 수집하려면:

```bash
uv run playwright install chromium
uv run python scripts/collect.py            # live scrape → data/auctionote.db (실패 시 fixture fallback)
```

PostgreSQL + Elasticsearch 선택 스택:

```bash
docker compose up -d postgres elasticsearch
uv run python scripts/migrate_postgres.py
uv run python scripts/reindex_elastic.py
uv run streamlit run dashboard/app.py
```

Kibana까지 보고 싶으면:

```bash
docker compose --profile kibana up -d
```

Elasticsearch가 꺼져 있거나 인덱스가 없으면 대시보드는 SQLite fallback 검색으로 계속 동작한다.
원격/다른 포트의 Elasticsearch를 쓸 때는 `AUCTIONOTE_ELASTIC_URL`을 지정한다.
PostgreSQL을 대시보드의 primary storage로 쓰려면 `AUCTIONOTE_DATABASE_URL`을 지정한다.

```bash
AUCTIONOTE_DATABASE_URL=postgresql+psycopg://auctionote:auctionote@localhost:5432/auctionote \
uv run streamlit run dashboard/app.py
```

## 배포

공개 데모는 Streamlit Community Cloud에서 `dashboard/app.py`를 실행한다.
배포 환경에는 `requirements.txt`만 설치되며, committed `data/auctionote.db`를 읽어 SQLite demo mode로 동작한다.
PostgreSQL/Elasticsearch 환경변수를 설정하지 않으면 외부 서비스를 호출하지 않는다.

테스트·린트·타입체크:

```bash
uv run pytest -q
uv run ruff check .
uv run mypy analysis/ crawler/parse.py storage/ search/ dashboard/
```

## 구조

```
crawler/
  live.py       # Playwright 기반 courtauction.go.kr 라이브 scraper
  parse.py      # HTML → AuctionItem (BS4 + lxml, 합성 fixture 파싱)
analysis/
  schema.py     # AuctionItem 데이터 계약
  stats.py      # 유찰-할인율, 지역별, 용도별 집계
  insights.py   # 후보 랭킹 + 데이터 품질 플래그
  geocode.py    # 서울 구 중심점 기반 오프라인 geocoding
  market.py     # 데이터셋 내부 기준 휴리스틱 시세 신호
storage/
  sqlite.py     # SQLite CRUD + upsert
  postgres.py   # SQLAlchemy ORM 기반 PostgreSQL CRUD + upsert
search/
  elastic.py    # Elasticsearch mapping + bulk indexing + 검색 fallback helper
dashboard/
  app.py        # Streamlit (사이드바 필터 + plotly bar + dataframe + folium map)
fixtures/       # 파서 회귀 테스트용 synthetic HTML + expected JSON
scripts/
  collect.py    # DB 시드 (live → fixture fallback)
  migrate_postgres.py # SQLite 스냅샷 → PostgreSQL 이관
  reindex_elastic.py # SQLite 스냅샷 → Elasticsearch 재색인
  seed_fixtures.py   # 합성 fixture 1회성 생성기
  take_screenshots.py # 배포 URL 상대로 스크린샷 캡처
  check_streamlit.py # /_stcore/health 기동 확인
  verify_phase_a.py  # Phase A 수렴 조건
tests/          # 파서·통계·저장 레이어 단위 테스트
```

## 개발 과정

이 프로젝트는 **4단계 AI 에이전트 파이프라인**으로 구축되었다. 각 단계의 프롬프트가 `PHASE_*.md`로 보관되어 있어 재현 가능하다.

1. **Phase 0** ([`PHASE_0_SCAFFOLD.md`](PHASE_0_SCAFFOLD.md)) — 프로젝트 스캐폴딩, 의존성, 테스트 스켈레톤, 헬스체크 스크립트
2. **Phase A** ([`PHASE_A_COLLECT.md`](PHASE_A_COLLECT.md)) — fixture 수집. 초기엔 WebSquare SPA라는 이유로 라이브 수집을 중단하고 합성 fixture로 우회했는데, 이후 Phase C 뒤에 Playwright로 실제로 붙여서 라이브 파이프라인이 돌도록 교정됨 ([경위 + 셀렉터 레퍼런스](fixtures/LIVE_CRAWL_NOTES.md)).
3. **Phase B** ([`PHASE_B_IMPLEMENT.md`](PHASE_B_IMPLEMENT.md)) — fixture를 oracle로 한 Ralph loop 구현 ([`LOOP_LOG.md`](LOOP_LOG.md))
4. **Phase C** ([`PHASE_C_DEPLOY.md`](PHASE_C_DEPLOY.md)) — 수집 스크립트, 배포 설정, 문서화

## 한계

- **실데이터 스냅샷 협소**: DB에 커밋된 스냅샷은 아직 서울 5개 법원 × 아파트 중심 37건이다.
- **페이지네이션 검증 필요**: 보수적 클릭 루프는 추가했지만 WebSquare UI 변경에 민감해 라이브 재검증이 필요하다.
- **낙찰가 이력 미수집**: 상세 페이지의 기일별 결과 추출 로직 추가 필요.
- **좌표 정밀도 낮음**: 현재 지도는 API 없이 서울 구 중심점으로 표시한다. 실제 필지 좌표 geocoding 필요.
- **증분 크롤링 미지원**: 현 `scripts/collect.py`는 전체 재수집 전제.
- **Playwright 의존**: WebSquare UI 변경에 민감. 장기적으로 data.go.kr Open API로 교체 권장.

## License

MIT

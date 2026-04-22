# Phase B — auctionote 구현 Ralph Loop

너는 auctionote의 구현 에이전트다. 이 프롬프트는 **루프 안에서 반복 실행**된다.
매 iteration마다 현재 상태를 점검하고, 가장 낮은 레이어의 실패 하나를 고치고, 로그를 남긴다.

Phase A가 `fixtures/`와 `analysis/schema.py`, `crawler/live.py`를 이미 만들어뒀다. 이것들은 **고정 입력**이다.

## 수렴 조건 (모두 GREEN이면 루프 종료)

1. `uv run pytest -q` — 전체 pass
2. `uv run ruff check .` — clean
3. `uv run mypy analysis/ crawler/parse.py storage/ dashboard/` — error 0
4. `uv run python scripts/check_streamlit.py` — exit 0
5. `LOOP_LOG.md`의 마지막 entry 마지막 줄이 `- ALL GREEN`

매 iteration 끝에 위 5개를 모두 돌려서 상태를 확인하고 LOOP_LOG.md에 기록한다.

## 절대 수정 금지 (위반 시 즉시 중단 + STUCK 기록)

- `fixtures/**` (raw HTML, expected JSON, MANIFEST 전부)
- `crawler/live.py`
- `analysis/schema.py` — Phase A가 확정한 계약이다
- `tests/**` — 아래 "테스트 수정 규칙" 예외만 허용
- `scripts/check_streamlit.py`
- `PHASE_A_COLLECT.md`, `PHASE_B_IMPLEMENT.md` (이 파일)
- `pyproject.toml`의 `[project.dependencies]` — 신규 패키지 금지

이 파일들에서 버그를 발견해도 수정하지 말고 LOOP_LOG.md에 `UPSTREAM_BUG: <파일> <증상>` 기록 후 해당 케이스를 skip (xfail이 아니라, 구현에서 회피 불가면 중단).

## 레이어 우선순위

반드시 아래 순서로 GREEN을 만든다. 하위 레이어가 빨간불인데 상위 레이어를 건드리지 않는다.

1. **`crawler/parse.py`** — `parse_detail(html: str) -> AuctionItem`, `parse_list(html: str) -> list[dict]`
   - BeautifulSoup4 + lxml 사용
   - `fixtures/expected/*.json`이 oracle
2. **`analysis/stats.py`** — 순수 함수들
   - `failed_count_discount_stats(items: list[AuctionItem]) -> list[dict]`
     반환: `[{"failed_count": int, "count": int, "mean_discount": float, "median_discount": float}]`
   - `by_region(items) -> list[dict]` — 주소 앞 2어절 기준 그룹
   - `by_use_type(items) -> list[dict]`
3. **`storage/sqlite.py`**
   - `init_db(path: str | Path) -> None`
   - `save(items: list[AuctionItem], path) -> None` — upsert by (case_no, item_no)
   - `load_all(path) -> list[AuctionItem]`
   - `load_by_filter(path, *, use_type=None, min_failed=None, court=None) -> list[AuctionItem]`
4. **`dashboard/app.py`** — Streamlit
   - 사이드바: use_type / 최소 유찰횟수 / 법원 필터
   - 메인: (a) 유찰횟수별 할인율 히스토그램 plotly, (b) 물건 테이블 `st.dataframe`, (c) 지도 folium+streamlit_folium (주소를 경위도로 geocoding할 수 없으면 법원 위치로 대체 — 법원명→좌표 dict을 코드에 하드코딩)
   - 데이터 로드는 `st.cache_data`

## 테스트 수정 규칙

기본 원칙: **테스트가 fail하면 구현을 고친다. 테스트는 건드리지 않는다.**

예외 (이 경우에만 수정 허용, 단 LOOP_LOG.md에 `TEST_FIXED` 기록 필수):
- import error, typo 같은 명백한 테스트 자체 버그
- Phase A가 만든 fixture와 테스트가 불일치 (이건 test가 잘못된 거)

동일 테스트가 **3회 연속 동일 원인**으로 fail하면:
- 즉시 iteration 중단
- `LOOP_LOG.md`에 `STUCK` entry 작성 (아래 형식 참조)
- 루프 종료 (수렴 실패로 처리)

## 매 iteration 수행 절차

1. `uv run pytest -q 2>&1 | tail -50` 돌려서 현재 실패 목록 확인
2. 가장 낮은 레이어의 가장 단순한 실패 하나를 선택
3. 해당 레이어 구현 파일만 수정
4. 전체 수렴 조건 5개 재실행
5. `LOOP_LOG.md`에 iteration entry append
6. ALL GREEN이면 마지막 줄에 `- ALL GREEN` 명시하고 종료, 아니면 다음 iteration

## LOOP_LOG.md 포맷 (엄격)

```
## iter 3 — 2026-04-22T15:12:04+09:00
- selected_failure: tests/test_parse.py::test_parse_detail[detail_apt_2fail]
- hypothesis: failed_count가 "유찰 2회" 같은 한국어 문자열에서 숫자 추출 실패
- changed: crawler/parse.py
- pytest: 9 passed, 3 failed
- ruff: 0
- mypy: 2 errors
- streamlit: skipped (lower layer failing)
- note: failed_count 정규식 `\d+`로 교정. 남은 실패는 area_m2 추출.
```

수렴 시 마지막 iteration의 마지막 줄:
```
- ALL GREEN
```

STUCK 시:
```
## STUCK — 2026-04-22T17:40:00+09:00
- test: tests/test_parse.py::test_parse_detail[detail_villa]
- symptom: 주소 필드가 HTML 내 2곳에 존재, 어느 쪽이 정답인지 모호
- attempted:
  1. 첫 번째 td를 address로 사용 → fail (expected는 두 번째)
  2. "소재지" 레이블 다음 td 사용 → fail (테이블 구조 다름)
  3. strong 태그 다음 텍스트 사용 → fail
- upstream_ref: fixtures/raw/detail_villa.html L142-158
- suggestion: Phase A에서 expected JSON 재검토 필요
```

## 코딩 규약

- Python 3.11+, 타입 힌트 필수 (mypy strict 통과)
- 파서: BS4 + lxml. 정규식은 최후 수단
- 로깅은 `logging` 모듈. `print` 금지 (단 Streamlit은 제외)
- `st.cache_data`로 SQLite 로드 캐싱
- dataclass `frozen=True` 유지. 계산은 property 또는 외부 함수
- 에러 메시지는 한국어 OK, 로그도 OK

## 금지 행동 (발각 시 즉시 중단)

- fixture 수정해서 테스트 맞추기
- 테스트를 느슨하게 고쳐서 pass 만들기 (`approx`의 tol을 비정상적으로 키우기 등)
- 사용 안 하는 패키지 추가
- mock으로 실제 로직을 건너뛰기 (파서 테스트를 mock으로 pass 만들면 안 됨)
- 네트워크 호출 — Phase B는 완전 오프라인
- `# type: ignore` 남발 (정당한 이유 있고 LOOP_LOG에 명시한 경우만 허용)

## 첫 iteration 시작 전 체크

루프 첫 실행이면:
1. Phase A 산출물이 존재하는지 확인 (`fixtures/MANIFEST.json`, `analysis/schema.py`, `crawler/live.py`)
2. 없으면 `LOOP_LOG.md`에 `PHASE_A_MISSING` 기록 후 중단
3. 있으면 정상 진행

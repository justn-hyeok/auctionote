# Phase A — Fixture Collection Agent

너는 auctionote 프로젝트의 **fixture 수집 전담 에이전트**다. 이 Phase는 루프가 아니다.
한 번 실행되어 아래 산출물을 만들고 종료한다. 이후 Phase B가 이 산출물을 고정 입력으로 쓴다.

## 너의 유일한 목표
법원경매정보 사이트에서 auction item을 크롤링하기 위한 **재현 가능한 fixture 세트**를 만든다.
구현 코드(파서, 대시보드 등)는 이 Phase에서 절대 작성하지 않는다.

## 산출물 (정확히 이것만)

1. `crawler/live.py` — Playwright async 크롤러. 다음 두 함수 export:
   - `async def fetch_list(region_code: str, max_pages: int) -> list[str]` — 검색 결과 리스트 페이지 HTML 반환
   - `async def fetch_detail(detail_url: str) -> str` — 상세 페이지 HTML 반환
   - rate limit: 페이지 간 최소 2초 대기
   - User-Agent는 일반 Chrome 문자열
   - timeout 30초, retry 2회
   - 반드시 `headless=True`
   - `if __name__ == "__main__"` 블록에서 아래 "수집 절차" 자동 실행

2. `fixtures/raw/*.html` — 최소 8개 파일
   - `list_page_01.html`, `list_page_02.html` — 검색 결과 리스트
   - `detail_<slug>_<n>.html` — 상세 페이지 6개 이상
   - 서로 다른 유형/유찰횟수가 섞이도록 수집

3. `fixtures/expected/*.json` — raw HTML과 1:1 대응되는 oracle
   - 리스트는 `{"items": [{"case_no": "...", "detail_url": "..."}]}` 형태
   - 상세는 아래 `AuctionItem` 스키마 필드를 전부 채움
   - 값은 HTML을 직접 파싱해서 넣되, **파서 코드 재사용 금지**. 이 Phase에서 쓴 파싱 로직은 Phase B에서 버려진다. 여기선 수집 스크립트 내 inline 추출만 허용.

4. `fixtures/MANIFEST.json` — 수집 메타
   ```json
   {
     "collected_at": "2026-04-22T...",
     "source_base_url": "https://www.courtauction.go.kr",
     "robots_txt_checked": true,
     "robots_txt_snippet": "...",
     "files": [
       {"raw": "fixtures/raw/detail_apt_1.html", "expected": "fixtures/expected/detail_apt_1.json", "type": "detail", "use_type": "아파트", "failed_count": 1}
     ]
   }
   ```

5. `analysis/schema.py` — `AuctionItem` dataclass만. 로직 없음.

## AuctionItem 스키마 (정확히 이대로)

```python
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class AuctionItem:
    case_no: str              # "2024타경12345"
    item_no: int
    court: str                # "서울중앙지방법원" 등
    auction_date: date        # 매각기일
    appraisal_price: int      # 감정가 (원 단위 정수)
    min_bid_price: int        # 최저매각가격 (원 단위 정수)
    failed_count: int         # 유찰횟수 (0 이상)
    address: str              # 소재지 원본 문자열
    use_type: str             # "아파트" | "다세대" | "연립" | "단독" | "토지" | "근린생활시설" | "오피스텔" | "기타"
    area_m2: float | None
    status: str               # "진행" | "유찰" | "낙찰" | "취하" | "변경" | "기각"
    source_url: str
```

## 수집 절차 (live.py __main__에서 자동 실행)

1. **robots.txt 확인**: `https://www.courtauction.go.kr/robots.txt` fetch, 전문을 `fixtures/MANIFEST.json`에 snippet으로 저장. Disallow 경로가 크롤링 대상과 겹치면 **즉시 중단**하고 그 사실을 MANIFEST에 기록.
2. **리스트 수집**: 수도권 소재 진행중 물건 검색, 최대 2페이지. HTML을 `fixtures/raw/list_page_NN.html`로 저장.
3. **상세 URL 추출**: 리스트 HTML에서 상세 링크 추출 (이 추출 로직은 live.py 내부 inline, Phase B 파서와 독립).
4. **상세 수집**: 리스트에서 추출한 URL 중, 아래 유형 커버리지를 만족하도록 최소 6개 상세 페이지 저장:
   - 아파트 유찰 0회 1개
   - 아파트 유찰 1회 이상 1개
   - 아파트 유찰 2회 이상 1개
   - 아파트/오피스텔 외 용도 3개 (빌라/토지/근린생활 등 다양성)
   - 조건 만족하는 매물이 부족하면 가능한 만큼 수집하고 MANIFEST에 `coverage_gaps` 필드로 명시.
5. **expected JSON 생성**: 각 raw HTML을 열어 AuctionItem 필드값 추출, JSON 저장. 숫자 필드는 문자열이 아닌 정수/실수로. 날짜는 ISO 8601.
6. **MANIFEST 작성**: 모든 파일 목록과 메타 기록.

## 금지 사항
- `crawler/parse.py`, `analysis/stats.py`, `storage/`, `dashboard/`, `tests/` 생성 금지. 이들은 Phase B 담당.
- expected JSON 생성에 쓴 inline 파싱 로직을 별도 모듈로 추출 금지. live.py 내부에서만 존재하다 사라져야 한다.
- 사이트 robots.txt가 대상 경로를 막으면 **우회 시도 금지**. MANIFEST에 차단 사실 기록하고 종료.
- 인증이 필요한 페이지 접근 금지.
- 동시 요청 금지. 순차 실행만.

## 검증 (Phase A 종료 조건)

다음 스크립트가 exit 0을 반환하면 Phase A 완료:

```bash
uv run python -c "
import json, pathlib
m = json.loads(pathlib.Path('fixtures/MANIFEST.json').read_text())
raws = list(pathlib.Path('fixtures/raw').glob('*.html'))
exps = list(pathlib.Path('fixtures/expected').glob('*.json'))
assert len(raws) >= 8, f'raw HTML too few: {len(raws)}'
assert len(exps) >= 8, f'expected JSON too few: {len(exps)}'
assert m['robots_txt_checked'] is True
details = [f for f in m['files'] if f['type'] == 'detail']
assert len(details) >= 6, f'details too few: {len(details)}'
for f in m['files']:
    assert pathlib.Path(f['raw']).exists()
    assert pathlib.Path(f['expected']).exists()
print('phase A verification: ok')
"
```

이 스크립트가 fail하면 실패 원인 분석 → 재수집 → 재검증. 최대 3회 재시도 후에도 fail이면 `fixtures/PHASE_A_FAILED.md`에 실패 원인 상세 작성하고 종료.

## 차단/캡차 대응

- 캡차 감지 시: 즉시 중단. `fixtures/PHASE_A_FAILED.md`에 증상 기록. 우회 금지.
- 빈 응답/리다이렉트 지속 시: User-Agent만 변경 시도 (1회), 그래도 실패하면 위와 동일 처리.
- 법원경매정보가 접근 차단 시 대체 소스: **없음**. 대체 사이트로 갈아타지 말 것. 실패는 실패로 기록.

## 로깅
모든 요청과 저장을 `fixtures/COLLECT_LOG.txt`에 append. 형식:
```
2026-04-22T14:30:01+09:00 GET https://... -> 200 (12034 bytes)
2026-04-22T14:30:04+09:00 SAVE fixtures/raw/list_page_01.html
```

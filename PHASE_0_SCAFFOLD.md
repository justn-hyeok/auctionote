# Phase 0 — Scaffolding Agent

너는 auctionote 프로젝트 **초기 스캐폴딩 에이전트**다. 1회 실행이다.
Phase A가 돌기 전, 프로젝트 뼈대·의존성·테스트 스켈레톤·검증 스크립트를 만든다.

**중요**: 이 Phase에서는 `fixtures/expected/*.json`이 아직 없다.
테스트는 "파일이 있으면 검증한다" 패턴으로 방어적으로 작성한다.
Phase A가 fixture를 채운 뒤, 같은 테스트가 자동으로 활성화된다.

## 산출물

### 1. 프로젝트 루트

- `pyproject.toml` (uv 호환, 아래 deps 확정 박기)
- `.gitignore` (Python 표준 + `data/` + `.venv/` + `__pycache__/`)
- `.python-version` — `3.11`
- `README.md` — 최소 뼈대 (제목, "WIP" 배지, 섹션 플레이스홀더)
- `LOOP_LOG.md` — 빈 파일

### 2. `pyproject.toml` deps (정확히 이대로)

```toml
[project]
name = "auctionote"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "playwright>=1.44",
    "beautifulsoup4>=4.12",
    "lxml>=5.2",
    "pandas>=2.2",
    "plotly>=5.22",
    "folium>=0.16",
    "streamlit>=1.35",
    "streamlit-folium>=0.20",
]

[dependency-groups]
dev = [
    "pytest>=8.2",
    "ruff>=0.5",
    "mypy>=1.10",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### 3. 디렉토리 구조 생성 (빈 `__init__.py` 포함)

```
crawler/__init__.py
analysis/__init__.py
storage/__init__.py
dashboard/__init__.py
tests/__init__.py
fixtures/raw/.gitkeep
fixtures/expected/.gitkeep
scripts/
data/.gitkeep
```

### 4. `scripts/check_streamlit.py`

Streamlit health check. Phase B의 수렴 조건 #4가 이걸 돌린다.

```python
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

PORT = 8765

proc = subprocess.Popen(
    [
        "uv", "run", "streamlit", "run", "dashboard/app.py",
        "--server.headless=true",
        f"--server.port={PORT}",
        "--server.address=127.0.0.1",
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.PIPE,
)
try:
    for _ in range(30):
        time.sleep(1)
        try:
            r = urlopen(f"http://127.0.0.1:{PORT}/_stcore/health", timeout=1)
            if r.status == 200:
                print("streamlit: ok")
                sys.exit(0)
        except URLError:
            continue
    err = (proc.stderr.read() or b"").decode(errors="replace")[-2000:]
    print(f"streamlit: fail\n---stderr tail---\n{err}")
    sys.exit(1)
finally:
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
```

### 5. `scripts/verify_phase_a.py`

Phase A 수렴 조건 스크립트. Phase A 프롬프트의 검증 섹션과 일치해야 함.

```python
import json
import pathlib
import sys

m_path = pathlib.Path("fixtures/MANIFEST.json")
if not m_path.exists():
    print("MANIFEST.json missing")
    sys.exit(1)

m = json.loads(m_path.read_text())
raws = list(pathlib.Path("fixtures/raw").glob("*.html"))
exps = list(pathlib.Path("fixtures/expected").glob("*.json"))

errors = []
if len(raws) < 8:
    errors.append(f"raw HTML too few: {len(raws)}")
if len(exps) < 8:
    errors.append(f"expected JSON too few: {len(exps)}")
if not m.get("robots_txt_checked"):
    errors.append("robots_txt_checked is not true")

details = [f for f in m.get("files", []) if f.get("type") == "detail"]
if len(details) < 6:
    errors.append(f"details too few: {len(details)}")

for f in m.get("files", []):
    if not pathlib.Path(f["raw"]).exists():
        errors.append(f"missing raw: {f['raw']}")
    if not pathlib.Path(f["expected"]).exists():
        errors.append(f"missing expected: {f['expected']}")

if errors:
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print("phase A verification: ok")
```

### 6. `tests/conftest.py`

fixture 로더 헬퍼.

```python
import json
from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def list_detail_cases() -> list[str]:
    """expected/*.json 중 detail_ 접두사인 것의 스템 목록."""
    if not (FIXTURES / "expected").exists():
        return []
    return sorted(
        p.stem for p in (FIXTURES / "expected").glob("detail_*.json")
    )


def list_list_cases() -> list[str]:
    if not (FIXTURES / "expected").exists():
        return []
    return sorted(
        p.stem for p in (FIXTURES / "expected").glob("list_*.json")
    )


def load_raw(name: str) -> str:
    return (FIXTURES / "raw" / f"{name}.html").read_text(encoding="utf-8")


def load_expected(name: str) -> dict:
    return json.loads((FIXTURES / "expected" / f"{name}.json").read_text(encoding="utf-8"))
```

### 7. `tests/test_parse.py`

```python
from datetime import date

import pytest

from tests.conftest import list_detail_cases, list_list_cases, load_expected, load_raw

DETAIL_CASES = list_detail_cases()
LIST_CASES = list_list_cases()


@pytest.mark.skipif(not DETAIL_CASES, reason="Phase A not complete: no detail fixtures")
@pytest.mark.parametrize("name", DETAIL_CASES)
def test_parse_detail(name):
    from crawler.parse import parse_detail

    html = load_raw(name)
    expected = load_expected(name)

    item = parse_detail(html)

    assert item.case_no == expected["case_no"]
    assert item.item_no == expected["item_no"]
    assert item.court == expected["court"]
    assert item.auction_date == date.fromisoformat(expected["auction_date"])
    assert item.appraisal_price == expected["appraisal_price"]
    assert item.min_bid_price == expected["min_bid_price"]
    assert item.failed_count == expected["failed_count"]
    assert item.use_type == expected["use_type"]
    assert item.status == expected["status"]
    assert item.address == expected["address"]
    if expected.get("area_m2") is not None:
        assert item.area_m2 == pytest.approx(expected["area_m2"], rel=1e-3)
    else:
        assert item.area_m2 is None


@pytest.mark.skipif(not LIST_CASES, reason="Phase A not complete: no list fixtures")
@pytest.mark.parametrize("name", LIST_CASES)
def test_parse_list(name):
    from crawler.parse import parse_list

    html = load_raw(name)
    expected = load_expected(name)

    items = parse_list(html)

    assert len(items) == len(expected["items"])
    for got, exp in zip(items, expected["items"], strict=True):
        assert got["case_no"] == exp["case_no"]
        assert got["detail_url"] == exp["detail_url"]
```

### 8. `tests/test_stats.py`

```python
from datetime import date

import pytest

from analysis.schema import AuctionItem
from analysis.stats import (
    by_region,
    by_use_type,
    failed_count_discount_stats,
)


def make(
    failed: int = 0,
    appraisal: int = 1_000_000_000,
    minbid: int = 1_000_000_000,
    address: str = "서울특별시 강남구 역삼동 1",
    use_type: str = "아파트",
) -> AuctionItem:
    return AuctionItem(
        case_no=f"2024타경{failed:05d}",
        item_no=1,
        court="서울중앙지방법원",
        auction_date=date(2026, 5, 1),
        appraisal_price=appraisal,
        min_bid_price=minbid,
        failed_count=failed,
        address=address,
        use_type=use_type,
        area_m2=None,
        status="유찰",
        source_url="",
    )


def test_discount_stats_groups_by_failed_count():
    items = [
        make(0, 1000, 1000),
        make(1, 1000, 800),
        make(1, 1000, 700),
        make(2, 1000, 500),
    ]
    stats = {s["failed_count"]: s for s in failed_count_discount_stats(items)}

    assert stats[0]["count"] == 1
    assert stats[0]["mean_discount"] == pytest.approx(0.0)

    assert stats[1]["count"] == 2
    assert stats[1]["mean_discount"] == pytest.approx(0.25)

    assert stats[2]["count"] == 1
    assert stats[2]["mean_discount"] == pytest.approx(0.5)


def test_discount_stats_empty():
    assert failed_count_discount_stats([]) == []


def test_by_region_groups_first_two_tokens():
    items = [
        make(address="서울특별시 강남구 역삼동 1"),
        make(address="서울특별시 강남구 삼성동 2"),
        make(address="서울특별시 서초구 반포동 3"),
    ]
    regions = {r["region"]: r for r in by_region(items)}
    assert regions["서울특별시 강남구"]["count"] == 2
    assert regions["서울특별시 서초구"]["count"] == 1


def test_by_use_type():
    items = [make(use_type="아파트"), make(use_type="아파트"), make(use_type="토지")]
    d = {r["use_type"]: r["count"] for r in by_use_type(items)}
    assert d == {"아파트": 2, "토지": 1}
```

### 9. `tests/test_storage.py`

```python
from datetime import date

from analysis.schema import AuctionItem
from storage.sqlite import init_db, load_all, load_by_filter, save


def _item(case_no: str, failed: int = 0, use_type: str = "아파트", court: str = "서울중앙지방법원") -> AuctionItem:
    return AuctionItem(
        case_no=case_no, item_no=1, court=court,
        auction_date=date(2026, 5, 1),
        appraisal_price=1_000_000_000, min_bid_price=800_000_000,
        failed_count=failed, address="서울특별시 강남구 역삼동",
        use_type=use_type, area_m2=84.93, status="유찰", source_url="",
    )


def test_save_and_load_roundtrip(tmp_path):
    db = tmp_path / "t.db"
    init_db(db)
    items = [_item("2024타경00001"), _item("2024타경00002", failed=2)]
    save(items, db)
    loaded = load_all(db)
    assert {i.case_no for i in loaded} == {"2024타경00001", "2024타경00002"}


def test_save_is_upsert(tmp_path):
    db = tmp_path / "t.db"
    init_db(db)
    save([_item("X", failed=0)], db)
    save([_item("X", failed=2)], db)
    loaded = load_all(db)
    assert len(loaded) == 1
    assert loaded[0].failed_count == 2


def test_load_by_filter(tmp_path):
    db = tmp_path / "t.db"
    init_db(db)
    save([
        _item("A", use_type="아파트", failed=0),
        _item("B", use_type="아파트", failed=2),
        _item("C", use_type="토지", failed=1),
    ], db)
    assert {i.case_no for i in load_by_filter(db, use_type="아파트")} == {"A", "B"}
    assert {i.case_no for i in load_by_filter(db, min_failed=1)} == {"B", "C"}
```

### 10. `dashboard/app.py` 플레이스홀더

Phase B가 채울 때까지 import 에러 안 나게 최소 구조만:

```python
import streamlit as st

st.set_page_config(page_title="auctionote", layout="wide")
st.title("auctionote")
st.info("Phase B 구현 대기 중")
```

### 11. Phase 0 자체 검증

다음이 모두 통과해야 Phase 0 완료:

```bash
uv sync
uv run ruff check .
uv run pytest -q  # skip 허용, 실패는 불허
uv run python scripts/check_streamlit.py
```

`pytest -q`에서 모든 테스트가 `s` (skipped)로 뜨는 게 정상이다 (Phase A 전이라 fixture 없음).
실패(`F`)가 하나라도 있으면 Phase 0 실패.

## 금지 사항

- `crawler/parse.py`, `analysis/stats.py`, `storage/sqlite.py` 구현 금지 (Phase B 담당)
- `crawler/live.py` 작성 금지 (Phase A 담당)
- `fixtures/` 내부에 아무것도 생성 금지 (`.gitkeep` 제외)
- `README.md`에 자세한 내용 금지 — WIP 플레이스홀더만

## 완료 리포트

종료 시 `PHASE_0_DONE.md` 생성, 다음 체크리스트 포함:

```markdown
# Phase 0 완료 리포트

- [x] pyproject.toml, .gitignore, .python-version 생성
- [x] 디렉토리 구조 생성
- [x] tests/ 3개 파일 작성 (skip으로 통과)
- [x] scripts/check_streamlit.py 작성
- [x] scripts/verify_phase_a.py 작성
- [x] dashboard/app.py 플레이스홀더
- [x] uv sync 성공
- [x] ruff clean
- [x] pytest skip으로 통과 (N개 skipped)
- [x] streamlit health check 통과

다음: Phase A 실행 (PHASE_A_COLLECT.md)
```

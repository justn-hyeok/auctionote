## iter 1 — 2026-04-22T09:45:00+09:00
- selected_failure: baseline — parse/stats/storage/dashboard 전 레이어 미구현
- hypothesis: fixtures가 BS4로 재현 가능한 정형 구조이므로, selector 기반 파서 + 순수함수 통계 + 단순 SQLite CRUD + Streamlit 렌더를 한 번에 구현해도 수렴 가능
- changed: crawler/parse.py, analysis/stats.py, storage/sqlite.py, dashboard/app.py
- pytest: 15 passed, 0 failed
- ruff: 0
- mypy: 0 (8 source files)
- streamlit: ok
- note: 첫 iteration에 4개 레이어 전부 GREEN. 파서는 class selector + data-item-no attr + meta[source-url], 숫자는 non-digit strip, area는 `-` → None 처리. 통계는 statistics.mean/median + defaultdict. storage는 INSERT OR REPLACE upsert + sqlite3.Row row_factory. 대시보드는 DB 없으면 fixtures에서 자동 시드, st.cache_data로 캐시.
- ALL GREEN

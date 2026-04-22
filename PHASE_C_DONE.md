# Phase C 완료

## 체크리스트

- [x] `data/auctionote.db` 생성 (6건, synthetic fallback — `scripts/collect.py` 실행 시 `LiveCrawlAbandoned` → fixtures/raw/detail_*.html 파싱)
- [x] `scripts/collect.py` (live → fixture fallback, 재실행 가능)
- [x] `.streamlit/config.toml` (theme + headless)
- [x] `.gitignore` 수정 — `!data/auctionote.db` 예외 추가
- [x] `README.md` 완성 ([DEMO_URL] 치환 대기, 합성 데이터임을 정직하게 기록)
- [x] `DEPLOY_STEPS.md` (GitHub push → Streamlit Cloud 연결 → URL 치환 → 스크린샷 순서)
- [x] `docs/screenshots/README.md` 플레이스홀더
- [x] 최종 `pytest -q` → 15 passed
- [x] 최종 `ruff check .` → clean
- [x] 최종 `mypy analysis/ crawler/parse.py storage/ dashboard/` → 0 errors
- [x] 최종 `uv run python scripts/check_streamlit.py` → ok

## 라이브 수집 결과 (정직하게)

Phase A에서 courtauction.go.kr이 WebSquare SPA로 확인되어 라이브 수집이 중단되었다. `crawler/live.py`는 `LiveCrawlAbandoned` 예외를 raise하는 스텁 상태이고, `scripts/collect.py`는 이 예외를 catch해 `fixtures/raw/detail_*.html` 합성 fixture에서 시드한다. 수집 건수는 6건 (합성, `use_type` 4종 × `failed_count` 0/1/2/3 커버).

이 사실은 README "데이터 출처" 섹션과 `fixtures/LIVE_CRAWL_ABANDONED.md`에 명시.

## 남은 수동 작업 (사용자 몫)

1. GitHub repo 생성 + push
2. Streamlit Cloud 연결 + URL 획득
3. `README.md`의 `[DEMO_URL]` 치환
4. 스크린샷 3장 촬영 → `docs/screenshots/`
5. 커밋 분리 (Phase 0/A/B/C 산출물이 현재 전부 untracked)

자세한 순서: `DEPLOY_STEPS.md`

## 커밋 상태

현재 Phase 0/A/B/C 산출물이 **전부 untracked** 상태다 (최초 `chore: bootstrap phase prompts` 커밋 이후 모든 구현이 미커밋). Phase C 스펙의 "최소 5개 커밋" 권장은 아직 미충족. 커밋 전략(기능 단위 분리 / Phase 단위 분리 / 단일 스쿼시)은 사용자 판단 대기.

## 후속 (post-Phase-C)

- data.go.kr 공공데이터포털 **법원경매정보 Open API** 키 발급 → `crawler/live.py`를 HTTPX 기반 API 클라이언트로 교체
- 합성 fixture는 파서 회귀 테스트로 유지, API 응답 샘플을 새 fixture로 추가
- 낙찰가 이력 / 주소 geocoding / 증분 크롤링 도입은 README "한계" 섹션 참조

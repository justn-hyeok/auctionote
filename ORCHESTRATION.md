# auctionote — AI 에이전트 오케스트레이션 가이드

이 프로젝트는 **4단계 AI 에이전트 파이프라인**으로 완전 자동화된다.
사람이 하는 일은 각 Phase의 프롬프트를 Claude Code에게 전달하고 수렴 조건을 확인하는 것뿐.

## Phase 구성

| Phase | 성격 | 프롬프트 파일 | 산출물 |
|-------|------|---------------|--------|
| 0 | 1회 실행 | `PHASE_0_SCAFFOLD.md` | 프로젝트 뼈대, 테스트, 검증 스크립트 |
| A | 1회 실행 | `PHASE_A_COLLECT.md` | `fixtures/`, `crawler/live.py`, `analysis/schema.py` |
| B | **Ralph loop** | `PHASE_B_IMPLEMENT.md` | 파서, 통계, 저장, 대시보드 |
| C | 1회 실행 | `PHASE_C_DEPLOY.md` | 실데이터, README, 배포 가이드 |

## 왜 이 구조인가

Ralph loop의 약점은 **탐색적 작업**과 **네트워크 의존 작업**이다. 이 두 구간을 루프 밖으로
빼내면 나머지는 결정론적 검증(pytest)으로 수렴 조건이 명확해진다.

- Phase 0: 결정론적, loop 불필요
- Phase A: 탐색적 + 네트워크 의존, loop에 부적합 → 1회 에이전트
- Phase B: fixture 고정된 순수 로직, **Ralph loop에 최적**
- Phase C: 탐색적 + 수동 배포 포함, loop 불필요

## 실행 순서

### Phase 0 실행

```bash
# 새 Claude Code 세션
claude -p "$(cat PHASE_0_SCAFFOLD.md)" --allowedTools "Read,Write,Edit,Bash"

# 검증
uv run ruff check .
uv run pytest -q       # 전부 skipped면 성공
uv run python scripts/check_streamlit.py
test -f PHASE_0_DONE.md
```

### Phase A 실행

```bash
claude -p "$(cat PHASE_A_COLLECT.md)" --allowedTools "Read,Write,Edit,Bash"

# 검증
uv run python scripts/verify_phase_a.py
```

실패 시 `fixtures/PHASE_A_FAILED.md` 확인. 차단 증상이면 프로젝트 자체 재검토.

### Phase B 실행 (Ralph loop)

```bash
MAX_ITER=50
for i in $(seq 1 $MAX_ITER); do
  echo "=== iter $i ==="
  claude -p "$(cat PHASE_B_IMPLEMENT.md)" \
    --allowedTools "Read,Write,Edit,Bash" \
    --disallowedTools "WebFetch,WebSearch"

  # 수렴 조건 5종 체크
  uv run pytest -q \
    && uv run ruff check . \
    && uv run mypy analysis/ crawler/parse.py storage/ dashboard/ \
    && uv run python scripts/check_streamlit.py \
    && tail -1 LOOP_LOG.md | grep -q "ALL GREEN" \
    && { echo "converged at iter $i"; break; }

  # STUCK 감지
  grep -q "^## STUCK" LOOP_LOG.md && { echo "stuck, aborting"; exit 1; }

  sleep 1
done
```

`harness-for-yall`에 이미 비슷한 래퍼 있으면 거기 얹는 게 나음.

### Phase C 실행

```bash
# Phase B가 ALL GREEN 확인 후
claude -p "$(cat PHASE_C_DEPLOY.md)" --allowedTools "Read,Write,Edit,Bash"

# 수동 작업 처리
cat DEPLOY_STEPS.md
# → GitHub push, Streamlit Cloud 연동, 스크린샷 촬영
```

## 파일 소유권 매트릭스

어떤 Phase가 어떤 파일을 수정할 수 있는지. Phase 프롬프트 내부 금지 조항과 이 표가 일치해야 함.

| 경로 | Phase 0 | Phase A | Phase B | Phase C |
|------|---------|---------|---------|---------|
| `pyproject.toml`, `.gitignore` | ✅ 생성 | ❌ | ❌ (deps 고정) | ⚠️ `.gitignore`만 조정 가능 |
| `analysis/schema.py` | ❌ | ✅ 생성 | ❌ (고정) | ❌ |
| `crawler/live.py` | ❌ | ✅ 생성 | ❌ | 읽기만 |
| `crawler/parse.py` | ❌ | ❌ | ✅ | 읽기만 |
| `analysis/stats.py` | ❌ | ❌ | ✅ | 읽기만 |
| `storage/sqlite.py` | ❌ | ❌ | ✅ | 읽기만 |
| `dashboard/app.py` | ✅ 플레이스홀더 | ❌ | ✅ | ⚠️ 스타일만 |
| `fixtures/**` | ❌ | ✅ 생성 | ❌ | ❌ |
| `tests/**` | ✅ 생성 | ❌ | ⚠️ 버그만 | ❌ |
| `scripts/check_streamlit.py` | ✅ 생성 | ❌ | ❌ | ❌ |
| `scripts/verify_phase_a.py` | ✅ 생성 | ❌ | ❌ | ❌ |
| `scripts/collect.py` | ❌ | ❌ | ❌ | ✅ 생성 |
| `README.md` | ✅ WIP | ❌ | ❌ | ✅ 완성 |
| `data/auctionote.db` | ❌ | ❌ | ❌ | ✅ 생성 |
| `LOOP_LOG.md` | ✅ 빈 파일 | ❌ | ✅ append | ❌ |

## 예상 소요 시간 (AI 실행 시간만)

- Phase 0: 5-10분
- Phase A: 15-40분 (사이트 구조 따라 변동 큼)
- Phase B: 30분-2시간 (Ralph 수렴 횟수 따라)
- Phase C: 10-20분
- 수동 배포: 15분

## 실패 모드와 대응

| 증상 | 원인 | 대응 |
|------|------|------|
| Phase A가 캡차에 막힘 | 사이트 차단 | 프로젝트 재설계 (다른 소스로 피벗) |
| Phase B가 STUCK | fixture와 테스트 불일치 | Phase A의 expected JSON 수동 검토 후 Phase B 재개 |
| Phase B 무한루프 | 수렴 조건 너무 엄격 | `MAX_ITER` 도달하면 LOOP_LOG 분석해서 가장 얕은 실패부터 수동 개입 |
| Streamlit health check 실패 | dashboard/app.py import error | Phase B 프롬프트의 우선순위 #4가 안 닿은 것. `LOOP_LOG.md`에 force iteration 힌트 추가 |
| Phase C 수집 0건 | live 사이트 구조 변경 | MANIFEST의 수집일과 현재 시점 비교, 필요 시 Phase A 재실행 |

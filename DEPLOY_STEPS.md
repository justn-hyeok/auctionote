# 배포 메모

Streamlit Community Cloud 공개 데모는 단순 모드로 운영한다.

## 현재 배포

- Repository: `justn-hyeok/auctionote`
- Branch: `main`
- Main file path: `dashboard/app.py`
- Live demo: https://auctionote-g5gndhc2ri3ca5h6qbyappb.streamlit.app/

## 배포 방식

- Streamlit Cloud는 `requirements.txt`를 설치한다.
- 공개 데모는 `data/auctionote.db`를 읽는 SQLite demo mode로 실행한다.
- `AUCTIONOTE_DATABASE_URL`이 없으면 PostgreSQL을 호출하지 않는다.
- `AUCTIONOTE_ELASTIC_URL`이 없으면 Elasticsearch를 호출하지 않는다.

## 배포

`main`에 push하면 Streamlit Cloud가 자동 재배포한다.

```bash
git push origin main
```

## 선택 로컬 스택

PostgreSQL/Elasticsearch까지 확인하고 싶을 때만 로컬에서 실행한다.

```bash
docker compose up -d postgres elasticsearch
uv run python scripts/migrate_postgres.py
uv run python scripts/reindex_elastic.py
AUCTIONOTE_DATABASE_URL=postgresql+psycopg://auctionote:auctionote@localhost:5432/auctionote \
AUCTIONOTE_ELASTIC_URL=http://localhost:9200 \
uv run streamlit run dashboard/app.py
```

## 검증

- `README.md`의 데모 링크가 살아있는지
- README 상단 스크린샷이 렌더되는지 (GitHub repo 페이지에서)
- Streamlit 앱에서 사이드바 필터가 동작하는지, 지도가 뜨는지

## 트러블슈팅

- **ModuleNotFoundError on Streamlit Cloud**: `requirements.txt`에 대시보드 실행 의존성을 추가한다.
- **lxml 빌드 실패**: Streamlit Cloud는 보통 wheel을 받아오지만, 실패 시 `packages.txt`에 `libxml2-dev libxslt-dev` 추가.
- **지도 안 뜸**: `streamlit-folium`이 설치됐는지 확인. pyproject.toml의 deps에 이미 포함.

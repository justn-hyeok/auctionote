# 배포 수동 작업

Streamlit Community Cloud 배포. 너(Justn)가 직접 해야 하는 단계 순서대로.

## 1. GitHub repo

1. https://github.com/new → name: `auctionote`, public
2. 로컬에서:
   ```bash
   git remote add origin git@github.com:justn-hyeok/auctionote.git
   git push -u origin main
   ```

## 2. Streamlit Cloud 연결

1. https://share.streamlit.io → **New app**
2. Repository: `justn-hyeok/auctionote`, Branch: `main`, Main file path: `dashboard/app.py`
3. Python version: 3.11
4. **Deploy** 클릭
5. 배포 완료(~2-3분) 후 URL 복사

## 3. README 치환

1. `README.md` 최상단의 `[DEMO_URL]` → 실제 URL로 치환
2. commit & push

## 4. 스크린샷

1. 배포된 대시보드에 접속
2. `docs/screenshots/README.md` 체크리스트대로 3장 촬영
3. 파일명 그대로 `docs/screenshots/`에 저장
4. commit & push

## 5. 검증

- `README.md`의 데모 링크가 살아있는지
- README 상단 스크린샷이 렌더되는지 (GitHub repo 페이지에서)
- Streamlit 앱에서 사이드바 필터가 동작하는지, 지도가 뜨는지

## 트러블슈팅

- **ModuleNotFoundError on Streamlit Cloud**: Streamlit Cloud는 `requirements.txt`를 자동 추론 못하는 경우가 있다. 필요하면 `uv pip compile pyproject.toml > requirements.txt` 생성 후 commit.
- **lxml 빌드 실패**: Streamlit Cloud는 보통 wheel을 받아오지만, 실패 시 `packages.txt`에 `libxml2-dev libxslt-dev` 추가.
- **지도 안 뜸**: `streamlit-folium`이 설치됐는지 확인. pyproject.toml의 deps에 이미 포함.

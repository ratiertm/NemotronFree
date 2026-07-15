# Nemotron 채팅 (PWA)

NVIDIA Nemotron 무료 API 를 사용하는 모바일 채팅 웹앱.
API 키는 **서버 환경변수에만** 존재하고 폰/브라우저로 노출되지 않습니다.

```
[갤럭시폰 브라우저]  →  [서버(server.py)]  →  [NVIDIA Nemotron API]
   PWA 채팅 UI          키 숨김 + 스트리밍 중계     (키 = 환경변수)
```

## 구조
- `server.py` — FastAPI. `web/` 정적 서빙 + `/api/chat` 스트리밍 중계
- `web/` — PWA 프런트엔드 (index.html / manifest / sw.js / 아이콘)
- `.env` — `NVIDIA_API_KEY` (git 제외됨)
- `render.yaml` — Render 무료 배포 설정

## 로컬 실행
```bash
.venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8000
```
- PC 브라우저: http://localhost:8000
- 같은 WiFi 의 폰: http://<PC-LAN-IP>:8000
  - ⚠️ LAN(http)에서는 "홈 화면에 추가(PWA 설치)"가 제한됩니다. 채팅은 정상 동작.
    PWA 설치는 아래 HTTPS 배포 후 완전히 동작합니다.

## 무료 클라우드 배포 (Render)
1. 이 프로젝트를 GitHub 저장소로 push (`.env` 는 제외됨 — 키가 올라가지 않음)
2. https://render.com 가입 → **New → Blueprint** → 이 저장소 선택
3. 환경변수 `NVIDIA_API_KEY` 에 `nvapi-...` 키 입력 (Render 대시보드)
4. 배포 완료 후 `https://<앱이름>.onrender.com` 주소 생성
5. 갤럭시 크롬에서 그 주소 접속 → 메뉴 → **홈 화면에 추가** → 앱처럼 사용 ✅

> Render 무료 플랜은 일정 시간 미사용 시 잠들었다가 첫 접속에 ~30초 콜드스타트가 있습니다.

## 모델
헤더 드롭다운에서 선택 (Ultra / Super / Nano). 기본값은 `NEMOTRON_MODEL` 환경변수로 변경 가능.

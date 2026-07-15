"""
Nemotron 채팅 웹앱 서버.

- 정적 PWA(web/) 를 서빙하고
- /api/chat 로 들어온 대화를 NVIDIA Nemotron API 로 중계(스트리밍)한다.
- API 키는 서버 환경변수(NVIDIA_API_KEY)에만 존재 → 폰/브라우저로 노출되지 않음.

로컬 실행:
  .venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8000

클라우드(Render 등):
  uvicorn server:app --host 0.0.0.0 --port $PORT
"""
import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

API_KEY = os.environ.get("NVIDIA_API_KEY")
DEFAULT_MODEL = os.environ.get("NEMOTRON_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")

ALLOWED_MODELS = {
    "nvidia/nemotron-3-ultra-550b-a55b",
    "nvidia/nemotron-3-super-120b-a12b",
    "nvidia/nemotron-3-nano-omni-30b-a3b",
}

client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=API_KEY) if API_KEY else None

app = FastAPI(title="Nemotron Chat")


class Msg(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Msg]
    model: str | None = None
    thinking: bool = True


@app.get("/api/health")
def health():
    return {"ok": True, "key_configured": bool(API_KEY), "default_model": DEFAULT_MODEL}


@app.post("/api/chat")
def chat(req: ChatRequest):
    if client is None:
        return JSONResponse(
            {"error": "서버에 NVIDIA_API_KEY 가 설정되지 않았습니다."}, status_code=500
        )

    model = req.model if req.model in ALLOWED_MODELS else DEFAULT_MODEL
    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    def sse(payload: dict) -> str:
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    def event_stream():
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=1,
                top_p=0.95,
                max_tokens=16384,
                extra_body={
                    "chat_template_kwargs": {"enable_thinking": bool(req.thinking)},
                    # 생각(reasoning) 예산을 전체(max_tokens)보다 작게 두어
                    # 답변(content)용 토큰 공간을 반드시 남긴다.
                    "reasoning_budget": 8192,
                },
                stream=True,
            )
            for chunk in completion:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                reasoning = getattr(delta, "reasoning_content", None)
                if reasoning:
                    yield sse({"type": "reasoning", "text": reasoning})
                if delta.content:
                    yield sse({"type": "content", "text": delta.content})
        except Exception as e:  # noqa: BLE001
            yield sse({"type": "error", "text": str(e)})
        finally:
            yield sse({"type": "done"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# 정적 PWA 서빙 (맨 마지막에 마운트: /api 라우트가 우선)
app.mount("/", StaticFiles(directory="web", html=True), name="web")

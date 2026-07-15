"""
NVIDIA Nemotron 3 Ultra — free API 스트리밍 테스트.

사전 준비:
  1. .env 파일에 NVIDIA_API_KEY=nvapi-... 저장
  2. pip install openai python-dotenv

실행:
  python nemotron_test.py "여기에 질문"
"""
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.environ.get("NVIDIA_API_KEY")
if not api_key:
    sys.exit("NVIDIA_API_KEY 가 .env 에 없습니다.")

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=api_key,
)

# 커맨드라인 인자를 프롬프트로 사용, 없으면 기본 질문
prompt = " ".join(sys.argv[1:]) or "간단히 자기소개 해줘. 한국어로."

completion = client.chat.completions.create(
    model="nvidia/nemotron-3-ultra-550b-a55b",
    messages=[{"role": "user", "content": prompt}],
    temperature=1,
    top_p=0.95,
    max_tokens=16384,
    extra_body={
        "chat_template_kwargs": {"enable_thinking": True},
        "reasoning_budget": 16384,
    },
    stream=True,
)

for chunk in completion:
    if not chunk.choices:
        continue
    reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
    if reasoning:
        print(reasoning, end="", flush=True)
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()

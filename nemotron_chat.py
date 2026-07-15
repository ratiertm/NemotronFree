"""
NVIDIA Nemotron 3 Ultra — 대화형 멀티턴 채팅 루프.

대화 히스토리를 유지하며 스트리밍으로 응답합니다.

사전 준비:
  1. .env 파일에 NVIDIA_API_KEY=nvapi-... 저장
  2. .venv/bin/python -m pip install openai python-dotenv

실행:
  .venv/bin/python nemotron_chat.py

명령어 (프롬프트에서 입력):
  /exit, /quit   종료
  /reset         대화 히스토리 초기화
  /think         사고 과정(reasoning) 표시 켜기/끄기
  /system <text> 시스템 프롬프트 설정
  /help          도움말
"""
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.environ.get("NVIDIA_API_KEY")
if not api_key:
    sys.exit("NVIDIA_API_KEY 가 .env 에 없습니다.")

MODEL = "nvidia/nemotron-3-ultra-550b-a55b"

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=api_key,
)


def stream_reply(messages, show_thinking):
    """모델 응답을 스트리밍하고, 최종 답변 텍스트를 반환한다."""
    completion = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=1,
        top_p=0.95,
        max_tokens=16384,
        extra_body={
            "chat_template_kwargs": {"enable_thinking": True},
            "reasoning_budget": 16384,
        },
        stream=True,
    )

    answer_parts = []
    printed_thinking_header = False
    printed_answer_header = False

    for chunk in completion:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta

        reasoning = getattr(delta, "reasoning_content", None)
        if reasoning and show_thinking:
            if not printed_thinking_header:
                print("\n\033[90m[사고 과정]\033[0m", flush=True)
                printed_thinking_header = True
            print(f"\033[90m{reasoning}\033[0m", end="", flush=True)

        if delta.content is not None:
            if not printed_answer_header:
                if printed_thinking_header:
                    print()  # 사고 과정과 답변 사이 줄바꿈
                print("\033[96mNemotron:\033[0m ", end="", flush=True)
                printed_answer_header = True
            print(delta.content, end="", flush=True)
            answer_parts.append(delta.content)

    print()  # 응답 끝 줄바꿈
    return "".join(answer_parts)


def main():
    show_thinking = True
    system_prompt = None
    history = []  # user/assistant 턴만 저장 (system 은 매 호출 시 앞에 붙임)

    print("=" * 60)
    print(" Nemotron 3 Ultra 대화형 채팅")
    print(" /help 로 명령어 확인, /exit 로 종료")
    print(f" 사고 과정 표시: {'ON' if show_thinking else 'OFF'}")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n\033[92m나:\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            break

        if not user_input:
            continue

        # ---- 명령어 처리 ----
        if user_input in ("/exit", "/quit"):
            print("종료합니다.")
            break
        if user_input == "/reset":
            history.clear()
            print("\033[93m대화 히스토리를 초기화했습니다.\033[0m")
            continue
        if user_input == "/think":
            show_thinking = not show_thinking
            print(f"\033[93m사고 과정 표시: {'ON' if show_thinking else 'OFF'}\033[0m")
            continue
        if user_input.startswith("/system"):
            system_prompt = user_input[len("/system"):].strip() or None
            state = f"설정됨: {system_prompt}" if system_prompt else "해제됨"
            print(f"\033[93m시스템 프롬프트 {state}\033[0m")
            continue
        if user_input == "/help":
            print(
                "\033[93m"
                "/exit, /quit   종료\n"
                "/reset         대화 히스토리 초기화\n"
                "/think         사고 과정 표시 토글\n"
                "/system <text> 시스템 프롬프트 설정 (빈 값이면 해제)\n"
                "/help          이 도움말"
                "\033[0m"
            )
            continue

        # ---- 대화 진행 ----
        history.append({"role": "user", "content": user_input})

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(history)

        try:
            answer = stream_reply(messages, show_thinking)
        except KeyboardInterrupt:
            print("\n\033[93m(응답 중단됨)\033[0m")
            history.pop()  # 방금 user 턴 되돌림
            continue
        except Exception as e:  # noqa: BLE001
            print(f"\n\033[91m오류: {e}\033[0m")
            history.pop()
            continue

        history.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()

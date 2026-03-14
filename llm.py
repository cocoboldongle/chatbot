"""
core/llm.py
──────────────────────────────────────────────
OpenAI API 호출 로직만 담당합니다.
UI(Streamlit)에 의존하지 않습니다.
"""
from typing import Generator
from openai import OpenAI


def get_api_key(api_key_input: str) -> str:
    """사이드바 입력값 → Streamlit secrets 순서로 API 키를 반환합니다."""
    if api_key_input:
        return api_key_input
    try:
        import streamlit as st
        return st.secrets["OPENAI_API_KEY"]
    except Exception:
        return ""


def stream_chat(
    api_key: str,
    messages: list[dict],
    system_prompt: str,
    temperature: float,
    max_tokens: int,
    model: str = "gpt-4o",
) -> Generator[str, None, None]:
    """
    OpenAI Chat Completions를 스트리밍으로 호출하고
    텍스트 청크를 하나씩 yield합니다.

    Parameters
    ----------
    api_key      : OpenAI API 키
    messages     : 지금까지의 대화 기록 [{"role": ..., "content": ...}, ...]
    system_prompt: 시스템 메시지
    temperature  : 샘플링 온도 (0.0 ~ 2.0)
    max_tokens   : 최대 응답 토큰 수
    model        : 사용할 모델 (기본 gpt-4o)

    Yields
    ------
    str : 스트리밍 응답 텍스트 청크
    """
    client = OpenAI(api_key=api_key)

    full_messages = [
        {"role": "system", "content": system_prompt},
        *messages,
    ]

    stream = client.chat.completions.create(
        model=model,
        messages=full_messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            yield delta

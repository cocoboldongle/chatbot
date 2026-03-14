"""
llm.py — OpenAI API 호출 + 정보 수집 판단 로직
"""
import json
from typing import Generator
from openai import OpenAI


def stream_chat(
    api_key: str,
    messages: list[dict],
    system_prompt: str,
    temperature: float,
    max_tokens: int,
    model: str = "gpt-4o",
) -> Generator[str, None, None]:
    client = OpenAI(api_key=api_key)
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system_prompt}, *messages],
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            yield delta


# ── 정보 수집 판단 ─────────────────────────────────────────────────────────────

INFO_CHECK_PROMPT = """
너는 대화 분석 전문가야. 아래 대화를 보고 JSON만 반환해. 다른 말은 절대 하지 마.

분석할 항목:
1. sufficient: 아래 4가지 항목이 충분히 파악되었으면 true, 아니면 false
   - 어떤 상황/사건이 있었는지
   - 그 상황에서 어떤 생각이 들었는지
   - 그 생각으로 인해 어떤 감정을 느꼈는지
   - 그 감정의 강도나 영향

2. 수집된 경우에만: 아래 필드도 채워줘 (없으면 null)
   - situation: 상황 한 줄 요약
   - thought: 핵심 생각 한 줄
   - emotion: 감정 (예: 불안, 슬픔, 분노)
   - intensity: 감정 강도 (예: "많이", "조금", "매우")
   - summary: 전체 상황을 2~3문장으로 공감하며 요약

반환 형식 예시:
{"sufficient": true, "situation": "...", "thought": "...", "emotion": "...", "intensity": "...", "summary": "..."}
{"sufficient": false, "situation": null, "thought": null, "emotion": null, "intensity": null, "summary": null}
"""


def check_info_sufficient(
    api_key: str,
    messages: list[dict],
    model: str = "gpt-4o",
) -> dict:
    """
    대화에서 상황/생각/감정 정보가 충분히 수집되었는지 판단.
    최소 사용자 메시지 3개 이상일 때만 체크.
    반환: {"sufficient": bool, "situation": str|None, ...}
    """
    user_msgs = [m for m in messages if m["role"] == "user"]
    if len(user_msgs) < 3:
        return {"sufficient": False}

    client   = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": INFO_CHECK_PROMPT},
            {"role": "user",   "content": str(messages)},
        ],
        temperature=0,
        max_tokens=400,
    )
    raw = response.choices[0].message.content.strip()
    try:
        # JSON 블록만 추출
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        return {"sufficient": False}

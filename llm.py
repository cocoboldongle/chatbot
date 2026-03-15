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
너는 심리 상담 대화 분석 전문가야. 아래 대화를 분석하고 JSON만 반환해. 다른 말은 절대 하지 마.

[핵심 판단 기준]
이 챗봇은 청소년의 부정적인 경험(스트레스, 갈등, 슬픔, 불안, 분노, 억울함 등)을
인지 재구조화로 도와주는 도구야.

따라서 sufficient는 아래 조건을 모두 만족할 때만 true야:
  1. 사용자가 부정적인 감정(슬픔, 불안, 분노, 억울함, 외로움, 무기력 등)을 언급했는가
  2. 그 감정을 유발한 구체적인 상황/사건이 파악되었는가
  3. 그 상황에서 어떤 생각이 들었는지 파악되었는가
  4. 감정의 강도가 어느 정도인지 파악되었는가

[중요]
- 단순히 즐거웠던 일, 좋은 일, 자랑스러운 일 → sufficient: false
- 긍정적인 감정(기쁨, 신남, 뿌듯함)만 나온 경우 → sufficient: false
- 부정적인 감정이 명확히 포함된 경우에만 sufficient: true 가능

반환 필드:
  - sufficient: bool
  - negative: bool  ← 부정적인 감정/사건이 대화에 등장했는지 여부
  - situation: 상황 한 줄 요약 (없으면 null)
  - thought: 핵심 생각 한 줄 (없으면 null)
  - emotion: 감정 단어 (없으면 null)
  - intensity: 감정 강도. 반드시 "약하게", "조금", "꽤", "많이", "매우", "극도로" 중 하나로 표현.
             사용자가 명시하지 않았더라도 대화 맥락에서 추론해서 반드시 채워줘. null 금지.
  - summary: 2~3문장 공감 요약 (없으면 null)

반환 예시:
{"sufficient": true, "negative": true, "situation": "엄마와 공부 문제로 싸움", "thought": "나만 혼내는 게 불공평하다", "emotion": "억울함과 슬픔", "intensity": "많이", "summary": "..."}
{"sufficient": false, "negative": false, "situation": null, "thought": null, "emotion": null, "intensity": null, "summary": null}
{"sufficient": false, "negative": true, "situation": "친구와 싸움", "thought": null, "emotion": "화남", "intensity": null, "summary": null}
"""


def check_info_sufficient(
    api_key: str,
    messages: list[dict],
    model: str = "gpt-4o",
) -> dict:
    """
    대화에서 부정적 사건의 상황/생각/감정 정보가 충분히 수집되었는지 판단.
    - 최소 사용자 메시지 3개 이상일 때만 체크
    - 긍정적인 대화만 있으면 sufficient=False, negative=False 반환
    반환: {"sufficient": bool, "negative": bool, "situation": str|None, ...}
    """
    user_msgs = [m for m in messages if m["role"] == "user"]
    if len(user_msgs) < 3:
        return {"sufficient": False, "negative": False}

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
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        return {"sufficient": False, "negative": False}

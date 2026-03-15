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


# ── 인지왜곡 추출 ──────────────────────────────────────────────────────────────

DISTORTION_EXTRACT_PROMPT = """
너는 인지행동치료(CBT) 전문가야. 아래 대화를 분석하고 JSON만 반환해. 다른 말은 절대 하지 마.

[인지왜곡 10가지 유형]
1. 흑백 사고 (All-or-Nothing): "항상", "절대", "완전히" — 중간 없이 극단적 판단
2. 과잉 일반화 (Overgeneralization): 한 번 일어난 일을 "항상 그래"로 확대
3. 부정적 편향 (Mental Filter): 좋은 건 무시하고 나쁜 것에만 집중
4. 긍정 축소화 (Disqualifying the Positive): 잘한 것을 "별거 아니야", "운이었어"로 무시
5. 성급한 판단 (Jumping to Conclusions): 증거 없이 타인 마음 단정 또는 미래 예측
6. 확대와 축소 (Magnification/Minimization): 작은 실수를 "다 망했어", "인생 끝"으로 과장
7. 감정적 추론 (Emotional Reasoning): "불안하니까 나쁜 일 생길 거야" — 느낌을 사실로
8. 해야 한다 진술 (Should Statements): "나는 항상 잘해야 해" — 비현실적 기준으로 자책
9. 낙인찍기 (Labeling): "나는 바보야", "나는 실패자야" — 자신/타인을 부정적으로 규정
10. 개인화 (Personalization): "다 내 탓이야" — 자신과 무관한 일도 자기 책임으로

[분석 지침]
- 대화 전체에서 사용자의 말을 분석해
- 가능성이 높은 순서대로 최대 3개 선택
- 각 왜곡에 대해 청소년이 이해하기 쉬운 설명과 대화에서 발견한 근거를 써줘
- 없으면 빈 배열 반환

반환 형식 (JSON만, 다른 텍스트 금지):
{
  "distortions": [
    {
      "type": "왜곡 이름 (한국어)",
      "english": "영문명",
      "reason": "왜 이 왜곡이라고 생각하는지 — 대화에서 발견한 근거 (청소년 눈높이로, 1~2문장)",
      "quote": "사용자가 실제로 한 말 중 이 왜곡이 드러나는 부분 (짧게)"
    }
  ]
}
"""


def extract_distortions(
    api_key: str,
    messages: list[dict],
    model: str = "gpt-4o",
) -> list[dict]:
    """
    대화에서 인지왜곡 유형을 추출.
    가능성 높은 순으로 최대 3개 반환.
    반환: [{"type": str, "english": str, "reason": str, "quote": str}, ...]
    """
    clean = [m for m in messages if m.get("role") in ("user", "assistant")]
    if not clean:
        return []

    client   = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": DISTORTION_EXTRACT_PROMPT},
            {"role": "user",   "content": str(clean)},
        ],
        temperature=0,
        max_tokens=600,
    )
    raw = response.choices[0].message.content.strip()
    try:
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        data  = json.loads(raw[start:end])
        return data.get("distortions", [])
    except Exception:
        return []


# ── 인지왜곡 탐색 충분성 판단 ─────────────────────────────────────────────────

DISTORTION_SUFFICIENT_PROMPT = """
너는 인지행동치료 전문가야. 아래 대화를 분석하고 JSON만 반환해. 다른 말은 절대 하지 마.

[이 대화는 인지왜곡 탐색 단계의 대화야]
목표: 인지왜곡 패턴을 추출하기에 충분한 정보가 모였는지 판단.

sufficient: true 조건 — 아래 3가지가 모두 확인돼야 해:
  1. 구체적 부정적 생각: 사용자가 그 상황에서 느낀 부정적 생각을 2개 이상 구체적으로 표현했는가
     (예: "엄마는 항상 나만 뭐라고 해", "말해봤자 또 싸울 것 같아")
  2. 반복성/패턴: 비슷한 상황이 반복된다는 것, 또는 이 생각이 자주 든다는 것이 확인됐는가
  3. 근거 탐색: 그 생각이 느낌인지 실제 근거가 있는지에 대한 대화가 오갔는가
     (사용자가 직접 답하지 않아도, 챗봇이 물어보고 사용자가 어떤 식으로든 반응했으면 ok)

false 조건:
  - 위 3가지 중 하나라도 빠지면 false
  - 사용자가 단답("응", "몰라요", "그냥요")만 반복한 경우 false
  - 구체적인 생각 표현 없이 상황 설명만 있는 경우 false

반환 형식 (JSON만):
{"sufficient": true} 또는 {"sufficient": false}
"""


def check_distortion_sufficient(
    api_key: str,
    messages: list[dict],
    model: str = "gpt-4o",
) -> bool:
    """
    인지왜곡 탐색이 충분히 됐는지 판단.
    distortion 단계의 사용자 메시지 4개 미만이면 무조건 False.
    """
    # distortion 단계 이후 메시지 기준으로 사용자 메시지 4개 미만이면 False
    user_msgs = [m for m in messages if m.get("role") == "user"]
    if len(user_msgs) < 4:
        return False

    client   = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": DISTORTION_SUFFICIENT_PROMPT},
            {"role": "user",   "content": str(messages)},
        ],
        temperature=0,
        max_tokens=50,
    )
    raw = response.choices[0].message.content.strip()
    try:
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        return json.loads(raw[start:end]).get("sufficient", False)
    except Exception:
        return False


# ── 재구조화 완료 판단 ─────────────────────────────────────────────────────────

REFRAMING_COMPLETE_PROMPT = """
너는 인지행동치료 전문가야. 아래 대화를 분석하고 JSON만 반환해. 다른 말은 절대 하지 마.

[판단 목표]
재구조화 단계 대화에서 사용자의 생각이 긍정적으로 변화했는지 판단해.

sufficient: true 조건 — 아래 중 2가지 이상이 확인돼야 해:
  1. 사용자가 기존의 부정적 생각에 대해 "그럴 수도 있겠다", "다르게 볼 수도 있겠다" 같은
     유연한 반응을 보였는가
  2. 사용자가 스스로 대안적 생각이나 관점을 제시했는가
     (예: "생각해보면 엄마가 걱정해서 그런 거일 수도 있겠어요")
  3. 감정적으로 조금 가벼워졌다는 표현이 있는가
     (예: "그렇게 생각하니까 좀 나은 것 같아요", "덜 억울한 것 같아요")
  4. 상황에 대한 구체적인 행동 계획이나 작은 변화를 언급했는가

false 조건:
  - 사용자가 여전히 같은 부정적 생각만 반복하고 있는 경우
  - 단순히 "네", "모르겠어요" 같은 단답만 있는 경우
  - 생각의 변화 없이 대화만 이어지는 경우
  - 재구조화 단계 사용자 메시지가 3개 미만인 경우

반환 형식 (JSON만):
{"complete": true, "summary": "사용자의 변화를 1~2문장으로 따뜻하게 요약"}
{"complete": false}
"""


def check_reframing_complete(
    api_key: str,
    messages: list[dict],
    model: str = "gpt-4o",
) -> dict:
    """
    재구조화가 완료됐는지 판단.
    reframing 단계 사용자 메시지 3개 미만이면 무조건 False.
    반환: {"complete": bool, "summary": str|None}
    """
    user_msgs = [m for m in messages if m.get("role") == "user"]
    if len(user_msgs) < 3:
        return {"complete": False}

    client   = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": REFRAMING_COMPLETE_PROMPT},
            {"role": "user",   "content": str(messages)},
        ],
        temperature=0,
        max_tokens=200,
    )
    raw = response.choices[0].message.content.strip()
    try:
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        return {"complete": False}


# ── 답변 추천 생성 ─────────────────────────────────────────────────────────────

SUGGEST_PROMPT = """
너는 청소년 심리 상담 보조 AI야. JSON만 반환해. 다른 말은 절대 하지 마.

아래 대화에서 마지막 챗봇 질문/말에 대해,
청소년이 실제로 할 법한 자연스러운 답변 3가지를 만들어줘.

조건:
  - 각 답변은 서로 다른 감정이나 입장을 반영해야 해 (긍정적/중립적/부정적 또는 다양한 관점)
  - 10~20자 내외의 짧고 자연스러운 말로 (너무 완벽한 문장 말고, 실제 청소년이 말하듯)
  - 반말 또는 편한 말투로
  - 답변이 대화 맥락에 맞아야 해

반환 형식 (JSON만):
{"suggestions": ["답변1", "답변2", "답변3"]}
"""


def generate_suggestions(
    api_key: str,
    messages: list[dict],
    model: str = "gpt-4o",
) -> list[str]:
    """
    마지막 챗봇 메시지에 대한 답변 추천 3개 생성.
    마지막 메시지가 assistant가 아니면 빈 리스트 반환.
    """
    clean = [m for m in messages if m.get("role") in ("user", "assistant")]
    if not clean or clean[-1].get("role") != "assistant":
        return []

    client   = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SUGGEST_PROMPT},
            {"role": "user",   "content": str(clean[-6:])},  # 최근 6개 메시지만
        ],
        temperature=0.9,
        max_tokens=200,
    )
    raw = response.choices[0].message.content.strip()
    try:
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        return json.loads(raw[start:end]).get("suggestions", [])
    except Exception:
        return []

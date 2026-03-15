"""
chat.py — 채팅 화면 렌더링
흐름: 인트로 → 설문 → 스타일 선택 → 정보수집 채팅 → 요약 확인 → 인지 재구조화
"""
import streamlit as st
from llm import stream_chat, check_info_sufficient, extract_distortions, check_distortion_sufficient
from sidebar import SidebarConfig

STYLES = {
    "detective": {
        "label": "🔍 분석적 탐정형",
        "desc": "논리적으로 생각을 함께 파헤쳐요",
        "prompt": (
            "너는 청소년을 돕는 따뜻한 인지 재구조화 상담사야. 상대는 14~19세 청소년이야.\n"
            "말투는 부드럽고 따뜻한 존댓말을 써. 딱딱하거나 심문하듯 질문하지 마.\n"
            "공감을 먼저 충분히 표현한 다음, 자연스럽게 생각을 탐색해.\n"
            "예: '그랬군요, 정말 힘드셨겠어요', '그 상황에서 어떤 생각이 제일 먼저 떠올랐나요?'\n"
            "한 번에 하나의 질문만 해. 직접 질문 대신 '~것 같은데, 맞나요?' 같은 간접 탐색도 자주 써.\n"
            "이미 나온 정보를 다시 묻지 마. 대화 흐름을 자연스럽게 이어가."
        ),
        "avatar": "🔍", "color": "#eef2ff", "border": "#c7d2fe",
    },
    "friend": {
        "label": "🤗 따뜻한 친구형",
        "desc": "공감 먼저, 옆에서 같이 느껴줘요",
        "prompt": (
            "너는 청소년의 가장 친한 친구야. 반말로 자연스럽게 대화해.\n"
            "상대가 힘든 말을 하면 먼저 충분히 공감해줘. '진짜? 그게 너무 힘들었겠다ㅠ', '맞아 그럴 만해' 같은 말로.\n"
            "질문은 한 번에 하나만, 대화 중간에 자연스럽게 녹여내.\n"
            "이미 말한 내용은 다시 묻지 말고, '그래서 그때 엄청 속상했겠다~' 처럼 이어받아.\n"
            "이모지는 가끔, 자연스럽게. 너무 많으면 오히려 어색해.\n"
            "절대 상담사처럼 굴지 마. 그냥 옆에서 들어주는 친구처럼."
        ),
        "avatar": "🤗", "color": "#fff7ed", "border": "#fed7aa",
    },
    "sibling": {
        "label": "😎 쿨한 형·누나형",
        "desc": "솔직하고 시원하게 얘기해줘요",
        "prompt": (
            "너는 청소년 동생과 편하게 얘기 나누는 쿨한 형 또는 누나야. 반말로 대화해.\n"
            "무겁지 않게, 담백하고 솔직하게 말해. '아 진짜? 그거 좀 억울하겠다', '그럴 수 있지~' 같은 톤.\n"
            "공감을 가볍게 표현하되, 진심이 느껴지게 해. 형식적인 위로는 하지 마.\n"
            "질문은 자연스럽게, 한 번에 하나. 이미 한 말은 다시 묻지 마.\n"
            "분위기가 무거워지면 살짝 유머를 섞어도 돼. 단, 감정을 무시하지는 마.\n"
            "심문하듯 캐묻는 건 절대 하지 마. 그냥 편하게 대화하는 느낌으로."
        ),
        "avatar": "😎", "color": "#f0fdf4", "border": "#bbf7d0",
    },
    "coach": {
        "label": "🧘 차분한 코치형",
        "desc": "천천히 함께 정리하고 방향을 찾아요",
        "prompt": (
            "너는 청소년을 돕는 차분하고 신뢰감 있는 멘탈 코치야. 따뜻한 존댓말을 써.\n"
            "급하게 해결하려 하지 말고, 천천히 감정과 생각을 같이 정리해.\n"
            "공감 먼저, 그 다음에 부드럽게 탐색. '많이 힘드셨겠어요', '그 마음이 이해돼요' 같은 말을 자주 써.\n"
            "한 번에 질문 하나만. '혹시 그때 어떤 생각이 들었는지 조금 더 얘기해줄 수 있어요?' 처럼 부드럽게.\n"
            "이미 나온 내용은 반드시 인정하고 이어가. 같은 걸 다시 묻지 마.\n"
            "대화 끝에는 작은 것이라도 긍정적인 방향을 함께 찾아줘."
        ),
        "avatar": "🧘", "color": "#f0f9ff", "border": "#bae6fd",
    },
}

# 정보 수집 단계 전용 시스템 프롬프트
INFO_GATHERING_SUFFIX = """

[현재 단계: 정보 수집 — 핵심 원칙]
지금은 상황을 파악하는 단계야. 아래 원칙을 반드시 지켜.

파악해야 할 4가지 (자연스러운 대화 흐름 안에서):
  1. 어떤 상황/사건이 있었는지
  2. 그 상황에서 어떤 생각이 들었는지
  3. 그 생각으로 어떤 감정을 느꼈는지
  4. 그 감정이 얼마나 강했는지

절대 하지 말아야 할 것:
  - 한 번에 여러 질문 금지. 반드시 하나만.
  - 이미 상대가 말한 정보를 다시 묻는 것 금지.
  - '어떤 생각이 드셨나요?', '감정의 강도는?' 같은 딱딱한 설문 형식 금지.
  - 연속 질문 금지. 공감 → 질문 순서를 반드시 지켜.

좋은 예시:
  - '엄마한테 혼나서 많이 속상했겠다. 그때 혼자 어떤 생각 들었어?'
  - '진짜 힘들었겠다. 그 순간 머릿속에 뭔가 맴돌지 않았어?'
  - '그런 상황이 반복되면 더 지치기 마련이지. 요즘 그런 일이 자주 있어?'

조언이나 재구조화는 아직 하지 마. 먼저 충분히 듣는 게 목표야.
"""

REFRAMING_SUFFIX = """

[현재 단계: 인지 재구조화]
사용자의 상황, 생각, 감정을 충분히 파악했어.
이제 본격적으로 인지 재구조화를 도와줘:
- 생각 패턴의 인지 왜곡을 부드럽게 탐색
- 다른 시각이나 관점 제시
- 보다 균형잡힌 생각으로 이끌기
"""

DISTORTION_SUFFIX = """

[현재 단계: 인지왜곡 탐색]
사용자의 마음 속 부정적인 생각 패턴을 함께 자연스럽게 탐색하는 단계야.

탐색해야 할 4가지 (대화 흐름 속에서 자연스럽게):
  1. 자동적 사고  — 그 순간 가장 먼저 떠오른 부정적인 생각이 뭔지
  2. 반복 패턴    — 이런 생각이 자주 반복되는지, 비슷한 상황에서도 그런지
  3. 극단성       — "항상", "절대", "완전히", "다", "절대" 같은 표현을 쓰는지
  4. 증거         — 그 생각을 뒷받침하는 실제 근거가 있는지, 아니면 느낌인지

인지왜곡 유형 참고 (탐색 시 활용):
  - 흑백 사고: "1등 아니면 패배자" 처럼 중간이 없는 극단적 판단
  - 과잉 일반화: 한 번 일어난 일을 "항상 그래"로 확대
  - 부정적 편향: 좋은 건 안 보고 나쁜 것만 집중
  - 긍정 축소화: 잘한 건 "별거 아니야", "운이었어"로 무시
  - 성급한 판단: 증거 없이 "저 사람은 나를 싫어해"로 단정
  - 확대와 축소: 작은 실수를 "다 망했어", "인생 끝"으로 과장
  - 감정적 추론: "불안하니까 나쁜 일 생길 거야"처럼 느낌을 사실로 믿음
  - 해야 한다 진술: "나는 항상 잘해야 해"처럼 비현실적 기준
  - 낙인찍기: "나는 바보야", "나는 실패자야"처럼 자신을 규정
  - 개인화: "엄마가 화난 건 다 내 탓이야"처럼 모든 걸 자기 책임으로

대화 원칙:
  - 4가지를 순서대로 캐묻지 마. 대화 흐름에서 자연스럽게 녹여내.
  - 한 번에 하나씩만. 공감 먼저, 탐색은 그 다음.
  - 구체적인 부정적 마음을 충분히 꺼낼 수 있도록 도와줘.
  - "항상 그런 것 같아? 아니면 이번에 특히 그랬던 건지?" 처럼 부드럽게.
  - 틀렸다고 지적하는 게 아니라, 함께 살펴보는 느낌으로.
  - 청소년이 쉽게 이해할 수 있는 말로. 어려운 심리 용어 금지.
  - 탐색이 충분히 됐다 싶으면, 부드럽게 다음 단계를 준비해줘.
"""

REFRAMING_SUFFIX = """

[현재 단계: 인지 재구조화]
인지왜곡 패턴을 확인했어. 이제 더 균형잡힌 시각으로 생각을 바꿔나가는 단계야.
- 왜곡된 생각 대신 현실적이고 균형잡힌 대안 생각을 함께 찾아줘
- "그럼 이렇게 생각해볼 수도 있지 않을까요?" 식으로 제안
- 작은 변화도 충분히 인정하고 격려해줘
- 청소년 눈높이에 맞는 쉬운 말로
"""

MOOD_EMOJIS = ["😭", "😢", "😟", "😕", "😐", "🙂", "😊", "😄", "😁", "🤩", "🥳"]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.stApp { background-color: #f7f9fc; }
section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e8edf2; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background-color: #e8f4fd; border-radius: 16px; padding: 12px 16px; margin: 6px 0;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    background-color: #ffffff; border-radius: 16px; border: 1px solid #e8edf2;
    padding: 12px 16px; margin: 6px 0;
}
.stChatInputContainer { border-top: 1px solid #e8edf2; background-color: #f7f9fc; padding-top: 8px; }
textarea[data-testid="stChatInput"] {
    border-radius: 20px !important; border: 1.5px solid #d0dce8 !important;
    background-color: #ffffff !important; font-family: 'Noto Sans KR', sans-serif !important;
    font-size: 0.95rem !important;
}
h1 { font-size: 1.5rem !important; font-weight: 700 !important; color: #2c3e50 !important; }
hr  { border-color: #e8edf2 !important; margin: 8px 0 16px 0 !important; }

@keyframes pageEnter {
    from { opacity: 0; transform: translateY(24px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pageEnterLeft {
    from { opacity: 0; transform: translateX(-20px); }
    to   { opacity: 1; transform: translateX(0); }
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(18px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInSlow { 0% { opacity: 0; } 40% { opacity: 0; } 100% { opacity: 1; } }
@keyframes scaleIn {
    from { opacity: 0; transform: scale(0.95) translateY(12px); }
    to   { opacity: 1; transform: scale(1) translateY(0); }
}

.page-enter { animation: pageEnter 0.45s cubic-bezier(0.22, 1, 0.36, 1) both; }
.page-enter .stagger-1 { animation: pageEnter 0.4s cubic-bezier(0.22,1,0.36,1) 0.05s both; opacity: 0; animation-fill-mode: forwards; }
.page-enter .stagger-2 { animation: pageEnter 0.4s cubic-bezier(0.22,1,0.36,1) 0.15s both; opacity: 0; animation-fill-mode: forwards; }
.page-enter .stagger-3 { animation: pageEnter 0.4s cubic-bezier(0.22,1,0.36,1) 0.25s both; opacity: 0; animation-fill-mode: forwards; }
.page-enter .stagger-4 { animation: pageEnter 0.4s cubic-bezier(0.22,1,0.36,1) 0.35s both; opacity: 0; animation-fill-mode: forwards; }
.page-enter .stagger-btn { animation: scaleIn 0.4s cubic-bezier(0.22,1,0.36,1) 0.45s both; opacity: 0; animation-fill-mode: forwards; }

.intro-wrap {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; min-height: 28vh; text-align: center; padding: 40px 20px 16px;
}
.intro-icon { font-size: 4rem; animation: fadeIn 0.8s ease both; animation-delay: 0.1s; margin-bottom: 20px; }
.intro-title {
    font-size: 2rem; font-weight: 700; color: #1e293b; letter-spacing: -0.5px;
    animation: fadeIn 0.9s ease both; animation-delay: 0.5s; opacity: 0; animation-fill-mode: forwards;
}
.intro-sub {
    font-size: 1rem; color: #64748b; font-weight: 300; margin-top: 10px;
    animation: fadeIn 0.9s ease both; animation-delay: 1.1s; opacity: 0; animation-fill-mode: forwards;
}
.intro-divider {
    width: 40px; height: 2px; background: linear-gradient(90deg, #93c5fd, #6ee7b7);
    border-radius: 2px; margin: 20px auto;
    animation: fadeInSlow 2s ease both; animation-delay: 0.3s; opacity: 0; animation-fill-mode: forwards;
}
.notice-wrap { animation: fadeIn 1s ease both; animation-delay: 1.6s; opacity: 0; animation-fill-mode: forwards; }
.intro-btn-wrap {
    animation: fadeIn 1s ease both; animation-delay: 2.4s; opacity: 0; animation-fill-mode: forwards;
    margin-top: 8px; width: 100%; max-width: 280px;
}
.notice-card {
    background: #ffffff; border: 1px solid #e8edf2; border-radius: 16px;
    padding: 18px 22px; margin-bottom: 10px;
    font-size: 0.88rem; color: #4a5568; line-height: 1.8; text-align: left;
}
.notice-card-title { font-size: 0.97rem; font-weight: 700; color: #1e293b; margin-bottom: 6px; }
.notice-card-sub   { font-size: 0.82rem; color: #64748b; margin-bottom: 10px; }
.notice-row { display: flex; gap: 6px; margin: 3px 0; align-items: flex-start; }
.notice-warn {
    background: #fff7ed; border: 1px solid #fed7aa; border-radius: 16px;
    padding: 16px 20px; margin-bottom: 10px;
    font-size: 0.86rem; color: #92400e; line-height: 1.75; text-align: left;
}
.notice-warn b { color: #b45309; }
.survey-card { background: #ffffff; border: 1px solid #e8edf2; border-radius: 20px; padding: 28px 32px; margin: 8px 0 24px 0; }
.survey-title { font-size: 1.05rem; font-weight: 700; color: #2c3e50; margin-bottom: 4px; }
.survey-sub   { font-size: 0.85rem; color: #8a9bb0; margin-bottom: 20px; }
.style-card { border-radius: 16px; padding: 18px 20px; margin-bottom: 4px; }
.style-name { font-weight: 700; font-size: 1rem; color: #2c3e50; }
.style-desc { font-size: 0.82rem; color: #6b7280; margin-top: 2px; }
.welcome-card {
    background: #ffffff; border: 1px solid #e8edf2; border-radius: 16px;
    padding: 20px 24px; margin: 16px 0 24px 0; color: #4a5568; font-size: 0.92rem; line-height: 1.7;
    animation: scaleIn 0.5s cubic-bezier(0.22,1,0.36,1) 0.1s both; opacity: 0; animation-fill-mode: forwards;
}
.welcome-card b { color: #2c7be5; }

/* ── 요약 확인 카드 ── */
.summary-card {
    background: linear-gradient(135deg, #f0f9ff 0%, #f0fdf4 100%);
    border: 1.5px solid #7dd3fc;
    border-radius: 20px;
    padding: 24px 28px;
    margin: 12px 0 20px 0;
    animation: scaleIn 0.5s cubic-bezier(0.22,1,0.36,1) both;
}
.summary-card-title {
    font-size: 1rem; font-weight: 700; color: #0369a1; margin-bottom: 14px;
}
.summary-row {
    display: flex; gap: 10px; margin: 8px 0; align-items: flex-start;
    font-size: 0.9rem; color: #334155; line-height: 1.6;
}
.summary-label {
    font-size: 0.75rem; font-weight: 700; color: #0284c7;
    background: #e0f2fe; border-radius: 6px; padding: 2px 7px;
    min-width: 44px; text-align: center; margin-top: 2px; flex-shrink: 0;
}
.summary-quote {
    background: #ffffff; border-left: 3px solid #7dd3fc;
    border-radius: 0 10px 10px 0; padding: 10px 14px;
    margin: 10px 0 16px 0; font-size: 0.9rem; color: #475569;
    line-height: 1.7; font-style: italic;
}
/* 인지왜곡 결과 카드 */
.distortion-result {
    background: #ffffff;
    border: 1.5px solid #ddd6fe;
    border-radius: 20px;
    padding: 22px 26px;
    margin: 14px 0 20px 0;
    animation: scaleIn 0.5s cubic-bezier(0.22,1,0.36,1) both;
}
.distortion-result-title {
    font-size: 1rem; font-weight: 700; color: #5b21b6; margin-bottom: 14px;
}
.distortion-item {
    background: linear-gradient(135deg, #faf5ff 0%, #f5f3ff 100%);
    border: 1px solid #e9d5ff;
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.distortion-item:last-child { margin-bottom: 0; }
.distortion-rank {
    font-size: 0.72rem; font-weight: 700; color: #7c3aed;
    background: #ede9fe; border-radius: 6px;
    padding: 2px 8px; display: inline-block; margin-bottom: 6px;
}
.distortion-name {
    font-size: 0.95rem; font-weight: 700; color: #3b0764; margin-bottom: 4px;
}
.distortion-en {
    font-size: 0.75rem; color: #a78bfa; margin-bottom: 8px;
}
.distortion-reason {
    font-size: 0.86rem; color: #4c1d95; line-height: 1.7; margin-bottom: 6px;
}
.distortion-quote {
    font-size: 0.82rem; color: #7c3aed; background: #ffffff;
    border-left: 3px solid #a78bfa; border-radius: 0 8px 8px 0;
    padding: 6px 10px; font-style: italic;
}

/* 인지왜곡 인트로 카드 */
.distortion-intro {
    background: linear-gradient(135deg, #faf5ff 0%, #ede9fe 100%);
    border: 1.5px solid #c4b5fd;
    border-radius: 20px;
    padding: 22px 26px;
    margin: 12px 0 20px 0;
    animation: scaleIn 0.5s cubic-bezier(0.22,1,0.36,1) both;
}
.distortion-intro-title {
    font-size: 1rem; font-weight: 700; color: #5b21b6; margin-bottom: 10px;
}
.distortion-intro-body {
    font-size: 0.88rem; color: #4c1d95; line-height: 1.8;
}
.distortion-intro-example {
    background: #ffffff; border-radius: 10px; padding: 10px 14px;
    margin-top: 12px; font-size: 0.84rem; color: #6d28d9; line-height: 1.75;
}
.phase-badge {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 0.75rem; font-weight: 600; padding: 3px 10px;
    border-radius: 20px; margin-bottom: 8px;
}
.phase-collecting { background: #fef9c3; color: #854d0e; border: 1px solid #fde047; }
.phase-distortion { background: #ede9fe; color: #5b21b6; border: 1px solid #c4b5fd; }
.phase-reframing  { background: #dcfce7; color: #166534; border: 1px solid #86efac; }
</style>
"""

NOTICE_HTML = """
<div class="notice-wrap">
  <div class="notice-card">
    <div class="notice-card-title">📌 이 챗봇은 무엇인가요?</div>
    <div class="notice-card-sub">교육 및 자기돌봄 도구입니다. 전문 심리치료가 아닙니다.</div>
    <div class="notice-row">✅&nbsp;<span><b>목적</b>: 인지행동치료(CBT) 기법을 활용한 자기 탐색 도구</span></div>
    <div class="notice-row">✅&nbsp;<span><b>역할</b>: 생각과 감정 패턴을 인식하도록 돕는 보조 도구</span></div>
    <div class="notice-row">❌&nbsp;<span><b>아닌 것</b>: 심리 상담·진단·치료의 대체 수단</span></div>
  </div>
  <div class="notice-card">
    <div class="notice-card-title">🚫 이 챗봇이 할 수 없는 것</div>
    <div class="notice-card-sub">이 AI는 절대로 다음을 대체할 수 없습니다.</div>
    <div class="notice-row">❌&nbsp;<span>자격을 갖춘 심리상담사나 정신건강 전문가</span></div>
    <div class="notice-row">❌&nbsp;<span>심리 진단이나 치료</span></div>
    <div class="notice-row">❌&nbsp;<span>응급 위기 개입</span></div>
    <div class="notice-row">❌&nbsp;<span>약물 처방이나 의학적 조언</span></div>
  </div>
  <div class="notice-warn">
    ⚠️ <b>이 챗봇은 AI입니다. 진짜 사람이 아닙니다.</b><br>
    AI는 당신을 진정으로 이해하거나 공감할 수 없습니다.<br>
    AI는 복잡한 정신건강 문제를 다룰 수 없으며, 실수하거나 부정확한 정보를 줄 수 있습니다.
  </div>
</div>
"""


def apply_styles() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def init_session() -> None:
    defaults = {
        "intro_done":      False,
        "survey_done":     False,
        "style_chosen":    False,
        "messages":        [],
        "user_gender":     None,
        "user_age":        None,
        "user_mood":       None,
        "chat_style":      None,
        # 정보 수집 관련
        "phase":           "collecting",   # "collecting" | "confirming" | "distortion" | "reframing"
        "collected_info":  None,           # check_info_sufficient 결과
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ── STEP 0 : 인트로 ───────────────────────────────────────────────────────────
def render_intro() -> None:
    st.markdown(
        '<div class="intro-wrap">'
        '<div class="intro-icon">🌱</div>'
        '<div class="intro-title">마음 다시 보기</div>'
        '<div class="intro-sub">생각을 새롭게, 마음을 가볍게</div>'
        '<div class="intro-divider"></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(NOTICE_HTML, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("<div class='intro-btn-wrap' style='margin:0 auto;'>", unsafe_allow_html=True)
        if st.button("내용을 확인했습니다. 시작하기 →", type="primary", use_container_width=True):
            st.session_state.intro_done = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def render_header() -> None:
    st.title("🌱 마음 다시 보기")
    st.caption("생각을 새롭게, 마음을 가볍게")
    st.divider()


# ── STEP 1 : 설문 ─────────────────────────────────────────────────────────────
def render_survey() -> None:
    st.markdown(
        '<div class="page-enter"><div class="stagger-1 survey-card">'
        '<div class="survey-title">시작하기 전에 간단히 알려주세요 👋</div>'
        '<div class="survey-sub">입력하신 정보는 더 잘 도와드리기 위해서만 사용돼요.</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        gender = st.radio("성별", options=["남성", "여성"], index=0)
    with col2:
        age = st.selectbox("나이", options=list(range(14, 20)), index=2,
                           format_func=lambda x: f"{x}세")
    st.markdown("<br>", unsafe_allow_html=True)
    mood = st.slider("지금 기분이 어때요?  (0 = 매우 나쁨 · 10 = 매우 좋음)",
                     min_value=0, max_value=10, value=5, step=1)
    st.markdown(
        f"<div style='text-align:center;font-size:2.2rem;margin:-8px 0 16px 0;"
        f"animation:pageEnter 0.4s ease both;'>{MOOD_EMOJIS[mood]}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("다음 →", type="primary", use_container_width=True):
        st.session_state.survey_done = True
        st.session_state.user_gender = gender
        st.session_state.user_age    = age
        st.session_state.user_mood   = mood
        st.rerun()


# ── STEP 2 : 스타일 선택 ─────────────────────────────────────────────────────
def render_style_select() -> None:
    st.markdown(
        '<div class="page-enter"><div class="stagger-1 survey-card">'
        '<div class="survey-title">어떤 스타일로 대화할까요? 💬</div>'
        '<div class="survey-sub">나와 잘 맞는 대화 스타일을 골라보세요.</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )
    keys    = list(STYLES.keys())
    stagger = ["stagger-2", "stagger-3", "stagger-2", "stagger-3"]
    for i, row in enumerate([keys[:2], keys[2:]]):
        cols = st.columns(2)
        for j, (col, key) in enumerate(zip(cols, row)):
            s = STYLES[key]
            bg, bdr, lbl, dsc = s["color"], s["border"], s["label"], s["desc"]
            sc = stagger[i * 2 + j]
            with col:
                st.markdown(
                    f'<div class="page-enter"><div class="{sc} style-card" style="background:{bg};border:1.5px solid {bdr};">'
                    f'<div class="style-name">{lbl}</div><div class="style-desc">{dsc}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
                if st.button("선택", key=f"style_{key}", use_container_width=True):
                    st.session_state.style_chosen = True
                    st.session_state.chat_style   = key
                    st.rerun()


# ── STEP 3 : 채팅 ─────────────────────────────────────────────────────────────
def _get_api_key() -> str:
    try:
        return st.secrets["OPENAI_API_KEY"]
    except Exception:
        return ""


def _phase_badge() -> None:
    """현재 단계 뱃지 표시."""
    phase = st.session_state.get("phase", "collecting")

    if phase == "collecting":
        st.markdown(
            "<div class='phase-badge phase-collecting'>💬 어떤 일이 있었는지 들어보는 중이에요</div>",
            unsafe_allow_html=True,
        )
    elif phase == "distortion":
        st.markdown(
            "<div class='phase-badge phase-distortion'>🔎 생각 속에 숨은 패턴을 찾아보는 중이에요</div>",
            unsafe_allow_html=True,
        )
    elif phase == "reframing":
        st.markdown(
            "<div class='phase-badge phase-reframing'>🌱 생각을 함께 새롭게 바라보는 중이에요</div>",
            unsafe_allow_html=True,
        )


def render_history() -> None:
    if not st.session_state.messages:
        style = STYLES[st.session_state.chat_style]
        mood  = st.session_state.user_mood
        emoji = MOOD_EMOJIS[mood]
        bdr, av, lbl = style["border"], style["avatar"], style["label"]
        st.markdown(
            f"<div class='welcome-card' style='border-color:{bdr};'>"
            f"{av} <b>{lbl}</b> 스타일로 대화를 시작할게요!<br><br>"
            f"오늘 기분이 <b>{mood}점</b>이군요 {emoji}&nbsp;"
            f"어떤 일이 있었는지 편하게 이야기해 주세요. 판단 없이 들을게요. 🤍"
            f"</div>",
            unsafe_allow_html=True,
        )

    _phase_badge()

    for msg in st.session_state.messages:
        # 인지왜곡 인트로 카드는 특수 태그로 저장된 것을 여기서 렌더링
        if msg.get("role") in ("__distortion_intro__", "__distortion_result__"):
            st.markdown(msg["content"], unsafe_allow_html=True)
            continue
        avatar = "🧑" if msg["role"] == "user" else STYLES[st.session_state.chat_style]["avatar"]
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])


def render_summary_confirm(info: dict) -> None:
    """수집된 정보를 카드로 보여주고 확인/수정 버튼 표시."""
    situation = info.get("situation") or ""
    thought   = info.get("thought")   or ""
    emotion   = info.get("emotion")   or ""
    intensity = info.get("intensity") or ""
    summary   = info.get("summary")   or ""

    # 감정 강도 표시 조합
    emotion_str = emotion
    if intensity and str(intensity).lower() not in ("none", "null", ""):
        emotion_str = f"{emotion} ({intensity})"

    st.markdown(
        '<div class="summary-card">'
        '<div class="summary-card-title">📋 지금까지 들은 내용을 정리해볼게요</div>'
        f'<div class="summary-row"><span class="summary-label">상황</span><span>{situation}</span></div>'
        f'<div class="summary-row"><span class="summary-label">생각</span><span>{thought}</span></div>'
        f'<div class="summary-row"><span class="summary-label">감정</span><span>{emotion_str}</span></div>'
        f'<div class="summary-quote">"{summary}"</div>'
        '<div style="font-size:0.88rem;color:#475569;margin-top:4px;">이 내용이 맞나요?</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 맞아요, 계속할게요", type="primary", use_container_width=True, key="confirm_yes"):
            st.session_state.phase          = "distortion"
            st.session_state.collected_info = info
            _start_distortion()
    with col2:
        if st.button("✏️ 조금 달라요", use_container_width=True, key="confirm_no"):
            st.session_state.phase          = "collecting"
            st.session_state.collected_info = None
            # 수정 안내 메시지
            st.session_state.messages.append({
                "role":    "assistant",
                "content": "그렇군요! 어떤 부분이 다른지 조금 더 이야기해 주실 수 있나요? 😊",
            })
            st.rerun()


def _call_gpt_once(system: str, trigger: str, max_tokens: int = 600) -> None:
    """시스템 프롬프트 + 현재 대화 기반으로 챗봇 메시지 한 번 생성 후 저장."""
    api_key = _get_api_key()
    if not api_key:
        st.rerun()
        return
    # 특수 role(인트로 카드 등)은 OpenAI API에 전달하지 않음
    api_messages = [
        m for m in st.session_state.messages
        if m.get("role") in ("user", "assistant")
    ]
    client   = __import__("openai").OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            *api_messages,
            {"role": "user", "content": trigger},
        ],
        temperature=0.7,
        max_tokens=max_tokens,
    )
    reply = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()


DISTORTION_INTRO_HTML = (
    "<div class='distortion-intro'><div class='distortion-intro-title'>🔎 이제 생각 속 패턴을 같이 찾아볼게요</div><div class='distortion-intro-body'>우리가 힘들 때, 머릿속에서 생각이 조금 과장되거나 한쪽으로 치우치는 경우가 있어요.<br>이걸 <b>인지왜곡</b>이라고 하는데, 나쁜 게 아니에요. 누구나 그럴 수 있어요. 😊<br><br>지금부터 아까 나눈 이야기 속에서 혹시 그런 패턴이 있었는지 함께 살펴볼게요.<div class='distortion-intro-example'>예를 들면 이런 것들이에요 👇<br>&#8226; <b>흑백논리</b> &#8212; &#39;이게 안 되면 다 끝이야&#39;<br>&#8226; <b>마음읽기</b> &#8212; &#39;저 사람이 나를 싫어하는 게 분명해&#39;<br>&#8226; <b>과잉일반화</b> &#8212; &#39;나는 항상 이렇게 실패해&#39;</div></div></div>"
)

def _render_distortion_result_html(distortions: list) -> str:
    """인지왜곡 결과 카드 HTML 생성."""
    if not distortions:
        return ""
    rank_labels = ["1순위", "2순위", "3순위"]
    items = ""
    for i, d in enumerate(distortions[:3]):
        rank  = rank_labels[i] if i < len(rank_labels) else f"{i+1}순위"
        name  = d.get("type", "")
        en    = d.get("english", "")
        reason= d.get("reason", "")
        quote = d.get("quote", "")
        items += (
            f"<div class='distortion-item'>"
            f"<div class='distortion-rank'>{rank}</div>"
            f"<div class='distortion-name'>{name}</div>"
            f"<div class='distortion-en'>{en}</div>"
            f"<div class='distortion-reason'>{reason}</div>"
            + (f"<div class='distortion-quote'>&#34;{quote}&#34;</div>" if quote else "")
            + "</div>"
        )
    return (
        "<div class='distortion-result'>"
        "<div class='distortion-result-title'>🧩 발견된 생각 패턴이에요</div>"
        + items +
        "</div>"
    )


def _start_distortion() -> None:
    """인지왜곡 탐색 시작 — 인트로 카드를 messages에 저장 후 챗봇 첫 메시지 생성."""
    # 인트로 카드를 대화 기록 맨 아래에 삽입 (특수 role로 구분)
    st.session_state.messages.append({
        "role":    "__distortion_intro__",
        "content": DISTORTION_INTRO_HTML,
    })
    style = STYLES[st.session_state.chat_style]
    info  = st.session_state.collected_info
    system = (
        style["prompt"] + DISTORTION_SUFFIX
        + f"\n\n[파악된 사용자 정보]\n"
        f"상황: {info.get('situation')}\n"
        f"생각: {info.get('thought')}\n"
        f"감정: {info.get('emotion')} ({info.get('intensity')})\n"
        f"성별: {st.session_state.user_gender}, 나이: {st.session_state.user_age}세\n"
        + "\n위기 상황(자해·자살 언급) 감지 시 즉시 청소년 전화 1388을 안내해."
    )
    _call_gpt_once(system, "[정보 확인 완료. 인지왜곡 탐색을 자연스럽게 시작해줘.]")


def _start_reframing() -> None:
    """재구조화 시작 — 인지왜곡 결과 카드 삽입 후 챗봇 첫 메시지 생성."""
    # 인지왜곡 추출 후 결과 카드를 messages에 삽입
    api_key = _get_api_key()
    if api_key:
        clean = [m for m in st.session_state.messages if m.get("role") in ("user", "assistant")]
        distortions = extract_distortions(api_key, clean)
        if distortions:
            result_html = _render_distortion_result_html(distortions)
            st.session_state.messages.append({
                "role":    "__distortion_result__",
                "content": result_html,
            })
            st.session_state["last_distortions"] = distortions
    style = STYLES[st.session_state.chat_style]
    info  = st.session_state.collected_info
    system = (
        style["prompt"] + REFRAMING_SUFFIX
        + f"\n\n[파악된 사용자 정보]\n"
        f"상황: {info.get('situation')}\n"
        f"생각: {info.get('thought')}\n"
        f"감정: {info.get('emotion')} ({info.get('intensity')})\n"
        f"성별: {st.session_state.user_gender}, 나이: {st.session_state.user_age}세\n"
        + "\n위기 상황(자해·자살 언급) 감지 시 즉시 청소년 전화 1388을 안내해."
    )
    _call_gpt_once(system, "[인지왜곡 탐색 완료. 재구조화를 시작해줘.]")


def render_chat_input(config: SidebarConfig) -> None:
    phase = st.session_state.get("phase", "collecting")

    # ── 확인 단계: 입력창 대신 확인 카드 ────────────────────────────────────
    if phase == "confirming":
        render_summary_confirm(st.session_state.get("collected_info", {}))
        return

    placeholder_text = (
        "오늘 어떤 일이 있었나요?" if phase == "collecting"
        else "네, 계속 이야기해 주세요" if phase == "distortion"
        else "자유롭게 이야기해 주세요"
    )

    if prompt := st.chat_input(placeholder_text):
        api_key = _get_api_key()
        if not api_key:
            st.error("⚠️ `.streamlit/secrets.toml`에 OPENAI_API_KEY를 설정해주세요.")
            st.stop()

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

        # ── 정보 수집 단계: 챗봇 응답 전에 먼저 충분성 체크 ────────────────
        if phase == "collecting":
            clean_messages = [m for m in st.session_state.messages if m.get("role") in ("user", "assistant")]
            result = check_info_sufficient(api_key, clean_messages)

            if result.get("sufficient"):
                # 부정적 사건이 충분히 수집됨 → 요약 카드로 전환
                st.session_state.phase          = "confirming"
                st.session_state.collected_info = result
                st.rerun()

            elif result.get("negative") is False:
                # 긍정적인 대화만 있음 → 챗봇이 자연스럽게 전환 유도
                # INFO_GATHERING_SUFFIX에 힌트 추가해서 챗봇이 부드럽게 넘어가도록
                st.session_state["_hint_positive"] = True

        style  = STYLES[st.session_state.chat_style]

        # 긍정 대화 힌트가 있으면 suffix에 전환 유도 문구 추가
        if phase == "collecting" and st.session_state.pop("_hint_positive", False):
            suffix = INFO_GATHERING_SUFFIX + """

[추가 지시]
지금까지 사용자가 즐거웠던 이야기를 해줬어. 충분히 공감하고 기뻐해줘.
그런 다음, 자연스럽게 "혹시 요즘 힘들거나 속상한 일은 없어?" 같은 식으로
부드럽게 넘어가봐. 억지스럽지 않게, 대화 흐름에 맞게.
"""
        else:
            if phase == "collecting":
                suffix = INFO_GATHERING_SUFFIX
            elif phase == "distortion":
                suffix = DISTORTION_SUFFIX
            else:
                suffix = REFRAMING_SUFFIX

        # 재구조화 단계면 수집된 정보도 함께 전달
        extra = ""
        if phase in ("reframing", "distortion") and st.session_state.collected_info:
            info  = st.session_state.collected_info
            extra = (
                f"\n\n[파악된 사용자 정보]\n"
                f"상황: {info.get('situation')}\n"
                f"생각: {info.get('thought')}\n"
                f"감정: {info.get('emotion')} ({info.get('intensity')})\n"
            )

        system = (
            style["prompt"] + suffix + extra
            + f"\n\n[사용자 기본 정보] 성별: {st.session_state.user_gender}, "
            f"나이: {st.session_state.user_age}세, 기분 점수: {st.session_state.user_mood}/10"
            + "\n위기 상황(자해·자살 언급) 감지 시 즉시 청소년 전화 1388을 안내해."
        )

        with st.chat_message("assistant", avatar=style["avatar"]):
            placeholder   = st.empty()
            full_response = ""
            try:
                api_messages = [
                    m for m in st.session_state.messages
                    if m.get("role") in ("user", "assistant")
                ]
                for chunk in stream_chat(
                    api_key=api_key,
                    messages=api_messages,
                    system_prompt=system,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                ):
                    full_response += chunk
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
            except Exception as e:
                st.error(f"❌ 오류: {e}")
                st.stop()

        st.session_state.messages.append({"role": "assistant", "content": full_response})

        # ── 인지왜곡 탐색 단계: 충분히 파악됐으면 재구조화로 자동 전환 ────────
        if phase == "distortion":
            clean = [m for m in st.session_state.messages if m.get("role") in ("user", "assistant")]
            if check_distortion_sufficient(api_key, clean):
                st.session_state.phase = "reframing"
                _start_reframing()


def render_main(config: SidebarConfig) -> None:
    if not st.session_state.intro_done:
        render_intro()
    elif not st.session_state.survey_done:
        render_header()
        render_survey()
    elif not st.session_state.style_chosen:
        render_header()
        render_style_select()
    else:
        render_header()
        render_history()
        render_chat_input(config)

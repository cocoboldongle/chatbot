"""
chat.py — 채팅 화면 렌더링
흐름: 인트로(안내) → 설문 → 스타일 선택 → 채팅
"""
import streamlit as st
from llm import get_api_key, stream_chat
from sidebar import SidebarConfig

STYLES = {
    "detective": {
        "label": "🔍 분석적 탐정형",
        "desc": "논리적으로 생각을 함께 파헤쳐요",
        "prompt": (
            "너는 논리적이고 분석적인 인지 재구조화 상담사야.\n"
            "말투는 차분하고 정중한 존댓말을 사용해.\n"
            "감정보다 사실과 근거에 집중하고, '그 생각의 근거가 뭔지 같이 살펴볼까요?',\n"
            "'다른 가능성은 없을까요?' 같은 탐색적 질문을 즐겨 써.\n"
            "단계적으로 생각을 분해하고, 인지 왜곡 패턴(흑백논리, 과잉일반화 등)을 부드럽게 짚어줘.\n"
            "문장은 간결하고 명확하게, 불필요한 감탄사는 쓰지 마."
        ),
        "avatar": "🔍", "color": "#eef2ff", "border": "#c7d2fe",
    },
    "friend": {
        "label": "🤗 따뜻한 친구형",
        "desc": "공감 먼저, 옆에서 같이 느껴줘요",
        "prompt": (
            "너는 따뜻하고 공감 잘하는 친한 친구야. 반말로 대화해.\n"
            "'그랬구나~', '진짜 힘들었겠다ㅠ', '나도 그런 적 있어서 알 것 같아' 처럼\n"
            "감정을 먼저 충분히 받아주고 공감해줘.\n"
            "이모지도 자연스럽게 써도 돼 (너무 많지 않게).\n"
            "판단하지 말고 먼저 들어줘. 조언은 공감 뒤에, 부드럽게 해줘.\n"
            "'혹시 그 생각 말고 다른 시각으로 보면 어떨까?' 같은 자연스러운 재구조화 질문을 해줘."
        ),
        "avatar": "🤗", "color": "#fff7ed", "border": "#fed7aa",
    },
    "sibling": {
        "label": "😎 쿨한 형·누나형",
        "desc": "솔직하고 시원하게 얘기해줘요",
        "prompt": (
            "너는 쿨하고 솔직한 형 또는 누나야. 반말로 대화해.\n"
            "'야 그거 별거 아니야~', '솔직히 말하면' 같은 직접적이고 시원한 말투를 써.\n"
            "너무 감성적이거나 무겁지 않게, 가볍고 유머 있게 대화해도 돼.\n"
            "하지만 중요한 감정은 무시하지 말고 '아 근데 그게 좀 힘들긴 하겠다'처럼 인정해줘.\n"
            "'근데 진짜로, 그 생각이 100% 맞다고 확신해?' 같은 직설적인 재구조화 질문을 던져줘."
        ),
        "avatar": "😎", "color": "#f0fdf4", "border": "#bbf7d0",
    },
    "coach": {
        "label": "🧘 차분한 코치형",
        "desc": "천천히 함께 정리하고 방향을 찾아요",
        "prompt": (
            "너는 차분하고 신뢰감 있는 멘탈 코치야. 정중한 존댓말을 사용해.\n"
            "빠르게 해결하려 하지 말고, 천천히 생각을 정리할 수 있도록 도와줘.\n"
            "'지금 어떤 감정이 가장 크게 느껴지시나요?', '그 상황을 조금 더 자세히 말씀해 주실 수 있나요?' 같은\n"
            "차분하고 개방적인 질문을 써.\n"
            "구체적인 행동이나 관점 전환 방법을 제안할 때는 명확하고 실용적으로 말해줘.\n"
            "급하지 않게, 함께 호흡을 맞추는 느낌으로 대화해."
        ),
        "avatar": "🧘", "color": "#f0f9ff", "border": "#bae6fd",
    },
}

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

/* ── 공통 페이지 전환 애니메이션 ── */
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

/* 모든 화면 전환에 적용되는 래퍼 */
.page-enter {
    animation: pageEnter 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
}
/* 카드들을 순서대로 등장시키는 stagger */
.page-enter .stagger-1 { animation: pageEnter 0.4s cubic-bezier(0.22,1,0.36,1) 0.05s both; opacity: 0; animation-fill-mode: forwards; }
.page-enter .stagger-2 { animation: pageEnter 0.4s cubic-bezier(0.22,1,0.36,1) 0.15s both; opacity: 0; animation-fill-mode: forwards; }
.page-enter .stagger-3 { animation: pageEnter 0.4s cubic-bezier(0.22,1,0.36,1) 0.25s both; opacity: 0; animation-fill-mode: forwards; }
.page-enter .stagger-4 { animation: pageEnter 0.4s cubic-bezier(0.22,1,0.36,1) 0.35s both; opacity: 0; animation-fill-mode: forwards; }
.page-enter .stagger-btn { animation: scaleIn 0.4s cubic-bezier(0.22,1,0.36,1) 0.45s both; opacity: 0; animation-fill-mode: forwards; }

/* ── 인트로 전용 ── */
.intro-wrap {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; min-height: 28vh; text-align: center; padding: 40px 20px 16px;
}
.intro-icon { font-size: 4rem; animation: fadeIn 0.8s ease both; animation-delay: 0.1s; margin-bottom: 20px; }
.intro-title {
    font-size: 2rem; font-weight: 700; color: #1e293b; letter-spacing: -0.5px;
    animation: fadeIn 0.9s ease both; animation-delay: 0.5s;
    opacity: 0; animation-fill-mode: forwards;
}
.intro-sub {
    font-size: 1rem; color: #64748b; font-weight: 300; margin-top: 10px;
    animation: fadeIn 0.9s ease both; animation-delay: 1.1s;
    opacity: 0; animation-fill-mode: forwards;
}
.intro-divider {
    width: 40px; height: 2px;
    background: linear-gradient(90deg, #93c5fd, #6ee7b7);
    border-radius: 2px; margin: 20px auto;
    animation: fadeInSlow 2s ease both; animation-delay: 0.3s;
    opacity: 0; animation-fill-mode: forwards;
}
.notice-wrap {
    animation: fadeIn 1s ease both; animation-delay: 1.6s;
    opacity: 0; animation-fill-mode: forwards;
}
.intro-btn-wrap {
    animation: fadeIn 1s ease both; animation-delay: 2.4s;
    opacity: 0; animation-fill-mode: forwards;
    margin-top: 8px; width: 100%; max-width: 280px;
}

/* ── 안내 카드 ── */
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

/* ── 설문·스타일 카드 ── */
.survey-card { background: #ffffff; border: 1px solid #e8edf2; border-radius: 20px; padding: 28px 32px; margin: 8px 0 24px 0; }
.survey-title { font-size: 1.05rem; font-weight: 700; color: #2c3e50; margin-bottom: 4px; }
.survey-sub   { font-size: 0.85rem; color: #8a9bb0; margin-bottom: 20px; }
.style-card { border-radius: 16px; padding: 18px 20px; margin-bottom: 4px; }
.style-name { font-weight: 700; font-size: 1rem; color: #2c3e50; }
.style-desc { font-size: 0.82rem; color: #6b7280; margin-top: 2px; }

/* ── 채팅 웰컴 카드 ── */
.welcome-card {
    background: #ffffff; border: 1px solid #e8edf2; border-radius: 16px;
    padding: 20px 24px; margin: 16px 0 24px 0; color: #4a5568; font-size: 0.92rem; line-height: 1.7;
    animation: scaleIn 0.5s cubic-bezier(0.22,1,0.36,1) 0.1s both;
    opacity: 0; animation-fill-mode: forwards;
}
.welcome-card b { color: #2c7be5; }
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
        "intro_done":   False,
        "survey_done":  False,
        "style_chosen": False,
        "messages":     [],
        "user_gender":  None,
        "user_age":     None,
        "user_mood":    None,
        "chat_style":   None,
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


# ── STEP 1 : 설문 ─────────────────────────────────────────────────────────────
def render_header() -> None:
    st.title("🌱 마음 다시 보기")
    st.caption("생각을 새롭게, 마음을 가볍게")
    st.divider()


def render_survey() -> None:
    st.markdown(
        '<div class="page-enter">'
        '<div class="stagger-1 survey-card">'
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
        '<div class="page-enter">'
        '<div class="stagger-1 survey-card">'
        '<div class="survey-title">어떤 스타일로 대화할까요? 💬</div>'
        '<div class="survey-sub">나와 잘 맞는 대화 스타일을 골라보세요.</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )
    keys = list(STYLES.keys())
    stagger = ["stagger-2", "stagger-3", "stagger-2", "stagger-3"]
    for i, row in enumerate([keys[:2], keys[2:]]):
        cols = st.columns(2)
        for j, (col, key) in enumerate(zip(cols, row)):
            s = STYLES[key]
            bg, bdr, lbl, dsc = s["color"], s["border"], s["label"], s["desc"]
            sc = stagger[i * 2 + j]
            with col:
                st.markdown(
                    f'<div class="page-enter">'
                    f'<div class="{sc} style-card" style="background:{bg};border:1.5px solid {bdr};">'
                    f'<div class="style-name">{lbl}</div>'
                    f'<div class="style-desc">{dsc}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
                if st.button("선택", key=f"style_{key}", use_container_width=True):
                    st.session_state.style_chosen = True
                    st.session_state.chat_style   = key
                    st.rerun()


# ── STEP 3 : 채팅 ─────────────────────────────────────────────────────────────
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
            f"편하게 이야기해 주세요. 판단 없이 들을게요. 🤍"
            f"</div>",
            unsafe_allow_html=True,
        )
    for msg in st.session_state.messages:
        avatar = "🧑" if msg["role"] == "user" else STYLES[st.session_state.chat_style]["avatar"]
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])


def render_chat_input(config: SidebarConfig) -> None:
    if prompt := st.chat_input("오늘 어떤 생각이 드나요?"):
        api_key = get_api_key(config.api_key_input)
        if not api_key:
            st.error("⚠️ OpenAI API 키를 사이드바에 입력하거나 `.streamlit/secrets.toml`에 설정해주세요.")
            st.stop()

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

        style = STYLES[st.session_state.chat_style]
        enriched_system = (
            style["prompt"]
            + f"\n\n[사용자 정보] 성별: {st.session_state.user_gender}, "
            f"나이: {st.session_state.user_age}세, "
            f"오늘 기분 점수: {st.session_state.user_mood}/10"
            + "\n위기 상황(자해·자살 언급) 감지 시 즉시 청소년 전화 1388을 안내해."
        )

        with st.chat_message("assistant", avatar=style["avatar"]):
            placeholder   = st.empty()
            full_response = ""
            try:
                for chunk in stream_chat(
                    api_key=api_key,
                    messages=st.session_state.messages,
                    system_prompt=enriched_system,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                ):
                    full_response += chunk
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
            except Exception as e:
                st.error(f"❌ 오류가 발생했어요: {e}")
                st.stop()

        st.session_state.messages.append({"role": "assistant", "content": full_response})


def render_main(config: SidebarConfig) -> None:
    init_session()
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

"""
chat.py — 채팅 화면 렌더링
설문(onboarding) → 채팅 화면 순서로 진행됩니다.
"""
import streamlit as st
from llm import get_api_key, stream_chat
from sidebar import SidebarConfig


# ── 스타일 ────────────────────────────────────────────────────────────────────
def apply_styles() -> None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }

    .stApp { background-color: #f7f9fc; }

    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e8edf2;
    }

    /* 사용자 말풍선 */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        background-color: #e8f4fd;
        border-radius: 16px;
        padding: 12px 16px;
        margin: 6px 0;
    }

    /* 어시스턴트 말풍선 */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
        background-color: #ffffff;
        border-radius: 16px;
        border: 1px solid #e8edf2;
        padding: 12px 16px;
        margin: 6px 0;
    }

    .stChatInputContainer {
        border-top: 1px solid #e8edf2;
        background-color: #f7f9fc;
        padding-top: 8px;
    }

    textarea[data-testid="stChatInput"] {
        border-radius: 20px !important;
        border: 1.5px solid #d0dce8 !important;
        background-color: #ffffff !important;
        font-family: 'Noto Sans KR', sans-serif !important;
        font-size: 0.95rem !important;
    }

    h1 {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: #2c3e50 !important;
    }

    hr {
        border-color: #e8edf2 !important;
        margin: 8px 0 16px 0 !important;
    }

    /* 설문 카드 */
    .survey-card {
        background: #ffffff;
        border: 1px solid #e8edf2;
        border-radius: 20px;
        padding: 28px 32px;
        margin: 8px 0 24px 0;
    }

    .survey-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 4px;
    }

    .survey-sub {
        font-size: 0.85rem;
        color: #8a9bb0;
        margin-bottom: 20px;
    }

    /* 기분 이모지 행 */
    .mood-row {
        display: flex;
        justify-content: space-between;
        font-size: 1.4rem;
        margin-top: 4px;
        padding: 0 2px;
    }

    /* 웰컴 카드 */
    .welcome-card {
        background: #ffffff;
        border: 1px solid #e8edf2;
        border-radius: 16px;
        padding: 20px 24px;
        margin: 16px 0 24px 0;
        color: #4a5568;
        font-size: 0.92rem;
        line-height: 1.7;
    }

    .welcome-card b { color: #2c7be5; }
    </style>
    """, unsafe_allow_html=True)


# ── 헤더 ──────────────────────────────────────────────────────────────────────
def render_header() -> None:
    st.title("🌱 마음 다시 보기")
    st.caption("생각을 새롭게, 마음을 가볍게")
    st.divider()


# ── 세션 초기화 ───────────────────────────────────────────────────────────────
def init_session() -> None:
    defaults = {
        "messages": [],
        "survey_done": False,
        "user_gender": None,
        "user_age": None,
        "user_mood": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ── 설문 화면 ─────────────────────────────────────────────────────────────────
MOOD_EMOJIS = ["😭", "😢", "😟", "😕", "😐", "🙂", "😊", "😄", "😁", "🤩", "🥳"]

def render_survey() -> None:
    """설문이 완료되지 않았을 때 보여주는 온보딩 화면."""

    st.markdown("""
    <div class="survey-card">
        <div class="survey-title">시작하기 전에 간단히 알려주세요 👋</div>
        <div class="survey-sub">입력하신 정보는 더 잘 도와드리기 위해서만 사용돼요.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        gender = st.radio(
            "성별",
            options=["남성", "여성", "기타 / 말하고 싶지 않아요"],
            index=0,
        )

    with col2:
        age = st.selectbox(
            "나이",
            options=list(range(14, 20)),
            index=2,
            format_func=lambda x: f"{x}세",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    mood = st.slider(
        "지금 기분이 어때요?  (0 = 매우 나쁨 · 10 = 매우 좋음)",
        min_value=0,
        max_value=10,
        value=5,
        step=1,
    )

    # 슬라이더 값에 따른 이모지 표시
    emoji = MOOD_EMOJIS[mood]
    st.markdown(
        f"<div style='text-align:center; font-size:2.2rem; margin: -8px 0 16px 0;'>{emoji}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("대화 시작하기 →", type="primary", use_container_width=True):
        st.session_state.survey_done = True
        st.session_state.user_gender = gender
        st.session_state.user_age = age
        st.session_state.user_mood = mood
        st.rerun()


# ── 채팅 기록 출력 ────────────────────────────────────────────────────────────
def render_history() -> None:
    # 첫 진입 시 웰컴 메시지
    if not st.session_state.messages:
        mood = st.session_state.user_mood
        emoji = MOOD_EMOJIS[mood]
        age  = st.session_state.user_age
        st.markdown(f"""
        <div class="welcome-card">
            안녕하세요! 오늘 기분이 <b>{mood}점</b>이군요 {emoji}<br>
            {age}세 친구와 이야기 나눌 수 있어 반가워요. 🤍<br><br>
            <b>마음 다시 보기</b>는 요즘 머릿속에서 맴도는 생각이나 감정을
            함께 천천히 살펴보는 공간이에요.<br>
            편하게 이야기해 주세요. 판단 없이 들을게요.
        </div>
        """, unsafe_allow_html=True)

    for msg in st.session_state.messages:
        avatar = "🧑" if msg["role"] == "user" else "🌱"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])


# ── 채팅 입력 ─────────────────────────────────────────────────────────────────
def render_chat_input(config: SidebarConfig) -> None:
    if prompt := st.chat_input("오늘 어떤 생각이 드나요?"):
        api_key = get_api_key(config.api_key_input)

        if not api_key:
            st.error("⚠️ OpenAI API 키를 사이드바에 입력하거나 `.streamlit/secrets.toml`에 설정해주세요.")
            st.stop()

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

        # system_prompt에 사용자 정보 추가
        enriched_system = (
            config.system_prompt
            + f"\n\n[사용자 정보] 성별: {st.session_state.user_gender}, "
            f"나이: {st.session_state.user_age}세, "
            f"오늘 기분 점수: {st.session_state.user_mood}/10"
        )

        with st.chat_message("assistant", avatar="🌱"):
            placeholder = st.empty()
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


# ── 메인 진입 함수 ────────────────────────────────────────────────────────────
def render_main(config: SidebarConfig) -> None:
    """설문 완료 여부에 따라 설문 or 채팅 화면을 분기합니다."""
    render_header()
    init_session()

    if not st.session_state.survey_done:
        render_survey()
    else:
        render_history()
        render_chat_input(config)

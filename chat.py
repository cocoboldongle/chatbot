"""
chat.py — 채팅 화면 렌더링
"""
import streamlit as st
from llm import get_api_key, stream_chat
from sidebar import SidebarConfig


def apply_styles() -> None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }

    /* 전체 배경 */
    .stApp {
        background-color: #f7f9fc;
    }

    /* 사이드바 */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e8edf2;
    }

    /* 채팅 말풍선 — 사용자 */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        background-color: #e8f4fd;
        border-radius: 16px;
        padding: 12px 16px;
        margin: 6px 0;
    }

    /* 채팅 말풍선 — 어시스턴트 */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
        background-color: #ffffff;
        border-radius: 16px;
        border: 1px solid #e8edf2;
        padding: 12px 16px;
        margin: 6px 0;
    }

    /* 입력창 */
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

    /* 타이틀 */
    h1 {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: #2c3e50 !important;
    }

    /* 구분선 */
    hr {
        border-color: #e8edf2 !important;
        margin: 8px 0 16px 0 !important;
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

    .welcome-card b {
        color: #2c7be5;
    }
    </style>
    """, unsafe_allow_html=True)


def render_header() -> None:
    st.title("🌱 마음 다시 보기")
    st.caption("생각을 새롭게, 마음을 가볍게")
    st.divider()

    # 대화가 아직 없을 때만 웰컴 카드 표시
    if not st.session_state.get("messages"):
        st.markdown("""
        <div class="welcome-card">
            안녕하세요 👋<br>
            오늘 어떤 생각이나 감정이 마음에 걸리나요?<br><br>
            <b>마음 다시 보기</b>는 여러분이 힘든 생각을 새로운 시각으로
            바라볼 수 있도록 함께 이야기를 나눠드려요.<br><br>
            편하게 말씀해 주세요. 판단 없이 들을게요. 🤍
        </div>
        """, unsafe_allow_html=True)


def init_session() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []


def render_history() -> None:
    for msg in st.session_state.messages:
        avatar = "🧑" if msg["role"] == "user" else "🌱"
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

        with st.chat_message("assistant", avatar="🌱"):
            placeholder = st.empty()
            full_response = ""

            try:
                for chunk in stream_chat(
                    api_key=api_key,
                    messages=st.session_state.messages,
                    system_prompt=config.system_prompt,
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

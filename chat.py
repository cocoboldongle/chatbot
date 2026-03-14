"""
ui/chat.py
──────────────────────────────────────────────
채팅 화면 렌더링만 담당합니다.
실제 API 호출은 core/llm.py의 stream_chat()에 위임합니다.
"""
import streamlit as st
from core.llm import get_api_key, stream_chat
from ui.sidebar import SidebarConfig


def apply_styles() -> None:
    """전역 CSS를 주입합니다."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stChatMessage {
        border-radius: 12px;
        padding: 4px 0;
    }

    h1 {
        font-weight: 600;
        font-size: 1.6rem !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    </style>
    """, unsafe_allow_html=True)


def render_header() -> None:
    """페이지 상단 타이틀 영역을 렌더링합니다."""
    st.title("🤖 GPT-4o Chatbot")
    st.caption("Powered by OpenAI GPT-4o · Built with Streamlit")
    st.divider()


def init_session() -> None:
    """세션 상태를 초기화합니다."""
    if "messages" not in st.session_state:
        st.session_state.messages = []


def render_history() -> None:
    """저장된 대화 기록을 화면에 출력합니다."""
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


def render_chat_input(config: SidebarConfig) -> None:
    """
    채팅 입력창을 렌더링하고, 입력이 들어오면
    core/llm.stream_chat()을 호출해 스트리밍 응답을 보여줍니다.
    """
    if prompt := st.chat_input("메시지를 입력하세요..."):
        api_key = get_api_key(config.api_key_input)

        if not api_key:
            st.error("⚠️ OpenAI API 키를 사이드바에 입력하거나 `.streamlit/secrets.toml`에 설정해주세요.")
            st.stop()

        # 사용자 메시지 저장 & 출력
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 어시스턴트 응답 스트리밍
        with st.chat_message("assistant"):
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
                st.error(f"❌ API 오류: {e}")
                st.stop()

        st.session_state.messages.append({"role": "assistant", "content": full_response})

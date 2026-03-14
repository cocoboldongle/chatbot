"""
ui/sidebar.py
──────────────────────────────────────────────
사이드바 렌더링만 담당합니다.
설정값을 딕셔너리로 반환하므로 app.py에서 가져다 쓰기 쉽습니다.
"""
import streamlit as st
from dataclasses import dataclass


@dataclass
class SidebarConfig:
    api_key_input: str
    temperature: float
    max_tokens: int
    system_prompt: str


def render_sidebar() -> SidebarConfig:
    """
    사이드바를 렌더링하고 사용자 설정값을 SidebarConfig로 반환합니다.
    """
    with st.sidebar:
        st.title("⚙️ Settings")
        st.divider()

        api_key_input = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-...",
            help="secrets.toml에 설정하거나 여기에 직접 입력하세요.",
        )

        st.divider()
        st.subheader("Model Parameters")

        temperature = st.slider(
            "Temperature", 0.0, 2.0, 0.7, 0.1,
            help="높을수록 창의적, 낮을수록 일관된 답변",
        )
        max_tokens = st.slider(
            "Max Tokens", 256, 4096, 1024, 128,
            help="응답 최대 길이",
        )
        system_prompt = st.text_area(
            "System Prompt",
            value="You are a helpful, friendly AI assistant. Respond in the same language the user uses.",
            height=120,
        )

        st.divider()

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.caption("Model: **gpt-4o**")

    return SidebarConfig(
        api_key_input=api_key_input,
        temperature=temperature,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
    )

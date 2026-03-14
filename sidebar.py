"""
sidebar.py — 사이드바 렌더링
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
    temperature = 0.7
    max_tokens  = 800

    with st.sidebar:
        st.markdown("### 🌱 마음 다시 보기")
        st.caption("인지 재구조화 챗봇")
        st.divider()

        api_key_input = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-...",
            help="secrets.toml에 설정하거나 여기에 입력하세요.",
        )

        st.divider()

        with st.expander("⚙️ 고급 설정", expanded=False):
            temperature = st.slider("창의성 (Temperature)", 0.0, 1.5, 0.7, 0.1)
            max_tokens  = st.slider("최대 응답 길이", 256, 2048, 800, 128)

        st.divider()

        # 대화 초기화 (채팅 기록만 리셋)
        if st.button("🗑️ 대화 초기화", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        # 스타일 재선택 — 스타일이 선택된 상태일 때만 표시
        if st.session_state.get("style_chosen"):
            if st.button("🎭 스타일 바꾸기", use_container_width=True):
                st.session_state.messages     = []
                st.session_state.style_chosen = False
                st.session_state.chat_style   = None
                st.rerun()

        st.divider()
        st.markdown(
            "<div style='font-size:0.75rem; color:#888; line-height:1.6;'>"
            "💬 이 챗봇은 전문 심리 상담을 대체하지 않습니다.<br>"
            "위기 상황 시 <b>청소년 전화 1388</b>에 연락하세요."
            "</div>",
            unsafe_allow_html=True,
        )

    return SidebarConfig(
        api_key_input=api_key_input,
        temperature=temperature,
        max_tokens=max_tokens,
        system_prompt="",  # chat.py의 STYLES 프롬프트가 실제로 사용됨
    )

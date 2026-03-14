"""
sidebar.py — 사이드바 렌더링
"""
import streamlit as st
from dataclasses import dataclass

SYSTEM_PROMPT = """
너는 청소년의 마음을 따뜻하게 돌봐주는 인지 재구조화 상담 챗봇이야.
대화 원칙:
1. 판단하지 않고 먼저 공감한다.
2. 부정적인 생각 패턴을 부드럽게 탐색하도록 돕는다.
3. "정말 그럴까?", "다른 시각으로 보면 어떨까?" 같은 열린 질문을 활용한다.
4. 짧고 따뜻한 문장으로 말한다. 어렵거나 딱딱한 표현은 피한다.
5. 위기 상황(자해, 자살 언급)이 감지되면 즉시 전문 상담 기관(청소년 전화 1388)을 안내한다.
항상 한국어로 답변한다.
""".strip()


@dataclass
class SidebarConfig:
    api_key_input: str
    temperature: float
    max_tokens: int
    system_prompt: str


def render_sidebar() -> SidebarConfig:
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
            max_tokens = st.slider("최대 응답 길이", 256, 2048, 800, 128)
            system_prompt = st.text_area(
                "시스템 프롬프트",
                value=SYSTEM_PROMPT,
                height=200,
            )
        
        # 기본값 (expander 미수정 시)
        if "temperature" not in dir():
            temperature = 0.7
        if "max_tokens" not in dir():
            max_tokens = 800
        if "system_prompt" not in dir():
            system_prompt = SYSTEM_PROMPT

        st.divider()

        if st.button("🗑️ 대화 초기화", use_container_width=True):
            st.session_state.messages = []
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
        system_prompt=system_prompt,
    )

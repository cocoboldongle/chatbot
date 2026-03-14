"""
app.py
──────────────────────────────────────────────
진입점(Entry Point).
페이지 설정 후 ui/sidebar.py, ui/chat.py를 조립합니다.
비즈니스 로직은 core/, UI 렌더링은 ui/ 에 있습니다.
"""
import sys
import os

# Streamlit Cloud에서 하위 패키지(ui, core)를 찾을 수 있도록 루트 경로 추가
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from sidebar import render_sidebar
from chat import apply_styles, render_header, init_session, render_history, render_chat_input

# ── 페이지 기본 설정 (반드시 최상단) ─────────────────────────────────────────
st.set_page_config(
    page_title="GPT-4o Chatbot",
    page_icon="🤖",
    layout="centered",
)

# ── 스타일 주입 ───────────────────────────────────────────────────────────────
apply_styles()

# ── 사이드바 렌더링 & 설정값 수집 ────────────────────────────────────────────
config = render_sidebar()

# ── 메인 채팅 화면 ────────────────────────────────────────────────────────────
render_header()
init_session()
render_history()
render_chat_input(config)

"""
app.py — 진입점
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from sidebar import render_sidebar
from chat import apply_styles, init_session, render_main

st.set_page_config(
    page_title="마음 다시 보기",
    page_icon="🌱",
    layout="wide",
)

apply_styles()

# 세션을 먼저 초기화해야 sidebar에서 messages를 정확히 읽을 수 있음
init_session()

config = render_sidebar()
render_main(config)

"""
app.py — 진입점
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from sidebar import render_sidebar
from chat import apply_styles, render_header, init_session, render_history, render_chat_input

st.set_page_config(
    page_title="마음 다시 보기",
    page_icon="🌱",
    layout="centered",
)

apply_styles()
config = render_sidebar()
render_header()
init_session()
render_history()
render_chat_input(config)

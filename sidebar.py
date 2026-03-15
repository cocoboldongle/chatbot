"""
sidebar.py — 사이드바 렌더링
"""
import json
import datetime
import streamlit as st
from dataclasses import dataclass

STYLE_LABELS = {
    "detective": "🔍 분석적 탐정형",
    "friend":    "🤗 따뜻한 친구형",
    "sibling":   "😎 쿨한 형·누나형",
    "coach":     "🧘 차분한 코치형",
}

MOOD_EMOJIS = ["😭","😢","😟","😕","😐","🙂","😊","😄","😁","🤩","🥳"]

SIDEBAR_CSS = """
<style>
/* 프로필 카드 */
.profile-card {
    background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%);
    border: 1px solid #dbeafe;
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 4px;
    font-size: 0.85rem;
    color: #334155;
    line-height: 1.8;
}
.profile-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 2px 0;
}
.profile-label {
    font-size: 0.75rem;
    color: #94a3b8;
    min-width: 36px;
}
.profile-value {
    font-weight: 600;
    color: #1e293b;
    font-size: 0.85rem;
}

/* 스타일 배지 */
.style-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #ffffff;
    border: 1.5px solid #c7d2fe;
    border-radius: 20px;
    padding: 6px 12px;
    font-size: 0.82rem;
    font-weight: 600;
    color: #3730a3;
    margin-bottom: 4px;
    width: 100%;
    box-sizing: border-box;
}

/* 진행 단계 표시 */
.progress-wrap {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-bottom: 4px;
}
.progress-step {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.78rem;
    color: #94a3b8;
    padding: 5px 8px;
    border-radius: 8px;
}
.progress-step.active {
    background: #eff6ff;
    color: #1d4ed8;
    font-weight: 600;
}
.progress-step.done {
    color: #86efac;
}
.progress-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: #e2e8f0;
    flex-shrink: 0;
}
.progress-step.active .progress-dot { background: #3b82f6; }
.progress-step.done  .progress-dot { background: #4ade80; }

/* 다운로드 버튼 커스텀 */
.stDownloadButton > button {
    width: 100%;
    background-color: #f8fafc !important;
    color: #334155 !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
}
.stDownloadButton > button:hover {
    background-color: #f1f5f9 !important;
    border-color: #cbd5e1 !important;
}
</style>
"""


@dataclass
class SidebarConfig:
    temperature: float
    max_tokens: int
    system_prompt: str


def _build_txt(messages: list, profile: dict) -> str:
    """대화 내용을 텍스트로 변환."""
    now   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "═══════════════════════════════════",
        "       🌱 마음 다시 보기 — 대화 기록",
        "═══════════════════════════════════",
        f"저장 일시  : {now}",
        f"성별       : {profile.get('gender', '-')}",
        f"나이       : {profile.get('age', '-')}세",
        f"기분 점수  : {profile.get('mood', '-')}/10",
        f"대화 스타일: {profile.get('style_label', '-')}",
        "───────────────────────────────────",
        "",
    ]
    for msg in messages:
        role  = "나" if msg["role"] == "user" else "챗봇"
        lines.append(f"[{role}]")
        lines.append(msg["content"])
        lines.append("")
    lines.append("═══════════════════════════════════")
    return "\n".join(lines)


def _build_json(messages: list, profile: dict) -> str:
    """대화 내용을 JSON으로 변환."""
    data = {
        "exported_at": datetime.datetime.now().isoformat(),
        "profile": profile,
        "messages": messages,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def render_sidebar() -> SidebarConfig:
    temperature = 0.7
    max_tokens  = 800

    with st.sidebar:
        st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)
        st.markdown("### 🌱 마음 다시 보기")
        st.caption("인지 재구조화 챗봇")
        st.divider()

        # ── 사용자 프로필 (설문 완료 후 표시) ──────────────────
        if st.session_state.get("survey_done"):
            st.divider()
            gender     = st.session_state.get("user_gender", "-")
            age        = st.session_state.get("user_age", "-")
            mood       = st.session_state.get("user_mood", 5)
            mood_emoji = MOOD_EMOJIS[int(mood)] if isinstance(mood, (int, float)) else "😐"

            st.markdown(
                f"<div class='profile-card'>"
                f"<div class='profile-row'><span class='profile-label'>성별</span>"
                f"<span class='profile-value'>{gender}</span></div>"
                f"<div class='profile-row'><span class='profile-label'>나이</span>"
                f"<span class='profile-value'>{age}세</span></div>"
                f"<div class='profile-row'><span class='profile-label'>기분</span>"
                f"<span class='profile-value'>{mood_emoji} {mood}점</span></div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # ── 현재 대화 스타일 (스타일 선택 후 표시) ────────────
        if st.session_state.get("style_chosen"):
            style_key   = st.session_state.get("chat_style", "")
            style_label = STYLE_LABELS.get(style_key, "")
            st.markdown(
                f"<div class='style-badge'>{style_label}</div>",
                unsafe_allow_html=True,
            )

        # ── 진행 단계 (채팅 시작 후 표시) ──────────────────────
        phase = st.session_state.get("phase", "")
        if phase:
            st.divider()
            st.caption("진행 단계")

            STEPS = [
                ("collecting",  "💬 이야기 들어보기"),
                ("confirming",  "📋 내용 확인하기"),
                ("distortion",  "🔎 생각 패턴 찾기"),
                ("selecting",   "🧩 패턴 선택하기"),
                ("reframing",   "🌱 새로운 시각 찾기"),
            ]
            # selecting과 reframing은 같은 순위로 처리
            phase_for_order = phase if phase != "selecting" else "selecting"
            PHASE_ORDER = [s[0] for s in STEPS]
            current_idx = PHASE_ORDER.index(phase) if phase in PHASE_ORDER else 0

            rows = []
            for i, (key, label) in enumerate(STEPS):
                if i < current_idx:
                    cls = "done"
                    icon = "✓"
                elif i == current_idx:
                    cls = "active"
                    icon = "▶"
                else:
                    cls = ""
                    icon = " "
                rows.append(
                    f"<div class='progress-step {cls}'>"
                    f"<div class='progress-dot'></div>"
                    f"{icon} {label}"
                    f"</div>"
                )
            st.markdown(
                "<div class='progress-wrap'>" + "".join(rows) + "</div>",
                unsafe_allow_html=True,
            )

        st.divider()

        # ── 고급 설정 ────────────────────────────────────────────
        with st.expander("⚙️ 고급 설정", expanded=False):
            temperature = st.slider("창의성 (Temperature)", 0.0, 1.5, 0.7, 0.1)
            max_tokens  = st.slider("최대 응답 길이", 256, 2048, 800, 128)

        st.divider()

        # ── 대화 다운로드 ────────────────────────────────────────
        messages = st.session_state.get("messages", [])
        profile  = {
            "gender":      st.session_state.get("user_gender", "-"),
            "age":         st.session_state.get("user_age", "-"),
            "mood":        st.session_state.get("user_mood", "-"),
            "style_label": STYLE_LABELS.get(st.session_state.get("chat_style", ""), "-"),
        }
        fname = datetime.datetime.now().strftime("마음다시보기_%Y%m%d_%H%M")

        st.caption("💾 대화 다운로드")
        if messages:
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📄 TXT",
                    data=_build_txt(messages, profile),
                    file_name=f"{fname}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            with col2:
                st.download_button(
                    label="🗂 JSON",
                    data=_build_json(messages, profile),
                    file_name=f"{fname}.json",
                    mime="application/json",
                    use_container_width=True,
                )
        else:
            st.caption("대화를 시작하면 다운로드할 수 있어요.")
        st.divider()

        # ── 액션 버튼들 ─────────────────────────────────────────
        if st.button("🗑️ 대화 초기화", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        if st.session_state.get("style_chosen"):
            if st.button("🎭 스타일 바꾸기", use_container_width=True):
                st.session_state.messages     = []
                st.session_state.style_chosen = False
                st.session_state.chat_style   = None
                st.rerun()

        if st.session_state.get("intro_done"):
            if st.button("🏠 처음으로", use_container_width=True):
                for key in ["intro_done", "survey_done", "style_chosen",
                            "messages", "user_gender", "user_age", "user_mood", "chat_style"]:
                    st.session_state[key] = (
                        []    if key == "messages" else
                        False if key in ["intro_done", "survey_done", "style_chosen"] else
                        None
                    )
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
        temperature=temperature,
        max_tokens=max_tokens,
        system_prompt="",
    )

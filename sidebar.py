"""
sidebar.py — 사이드바 렌더링
"""
import json
import datetime
import requests
import streamlit as st
from dataclasses import dataclass
from llm import mask_personal_info

STYLE_LABELS = {
    "detective": "🔍 분석적 탐정형",
    "friend":    "🤗 따뜻한 친구형",
    "sibling":   "😎 쿨한 형·누나형",
    "coach":     "🧘 차분한 코치형",
}


REFRAMING_METHOD_LABELS = {
    "방법1":  "대안적 설명 찾기",
    "방법2":  "객관적 증거 수집",
    "방법3":  "비용/결과 재평가",
    "방법4":  "관점 바꾸기",
    "방법5":  "기적 질문 & 작은 행동",
    "방법 1": "대안적 설명 찾기",
    "방법 2": "객관적 증거 수집",
    "방법 3": "비용/결과 재평가",
    "방법 4": "관점 바꾸기",
    "방법 5": "기적 질문 & 작은 행동",
}

def _format_reframing_methods(raw: str) -> str:
    if not raw or raw == "-":
        return "-"
    parts = [p.strip() for p in raw.replace("，", ",").split(",")]
    return ", ".join(REFRAMING_METHOD_LABELS.get(p, p) for p in parts)

def _get_distortion_label(distortions: list, idx: int) -> str:
    """last_distortions 리스트에서 idx번째 왜곡 이름 반환. 없으면 '-'."""
    if not distortions or idx >= len(distortions):
        return "-"
    return distortions[idx].get("type", "-")

MOOD_EMOJIS = ["😭","😢","😟","😕","😐","🙂","😊","😄","😁","🤩","🥳"]

SIDEBAR_CSS = """
<style>
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

/* [NEW] 연구 메타 카드 */
.meta-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 4px;
    font-size: 0.78rem;
    color: #64748b;
    line-height: 1.9;
}
.meta-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.meta-label { color: #94a3b8; }
.meta-value { font-weight: 600; color: #334155; }
/* completion_type 색상 */
.meta-normal  { color: #15803d; }
.meta-soft    { color: #92400e; }
.meta-timeout { color: #b91c1c; }

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
    user_direction: str


def _build_txt(messages: list, profile: dict, mask: bool = False, api_key: str = "") -> str:
    now   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "═══════════════════════════════════",
        "       🌱 마음 다시 보기 — 대화 기록",
        "═══════════════════════════════════",
        f"저장 일시       : {now}",
        f"성별            : {profile.get('gender', '-')}",
        f"나이            : {profile.get('age', '-')}세",
        f"기분 점수       : {profile.get('mood', '-')}/10",
        f"대화 스타일     : {profile.get('style_label', '-')}",
        f"재구조화 방법   : {profile.get('reframing_methods', '-')}",
        f"완료 유형       : {profile.get('completion_type', '-')}",
        f"전체 턴 수      : {profile.get('total_turns', '-')}",
        f"재구조화 턴 수  : {profile.get('reframing_turns', '-')}",
        f"막힘 감지 횟수  : {profile.get('stuck_count', '-')}",
        f"수집된 상황     : {profile.get('situation', '-')}",
        f"수집된 생각     : {profile.get('thought', '-')}",
        f"수집된 감정     : {profile.get('emotion', '-')} ({profile.get('intensity', '-')})",
        f"발견된 왜곡 1순위: {profile.get('distortion_1', '-')}",
        f"발견된 왜곡 2순위: {profile.get('distortion_2', '-')}",
        f"발견된 왜곡 3순위: {profile.get('distortion_3', '-')}",
        f"선택한 왜곡      : {profile.get('selected_distortion_type', '-')}",
        f"개인정보 마스킹  : {'적용됨' if mask else '미적용'}",
        "───────────────────────────────────",
        "",
    ]
    for msg in messages:
        role    = "나" if msg["role"] == "user" else "챗봇"
        content = msg["content"]
        if mask and msg["role"] == "user" and api_key:
            content = mask_personal_info(api_key, content)
        lines.append(f"[{role}]")
        lines.append(content)
        lines.append("")
    lines.append("═══════════════════════════════════")
    return "\n".join(lines)


def _build_json(messages: list, profile: dict, mask: bool = False, api_key: str = "") -> str:
    masked_messages = []
    for msg in messages:
        m = dict(msg)
        if mask and m.get("role") == "user" and api_key:
            m["content"] = mask_personal_info(api_key, m["content"])
        masked_messages.append(m)
    data = {
        "exported_at":     datetime.datetime.now().isoformat(),
        "privacy_masked":  mask,
        "profile":         profile,
        "messages":        masked_messages,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def _save_to_supabase(messages: list, profile: dict, mask: bool, api_key: str) -> bool:
    try:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        if not url or not key:
            return False

        clean_messages = [m for m in messages if m.get("role") in ("user", "assistant")]
        if mask and api_key:
            from llm import mask_personal_info as _mask
            masked = []
            for m in clean_messages:
                mc = dict(m)
                if mc["role"] == "user":
                    mc["content"] = _mask(api_key, mc["content"])
                masked.append(mc)
        else:
            masked = clean_messages

        payload = {
            "gender":             profile.get("gender", "-"),
            "age":                profile.get("age"),
            "mood":               profile.get("mood"),
            "chat_style":         profile.get("style_label", "-"),
            "reframing_methods":  profile.get("reframing_methods", "-"),
            # [NEW] 연구용 메타데이터
            "completion_type":    profile.get("completion_type", "-"),
            "total_turns":        profile.get("total_turns", 0),
            "reframing_turns":    profile.get("reframing_turns", 0),
            "stuck_count":        profile.get("stuck_count", 0),
            "distortion_1":       profile.get("distortion_1", "-"),
            "distortion_2":       profile.get("distortion_2", "-"),
            "distortion_3":       profile.get("distortion_3", "-"),
            "selected_distortion":profile.get("selected_distortion_type", "-"),
            "situation":          profile.get("situation", "-"),
            "thought":            profile.get("thought", "-"),
            "emotion":            profile.get("emotion", "-"),
            "intensity":          profile.get("intensity", "-"),
            "privacy_masked":     mask,
            "messages":           masked,
        }

        resp = requests.post(
            f"{url}/rest/v1/chatbot0602",
            headers={
                "apikey":        key,
                "Authorization": f"Bearer {key}",
                "Content-Type":  "application/json",
                "Prefer":        "return=minimal",
            },
            json=payload,
            timeout=10,
        )
        return resp.status_code in (200, 201)
    except Exception:
        return False


def render_sidebar() -> SidebarConfig:
    temperature = 0.7
    max_tokens  = 800

    with st.sidebar:
        st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)
        st.markdown("### 🌱 마음 다시 보기")
        st.caption("인지 재구조화 챗봇")
        st.divider()

        # ── 사용자 프로필 ─────────────────────────────────────────
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

        # ── 대화 스타일 ────────────────────────────────────────────
        if st.session_state.get("style_chosen"):
            style_key   = st.session_state.get("chat_style", "")
            style_label = STYLE_LABELS.get(style_key, "")
            st.markdown(
                f"<div class='style-badge'>{style_label}</div>",
                unsafe_allow_html=True,
            )

        # ── 진행 단계 ──────────────────────────────────────────────
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
                ("done",        "✅ 마무리"),
            ]
            PHASE_ORDER = [s[0] for s in STEPS]
            current_idx = PHASE_ORDER.index(phase) if phase in PHASE_ORDER else 0

            rows = []
            for i, (key, label) in enumerate(STEPS):
                if i < current_idx:
                    cls = "done"; icon = "✓"
                elif i == current_idx:
                    cls = "active"; icon = "▶"
                else:
                    cls = ""; icon = " "
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

        # ── 연구용 메타데이터 패널 (비밀번호 잠금) ───────────────
        if st.session_state.get("style_chosen"):
            st.divider()
            with st.expander("📊 세션 현황", expanded=False):
                meta_pw = st.text_input(
                    "비밀번호", type="password",
                    placeholder="비밀번호를 입력하세요",
                    key="meta_pw"
                )
                if meta_pw == "1234":
                    completion_type  = st.session_state.get("completion_type") or "-"
                    total_turns      = st.session_state.get("total_turns", 0)
                    reframing_turns  = st.session_state.get("reframing_turns", 0)
                    stuck_count      = st.session_state.get("stuck_count", 0)
                    reframing_method = _format_reframing_methods(st.session_state.get("selected_reframing_methods") or "-")
                    progress_count   = st.session_state.get("progress_count", 0)
                    last_d           = st.session_state.get("last_distortions", [])
                    sel_d            = (st.session_state.get("selected_distortion") or {}).get("type", "-")
                    d_labels         = [d.get("type", "-") for d in last_d[:3]]
                    collected        = st.session_state.get("collected_info") or {}

                    type_color = {
                        "normal":  "meta-normal",
                        "soft":    "meta-soft",
                        "timeout": "meta-timeout",
                    }.get(completion_type, "")

                    # 왜곡 순위 행 생성
                    distortion_rows = ""
                    for i, label in enumerate(d_labels):
                        distortion_rows += (
                            f"<div class='meta-row'><span class='meta-label'>왜곡 {i+1}순위</span>"
                            f"<span class='meta-value'>{label}</span></div>"
                        )
                    if not d_labels:
                        distortion_rows = (
                            "<div class='meta-row'><span class='meta-label'>왜곡</span>"
                            "<span class='meta-value'>-</span></div>"
                        )

                    st.markdown(
                        f"<div class='meta-card'>"
                        f"<div class='meta-row'><span class='meta-label'>완료 유형</span>"
                        f"<span class='meta-value {type_color}'>{completion_type}</span></div>"
                        f"<div class='meta-row'><span class='meta-label'>전체 턴</span>"
                        f"<span class='meta-value'>{total_turns}</span></div>"
                        f"<div class='meta-row'><span class='meta-label'>재구조화 턴</span>"
                        f"<span class='meta-value'>{reframing_turns}</span></div>"
                        f"<div class='meta-row'><span class='meta-label'>변화 감지</span>"
                        f"<span class='meta-value'>{progress_count}회</span></div>"
                        f"<div class='meta-row'><span class='meta-label'>막힘 감지</span>"
                        f"<span class='meta-value'>{stuck_count}회</span></div>"
                        f"<div class='meta-row'><span class='meta-label'>재구조화 방법</span>"
                        f"<span class='meta-value'>{reframing_method}</span></div>"
                        + distortion_rows +
                        f"<div class='meta-row'><span class='meta-label'>선택 왜곡</span>"
                        f"<span class='meta-value'>{sel_d}</span></div>"
                        f"<div class='meta-row'><span class='meta-label'>상황</span>"
                        f"<span class='meta-value'>{collected.get('situation', '-')}</span></div>"
                        f"<div class='meta-row'><span class='meta-label'>생각</span>"
                        f"<span class='meta-value'>{collected.get('thought', '-')}</span></div>"
                        f"<div class='meta-row'><span class='meta-label'>감정</span>"
                        f"<span class='meta-value'>{collected.get('emotion', '-')} ({collected.get('intensity', '-')})</span></div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                elif meta_pw:
                    st.caption("❌ 비밀번호가 틀렸어요.")

        st.divider()

        # ── 원하는 대화 방향 ────────────────────────────────────────
        st.caption("🧭 원하는 대화 방향이 있나요?")
        ph = "예) 위로보다는 해결책을 찾고 싶어요\n예) 엄마 입장도 이해해보고 싶어요"
        user_direction = st.text_area(
            label="direction",
            label_visibility="collapsed",
            placeholder=ph,
            height=100,
            key="user_direction_input",
        )
        if user_direction:
            st.caption("✅ 입력한 방향이 대화에 반영돼요")

        st.divider()

        # ── 고급 설정 ──────────────────────────────────────────────
        with st.expander("⚙️ 고급 설정", expanded=False):
            pw = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요", key="admin_pw")
            if pw == "1234":
                temperature = st.slider("창의성 (Temperature)", 0.0, 1.5, 0.7, 0.1)
                max_tokens  = st.slider("최대 응답 길이", 256, 2048, 800, 128)
            elif pw:
                st.caption("❌ 비밀번호가 틀렸어요.")

        st.divider()

        # ── 대화 다운로드 ──────────────────────────────────────────
        messages = st.session_state.get("messages", [])
        profile  = {
            "gender":            st.session_state.get("user_gender", "-"),
            "age":               st.session_state.get("user_age", "-"),
            "mood":              st.session_state.get("user_mood", "-"),
            "style_label":       STYLE_LABELS.get(st.session_state.get("chat_style", ""), "-"),
            "reframing_methods": _format_reframing_methods(st.session_state.get("selected_reframing_methods", "-")),
            # [NEW]
            "completion_type":   st.session_state.get("completion_type", "-"),
            "total_turns":       st.session_state.get("total_turns", 0),
            "reframing_turns":   st.session_state.get("reframing_turns", 0),
            "stuck_count":       st.session_state.get("stuck_count", 0),
            # 발견된 왜곡 1~3순위 및 선택한 왜곡
            "distortion_1":      _get_distortion_label(st.session_state.get("last_distortions", []), 0),
            "distortion_2":      _get_distortion_label(st.session_state.get("last_distortions", []), 1),
            "distortion_3":      _get_distortion_label(st.session_state.get("last_distortions", []), 2),
            "selected_distortion_type": (st.session_state.get("selected_distortion") or {}).get("type", "-"),
            # 정보 수집 결과
            "situation":   (st.session_state.get("collected_info") or {}).get("situation", "-"),
            "thought":     (st.session_state.get("collected_info") or {}).get("thought", "-"),
            "emotion":     (st.session_state.get("collected_info") or {}).get("emotion", "-"),
            "intensity":   (st.session_state.get("collected_info") or {}).get("intensity", "-"),
        }
        fname = datetime.datetime.now().strftime("마음다시보기_%Y%m%d_%H%M")

        st.caption("💾 대화 다운로드")
        if messages:
            do_mask = st.toggle(
                "🔒 개인정보 마스킹",
                value=True,
                help="이름·학교·지역 등 신상 정보를 *로 가려서 저장해요.",
            )
            try:
                _api_key = st.secrets["OPENAI_API_KEY"]
            except Exception:
                _api_key = ""

            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📄 TXT",
                    data=_build_txt(messages, profile, mask=do_mask, api_key=_api_key),
                    file_name=f"{fname}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="dl_txt",
                )
            with col2:
                st.download_button(
                    label="🗂 JSON",
                    data=_build_json(messages, profile, mask=do_mask, api_key=_api_key),
                    file_name=f"{fname}.json",
                    mime="application/json",
                    use_container_width=True,
                    key="dl_json",
                )

            if st.button("☁️ DB에 저장", use_container_width=True, key="save_db"):
                with st.spinner("저장 중..."):
                    ok = _save_to_supabase(messages, profile, mask=do_mask, api_key=_api_key)
                if ok:
                    st.success("✅ DB에 저장됐어요!")
                else:
                    st.error("❌ 저장 실패. Supabase 설정을 확인해주세요.")
        else:
            st.caption("대화를 시작하면 다운로드할 수 있어요.")
        st.divider()

        # ── 액션 버튼 ──────────────────────────────────────────────
        if st.button("🗑️ 대화 초기화", use_container_width=True):
            # 메시지 + 연구용 메타데이터 전체 리셋
            reset_keys = {
                "messages":                  [],
                "phase":                     "collecting",
                "collected_info":            None,
                "distortion_start_messages": 0,
                "reframing_start_messages":  0,
                "crisis_count":              0,
                "progress_count":            0,
                "crisis_modal_shown":        False,
                "suggestions":               [],
                "stuck_count":               0,
                "completion_type":           None,
                "total_turns":               0,
                "reframing_turns":           0,
                "selected_reframing_methods": "",
                "selected_distortion":       None,
                "last_distortions":          [],
                "reframing_summary":         "",
            }
            for k, v in reset_keys.items():
                st.session_state[k] = v
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
        user_direction=user_direction,
    )

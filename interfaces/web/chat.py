from __future__ import annotations

import html
import time

import streamlit as st

from homeagent.app.agent import HouseRentingAgentV2
from homeagent.config import PROJECT_NAME
from homeagent.domain.models import RecommendationResult
from homeagent.interfaces.web.results import render_results
from homeagent.interfaces.web.state import reset_voice_widget
from homeagent.interfaces.web.voice import detect_voice_backend, maybe_process_audio_input


def build_assistant_message(result: RecommendationResult) -> str:
    lines = [result.analysis_summary]
    if result.relaxation_notes:
        lines.append(f"已自动放宽：{'；'.join(result.relaxation_notes)}")
    if result.recommendations:
        preview = "；".join(
            f"{item.title}（{item.monthly_rent} 元/月）" for item in result.recommendations[:3]
        )
        lines.append(f"优先推荐：{preview}")
    return "\n\n".join(lines)


def persist_conversation(agent: HouseRentingAgentV2, query: str, assistant_message: str) -> None:
    st.session_state.chat_history.append({"role": "user", "content": query})
    st.session_state.chat_history.append({"role": "assistant", "content": assistant_message})
    agent.record_conversation(query, assistant_message)


def run_query(agent: HouseRentingAgentV2, query: str, source: str) -> tuple[RecommendationResult, str]:
    result = agent.search(query, verbose=True)
    st.session_state.result = result
    st.session_state.last_query = query
    st.session_state.last_search_source = source
    st.session_state.selected_listing_id = result.recommendations[0].listing_id if result.recommendations else ""
    st.session_state.gallery_index = 0
    return result, build_assistant_message(result)


def stream_text(text: str, chunk_size: int = 10):
    for index in range(0, len(text), chunk_size):
        yield text[index : index + chunk_size]
        time.sleep(0.018)


def render_chat_bubble(role: str, content: str, placeholder=None) -> None:
    safe_content = html.escape(content).replace("\n", "<br/>")
    target = placeholder if placeholder is not None else st

    if role == "user":
        target.markdown(
            f"""
            <div class="chat-row user">
                <div class="chat-bubble user">{safe_content}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    target.markdown(
        f"""
        <div class="chat-row assistant">
            <div class="assistant-avatar">巢</div>
            <div class="assistant-block">
                <div class="assistant-card">
                    <div class="assistant-card-icon">✦</div>
                    <div class="assistant-card-text">{PROJECT_NAME} 正在结合房源、知识库和筛选偏好给你结果</div>
                </div>
                <div class="assistant-message">{safe_content}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def submit_query(agent: HouseRentingAgentV2, query: str, source: str) -> None:
    with st.spinner(f"{PROJECT_NAME} 正在分析需求并搜索房源..."):
        _, assistant_message = run_query(agent, query, source=source)
    persist_conversation(agent, query, assistant_message)


def render_header() -> None:
    has_history = bool(st.session_state.get("chat_history"))
    has_result = st.session_state.get("result") is not None
    if has_history or has_result:
        st.markdown(
            f"""
            <div class="mini-topbar">
                <div class="mini-brand">{PROJECT_NAME}</div>
                <div class="mini-subtitle">北京租房智能助手</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""
        <div class="hero-shell">
            <div class="hero-kicker">{PROJECT_NAME} · Beijing Renting Agent</div>
            <h1>像和 Kimi 聊天一样找房。</h1>
            <p>直接说预算、区域、户型和通勤偏好。系统会把结构化筛选、知识检索和房源推荐收敛成一条清晰的对话流。</p>
            <div class="hero-suggestions">
                <span>朝阳区 两室一厅 预算7000 近地铁</span>
                <span>海淀区 一居室 预算5000 精装</span>
                <span>丰台区 可月付 通勤国贸</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_voice_input(agent: HouseRentingAgentV2) -> None:
    _, backend_label = detect_voice_backend()
    with st.expander("语音输入", expanded=False):
        st.caption(f"当前转写引擎：{backend_label}")
        helper_col, action_col = st.columns([4, 1])
        with helper_col:
            st.caption("如果浏览器没有重新弹出麦克风授权，可以点右侧按钮重新挂载录音组件。")
        with action_col:
            if st.button("重载麦克风", use_container_width=True, key="reset_voice_widget"):
                reset_voice_widget()
                st.rerun()

        audio_file = st.audio_input(
            "录音",
            key=f"voice_audio_input_{st.session_state.voice_widget_version}",
            label_visibility="collapsed",
        )
        maybe_process_audio_input(audio_file)

        if st.session_state.voice_error:
            st.warning(st.session_state.voice_error)

        if st.session_state.voice_draft:
            draft_col, send_col = st.columns([5, 1])
            with draft_col:
                st.text_area(
                    "语音识别结果",
                    value=st.session_state.voice_draft,
                    key="voice_draft",
                    height=88,
                )
            with send_col:
                st.write("")
                if st.button("发送", use_container_width=True, key="send_voice_query"):
                    submit_query(agent, st.session_state.voice_draft.strip(), source="voice")
                    st.session_state.voice_draft = ""
                    st.session_state.voice_error = ""
                    st.rerun()


def render_empty_prompts(agent: HouseRentingAgentV2) -> None:
    st.markdown('<div class="suggestion-title">试试这样问</div>', unsafe_allow_html=True)
    prompt_cols = st.columns(3, gap="small")
    prompts = [
        "朝阳区 两室一厅 预算7000 近地铁",
        "海淀区 一居室 预算5000 精装",
        "通州区 两居室 预算6000 可月付",
    ]
    for col, prompt in zip(prompt_cols, prompts):
        with col:
            if st.button(prompt, key=f"quick_prompt_{prompt}", use_container_width=True):
                submit_query(agent, prompt, source="preset")
                st.rerun()


def render_chat_panel(agent: HouseRentingAgentV2, result: RecommendationResult | None) -> None:
    st.markdown('<div class="chat-stream-shell">', unsafe_allow_html=True)

    with st.container(height=680, border=False):
        if not st.session_state.chat_history:
            render_empty_prompts(agent)
            st.markdown('<div class="chat-spacer"></div>', unsafe_allow_html=True)
        else:
            for item in st.session_state.chat_history[-12:]:
                render_chat_bubble(item["role"], item["content"])

        if result is not None:
            render_results(agent, result)

    render_voice_input(agent)
    prompt = st.chat_input(f"问问 {PROJECT_NAME}，比如：朝阳区 两室一厅 预算7000 近地铁")
    if prompt:
        submit_query(agent, prompt.strip(), source="chat")
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

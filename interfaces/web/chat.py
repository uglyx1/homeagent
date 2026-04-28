from __future__ import annotations

import html
import time

import streamlit as st

from homeagent.app.agent import HouseRentingAgentV2
from homeagent.config import PROJECT_NAME, PROJECT_SUBTITLE
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
        result = st.session_state.get("result")
        total = result.total_found if result else 0
        compared = len(st.session_state.get("compare_ids", []))
        st.markdown(
            f"""
            <div class="mini-topbar">
                <div>
                    <div class="mini-brand">{PROJECT_NAME}</div>
                    <div class="mini-subtitle">{PROJECT_SUBTITLE}</div>
                </div>
                <div class="mini-status">
                    <span>{total} 套候选</span>
                    <span>{compared} 套对比</span>
                    <span>北京</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""
        <div class="hero-shell">
            <div class="hero-main">
                <div>
                    <div class="hero-kicker">{PROJECT_NAME} · Beijing Renting Agent</div>
                    <h1>把租房筛选变成一张清楚的决策桌。</h1>
                    <p>说出预算、区域、户型和通勤偏好，巢选会把候选房源、匹配理由、区域分布和下一步建议整理成连续的对话结果。</p>
                    <div class="hero-chips">
                        <span class="hero-chip">自然语言找房</span>
                        <span class="hero-chip">结构化筛选</span>
                        <span class="hero-chip">地图对比</span>
                    </div>
                </div>
                <div class="hero-suggestions">
                    <span>朝阳区 两室一厅 预算7000 近地铁</span>
                    <span>海淀区 一居室 预算5000 精装</span>
                    <span>丰台区 可月付 通勤国贸</span>
                </div>
            </div>
            <div class="hero-rail">
                <div class="hero-rail-title">今日工作台</div>
                <div class="hero-rail-item">
                    <div class="hero-rail-value">5</div>
                    <div class="hero-rail-label">优先推荐位</div>
                </div>
                <div class="hero-rail-item">
                    <div class="hero-rail-value">3</div>
                    <div class="hero-rail-label">知识检索参考</div>
                </div>
                <div class="hero-rail-item">
                    <div class="hero-rail-value">4</div>
                    <div class="hero-rail-label">决策视图：推荐、地图、详情、对比</div>
                </div>
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
    st.markdown('<div class="suggestion-title">快捷需求</div>', unsafe_allow_html=True)
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

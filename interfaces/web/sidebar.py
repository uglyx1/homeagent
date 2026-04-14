from __future__ import annotations

import streamlit as st

from homeagent.app.agent import HouseRentingAgentV2
from homeagent.config import PROJECT_NAME
from homeagent.domain.models import RecommendationResult
from homeagent.interfaces.web.chat import persist_conversation, run_query
from homeagent.interfaces.web.data import get_agent, get_filter_options, hydrate_chat_history
from homeagent.interfaces.web.state import clear_filters, compose_filter_query, read_filters


def render_sidebar(agent: HouseRentingAgentV2, result: RecommendationResult | None) -> None:
    options = get_filter_options()
    with st.sidebar:
        st.markdown(f"### {PROJECT_NAME}")
        st.caption("筛选器和辅助面板都收在这里，主页面只保留对话。")

        user_id = st.text_input("用户 ID", value=st.session_state.user_id)
        if user_id != st.session_state.user_id:
            st.session_state.user_id = user_id
            st.session_state.result = None
            st.session_state.selected_listing_id = ""
            st.session_state.compare_ids = []
            st.session_state.gallery_index = 0
            st.session_state.chat_history = hydrate_chat_history(get_agent(user_id))
            st.rerun()

        with st.expander("筛选搜索", expanded=True):
            st.multiselect("区域", options["districts"], key="filter_districts", placeholder="可多选")
            st.selectbox("户型", options["room_labels"], key="filter_room_label")
            st.slider(
                "预算",
                min_value=options["budget_min"],
                max_value=options["budget_max"],
                value=st.session_state.filter_budget,
                step=100,
                key="filter_budget",
            )
            st.checkbox("优先近地铁", key="filter_near_subway")
            if st.session_state.filter_near_subway:
                st.slider("地铁距离", min_value=200, max_value=options["metro_max"], step=100, key="filter_metro_limit")
            st.multiselect("标签", options["tag_options"], key="filter_tags", placeholder="例如 精装 / 近地铁")
            st.text_input("补充关键词", key="filter_keyword")

            filters = read_filters()
            filter_query = compose_filter_query(filters, options)

            if st.button("按筛选条件搜索", use_container_width=True):
                if filter_query:
                    result, assistant_message = run_query(agent, filter_query, source="filters")
                    persist_conversation(agent, filter_query, assistant_message)
                    st.session_state.result = result
                    st.rerun()
                st.warning("先选择一些筛选条件。")

            if st.button("清空全部筛选", use_container_width=True):
                clear_filters(options)
                st.rerun()

            st.caption("左侧筛选器是独立搜索入口，不会自动拼进聊天输入框。")

        with st.expander("本轮状态", expanded=False):
            total = result.total_found if result else 0
            hit_count = len(result.knowledge_hits) if result else 0
            st.metric("候选房源", total)
            st.metric("知识命中", hit_count)
            st.metric("收藏房源", len(agent.get_favorite_listing_ids()))
            st.metric("对比列表", len(st.session_state.compare_ids))

        with st.expander("系统状态", expanded=False):
            st.code(agent.get_status_summary(), language=None)

        with st.expander("用户画像", expanded=False):
            st.code(agent.get_memory_summary(), language=None)

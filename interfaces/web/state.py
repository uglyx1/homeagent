from __future__ import annotations

import streamlit as st

from homeagent.app.agent import HouseRentingAgentV2
from homeagent.interfaces.web.data import get_filter_options, hydrate_chat_history


def ensure_state(agent: HouseRentingAgentV2) -> None:
    options = get_filter_options()
    st.session_state.setdefault("user_id", "demo_user")
    st.session_state.setdefault("result", None)
    st.session_state.setdefault("selected_listing_id", "")
    st.session_state.setdefault("compare_ids", [])
    st.session_state.setdefault("gallery_index", 0)
    st.session_state.setdefault("last_query", "")
    st.session_state.setdefault("last_search_source", "")
    st.session_state.setdefault("voice_draft", "")
    st.session_state.setdefault("voice_last_digest", "")
    st.session_state.setdefault("voice_backend", "")
    st.session_state.setdefault("voice_error", "")
    st.session_state.setdefault("voice_widget_version", 0)
    st.session_state.setdefault("filter_budget", (options["budget_min"], options["budget_max"]))
    st.session_state.setdefault("filter_districts", [])
    st.session_state.setdefault("filter_room_label", "不限")
    st.session_state.setdefault("filter_near_subway", False)
    st.session_state.setdefault("filter_metro_limit", min(800, options["metro_max"]))
    st.session_state.setdefault("filter_tags", [])
    st.session_state.setdefault("filter_keyword", "")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = hydrate_chat_history(agent)


def read_filters() -> dict:
    return {
        "districts": st.session_state.filter_districts,
        "room_label": st.session_state.filter_room_label,
        "budget_range": st.session_state.filter_budget,
        "near_subway": st.session_state.filter_near_subway,
        "metro_limit": st.session_state.filter_metro_limit,
        "tags": st.session_state.filter_tags,
        "keyword": st.session_state.filter_keyword.strip(),
    }


def compose_filter_query(filters: dict, options: dict) -> str:
    parts: list[str] = []
    if filters["districts"]:
        parts.append("、".join(filters["districts"]))
    if filters["room_label"] != "不限":
        parts.append(filters["room_label"])

    budget_min, budget_max = filters["budget_range"]
    if budget_max < options["budget_max"] or budget_min > options["budget_min"]:
        if budget_min > options["budget_min"]:
            parts.append(f"预算{budget_min}到{budget_max}")
        else:
            parts.append(f"预算{budget_max}以内")

    if filters["near_subway"]:
        parts.append(f"近地铁 {filters['metro_limit']} 米内")
    if filters["tags"]:
        parts.extend(filters["tags"])
    if filters["keyword"]:
        parts.append(filters["keyword"])
    return " ".join(part for part in parts if part).strip()


def clear_filters(options: dict) -> None:
    st.session_state.filter_districts = []
    st.session_state.filter_room_label = "不限"
    st.session_state.filter_budget = (options["budget_min"], options["budget_max"])
    st.session_state.filter_near_subway = False
    st.session_state.filter_metro_limit = min(800, options["metro_max"])
    st.session_state.filter_tags = []
    st.session_state.filter_keyword = ""


def reset_voice_widget() -> None:
    st.session_state.voice_widget_version += 1
    st.session_state.voice_last_digest = ""
    st.session_state.voice_draft = ""
    st.session_state.voice_error = ""

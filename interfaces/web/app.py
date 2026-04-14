from __future__ import annotations

import streamlit as st

from homeagent.interfaces.web.chat import render_chat_panel, render_header
from homeagent.interfaces.web.constants import PAGE_TITLE
from homeagent.interfaces.web.data import get_agent
from homeagent.interfaces.web.sidebar import render_sidebar
from homeagent.interfaces.web.state import ensure_state
from homeagent.interfaces.web.styles import inject_styles


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, layout="wide", initial_sidebar_state="collapsed")

    bootstrap_agent = get_agent(st.session_state.get("user_id", "demo_user"))
    ensure_state(bootstrap_agent)
    inject_styles()

    agent = get_agent(st.session_state.user_id)
    result = st.session_state.result

    render_sidebar(agent, result)

    with st.container():
        render_header()
        render_chat_panel(agent, result)

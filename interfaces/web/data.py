from __future__ import annotations

import urllib.request
from collections import Counter

import streamlit as st

from homeagent.app.agent import HouseRentingAgentV2
from homeagent.infrastructure.datasources.listing_data_source import get_data_source
from homeagent.interfaces.web.constants import IMAGE_HEADERS, ROOM_LABEL_TO_TYPE


def get_agent(user_id: str) -> HouseRentingAgentV2:
    return HouseRentingAgentV2(user_id=user_id)


@st.cache_data(show_spinner=False, ttl=3600)
def get_filter_options() -> dict:
    listings = get_data_source().all_listings()
    districts = sorted({item.district for item in listings if item.district})
    tags = Counter(tag for item in listings for tag in item.tags)
    max_budget = max((item.monthly_rent for item in listings), default=10000)
    min_budget = min((item.monthly_rent for item in listings), default=1000)
    max_metro = max((item.transport.metro_distance or 0 for item in listings), default=1500)
    return {
        "districts": districts,
        "room_labels": list(ROOM_LABEL_TO_TYPE.keys()),
        "tag_options": [tag for tag, _ in tags.most_common(16)],
        "budget_min": int(min_budget // 100 * 100),
        "budget_max": int((max_budget + 99) // 100 * 100),
        "metro_max": max(500, int((max_metro + 99) // 100 * 100)),
    }


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_image_bytes(url: str) -> bytes | None:
    if not url:
        return None
    try:
        request = urllib.request.Request(url, headers=IMAGE_HEADERS)
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read()
    except Exception:
        return None


def hydrate_chat_history(agent: HouseRentingAgentV2) -> list[dict[str, str]]:
    history: list[dict[str, str]] = []
    for item in agent.get_recent_conversations(limit=8):
        history.append({"role": "user", "content": item["query"]})
        history.append({"role": "assistant", "content": item["response"]})
    return history


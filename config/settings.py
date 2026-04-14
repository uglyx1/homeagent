from __future__ import annotations

from typing import Any

import yaml

from homeagent.utils.config_handler import get_env, get_env_bool, get_env_int
from homeagent.utils.path_tool import (
    AGENT_COMPAT_CONFIG_PATH,
    CHROMA_PERSIST_DIR_DEFAULT,
    DATA_DIR,
    KNOWLEDGE_DIR,
    MEMORY_DIR,
    PACKAGE_ROOT,
    RAW_DATA_DIR,
    VECTOR_STORE_DIR_DEFAULT,
    WORKSPACE_ROOT,
    ensure_directories,
)


PROJECT_ROOT = PACKAGE_ROOT
WORKSPACE_DIR = WORKSPACE_ROOT

PROJECT_NAME = "巢选"
PROJECT_SUBTITLE = "租房 Agent 工作台"
DEFAULT_CITY = "北京"
DEFAULT_USER_ID = "demo_user"
TOP_N_RECOMMENDATIONS = 5
MAX_REACT_STEPS = 4
MAX_GRAPH_STEPS = 5

DEMO_LISTINGS_PATH = DATA_DIR / "demo_listings.json"
PROCESSED_LISTINGS_PATH = DATA_DIR / "processed_listings.json"
VECTOR_DOCS_PATH = KNOWLEDGE_DIR / "listing_vector_docs.json"

LLM_MODEL = get_env(["HOMEAGENT_LLM_MODEL"], "qwen-flash")
LLM_BASE_URL = get_env(
    ["HOMEAGENT_LLM_BASE_URL", "DASHSCOPE_BASE_URL"],
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
)
LLM_API_KEY = get_env(["DASHSCOPE_API_KEY", "OPENAI_API_KEY"], "")
LANGGRAPH_ENABLED = get_env_bool("HOMEAGENT_LANGGRAPH_ENABLED", True)
LANGCHAIN_WORKFLOW_ENABLED = get_env_bool("HOMEAGENT_LANGCHAIN_ENABLED", LANGGRAPH_ENABLED)
LLM_TEMPERATURE = 0.1
SEARCH_LIMIT = get_env_int("HOMEAGENT_SEARCH_LIMIT", 20)

_DEFAULT_CHROMA_SETTINGS: dict[str, Any] = {
    "client": {"persist_directory": "chroma_db"},
    "collection": {"name": "agent"},
    "retrieval": {"k": 3},
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_chroma_settings() -> dict[str, Any]:
    if not AGENT_COMPAT_CONFIG_PATH.exists():
        return _DEFAULT_CHROMA_SETTINGS
    try:
        payload = yaml.safe_load(AGENT_COMPAT_CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return _DEFAULT_CHROMA_SETTINGS

    envs = payload.get("envs", {})
    selected_env = get_env(["HOMEAGENT_CHROMA_ENV"], "default")
    base_settings = envs.get("default", {})
    env_override = envs.get(selected_env, {}) if selected_env != "default" else {}
    merged = _deep_merge(_DEFAULT_CHROMA_SETTINGS, base_settings)
    if env_override:
        merged = _deep_merge(merged, env_override)
    return merged


CHROMA_SETTINGS = _load_chroma_settings()
CHROMA_COLLECTION_NAME = get_env(
    ["HOMEAGENT_CHROMA_COLLECTION"],
    f"{CHROMA_SETTINGS.get('collection', {}).get('name', 'agent')}_chaoxuan_listings",
)
CHROMA_TOP_K = int(CHROMA_SETTINGS.get("retrieval", {}).get("k") or 3)
CHROMA_PERSIST_DIR = WORKSPACE_ROOT / str(
    CHROMA_SETTINGS.get("client", {}).get("persist_directory") or CHROMA_PERSIST_DIR_DEFAULT.name
)
VECTOR_STORE_DIR = CHROMA_PERSIST_DIR or VECTOR_STORE_DIR_DEFAULT

ensure_directories(
    [
        DATA_DIR,
        KNOWLEDGE_DIR,
        MEMORY_DIR,
        RAW_DATA_DIR,
        CHROMA_PERSIST_DIR,
    ]
)


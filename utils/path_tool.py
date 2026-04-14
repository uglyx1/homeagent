from __future__ import annotations

from pathlib import Path
from typing import Iterable


PACKAGE_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = PACKAGE_ROOT.parent

CONFIG_DIR = PACKAGE_ROOT / "config"
DATA_DIR = PACKAGE_ROOT / "data"
PROMPTS_DIR = PACKAGE_ROOT / "prompts"
UTILS_DIR = PACKAGE_ROOT / "utils"
WORKFLOWS_DIR = PACKAGE_ROOT / "workflows"
KNOWLEDGE_DIR = PACKAGE_ROOT / "knowledge"
MEMORY_DIR = DATA_DIR / "memory"
RAW_DATA_DIR = DATA_DIR / "raw_data"

CHROMA_PERSIST_DIR_DEFAULT = WORKSPACE_ROOT / "chroma_db"
VECTOR_STORE_DIR_DEFAULT = CHROMA_PERSIST_DIR_DEFAULT
AGENT_COMPAT_CONFIG_PATH = WORKSPACE_ROOT / "Agent" / "config" / "chroma.yml"


def ensure_directories(paths: Iterable[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


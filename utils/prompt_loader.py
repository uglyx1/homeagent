from __future__ import annotations

from pathlib import Path

from homeagent.utils.file_handler import read_text
from homeagent.utils.path_tool import PROMPTS_DIR


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return read_text(path)


def prompt_path(name: str) -> Path:
    return PROMPTS_DIR / name


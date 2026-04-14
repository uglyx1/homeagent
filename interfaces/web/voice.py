from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path

import streamlit as st
from openai import OpenAI

try:
    import speech_recognition as sr
except Exception:  # pragma: no cover
    sr = None


@st.cache_resource(show_spinner=False)
def get_openai_client() -> OpenAI | None:
    if not os.environ.get("OPENAI_API_KEY"):
        return None
    return OpenAI()


def detect_voice_backend() -> tuple[str | None, str]:
    if get_openai_client() is not None:
        return "openai", "OpenAI 语音转写"
    if sr is not None:
        return "sphinx", "PocketSphinx 离线转写"
    return None, "当前环境没有可用语音转写引擎"


def transcribe_audio_bytes(audio_bytes: bytes, mime_type: str = "audio/wav") -> tuple[str | None, str, str | None]:
    backend, backend_label = detect_voice_backend()
    if backend is None:
        return None, "", "当前环境没有可用的语音转写引擎。"

    suffix = ".wav" if "wav" in mime_type else ".mp3"
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = Path(temp_file.name)

        if backend == "openai":
            client = get_openai_client()
            if client is None:
                return None, backend_label, "没有检测到 OpenAI API Key。"
            with open(temp_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="gpt-4o-mini-transcribe",
                    file=audio_file,
                    prompt=(
                        "This is a Chinese rental search query. Common words include 北京、朝阳区、海淀区、"
                        "丰台区、一室一厅、两室一厅、三室一厅、近地铁、整租、合租。"
                    ),
                )
            text = getattr(transcription, "text", "") if transcription is not None else ""
            text = text.strip()
            if not text:
                return None, backend_label, "没有识别到清晰的语音内容。"
            return text, backend_label, None

        if sr is None:
            return None, backend_label, "PocketSphinx 未安装。"
        recognizer = sr.Recognizer()
        with sr.AudioFile(str(temp_path)) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_sphinx(audio_data).strip()
        if not text:
            return None, backend_label, "离线转写没有识别到有效内容。"
        return text, backend_label, None
    except Exception as exc:
        return None, backend_label, f"语音转写失败：{exc}"
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def maybe_process_audio_input(audio_file) -> None:
    if audio_file is None:
        return
    audio_bytes = audio_file.getvalue()
    digest = hashlib.md5(audio_bytes).hexdigest()
    if digest == st.session_state.voice_last_digest:
        return
    transcript, backend_label, error = transcribe_audio_bytes(audio_bytes, getattr(audio_file, "type", "audio/wav"))
    st.session_state.voice_last_digest = digest
    st.session_state.voice_backend = backend_label
    st.session_state.voice_error = error or ""
    if transcript:
        st.session_state.voice_draft = transcript

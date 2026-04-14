from __future__ import annotations

import streamlit as st


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #ffffff;
            --panel: #ffffff;
            --panel-soft: #f7f7f8;
            --panel-muted: #fafafa;
            --line: #e8e8eb;
            --line-strong: #d9d9df;
            --ink: #171717;
            --muted: #6b7280;
            --brand: #4f8cff;
            --brand-soft: #eff5ff;
            --shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
        }

        .stApp {
            background: var(--bg);
            color: var(--ink);
        }

        .block-container {
            max-width: 960px;
            padding-top: 1rem;
            padding-bottom: 6rem;
        }

        header[data-testid="stHeader"] {
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(12px);
        }

        section[data-testid="stSidebar"] {
            background: #fcfcfd;
            border-right: 1px solid var(--line);
        }

        .mini-topbar {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            padding: 0.35rem 0 1rem;
        }

        .mini-brand {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--ink);
        }

        .mini-subtitle {
            color: var(--muted);
            font-size: 0.9rem;
        }

        .hero-shell {
            padding: 1.2rem 0 1rem;
        }

        .hero-kicker {
            display: inline-flex;
            align-items: center;
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            background: var(--panel-soft);
            color: var(--brand);
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.03em;
        }

        .hero-shell h1 {
            margin: 1rem 0 0;
            font-size: 3rem;
            line-height: 1.1;
            letter-spacing: -0.04em;
            color: var(--ink);
        }

        .hero-shell p {
            margin: 0.85rem 0 0;
            color: var(--muted);
            font-size: 1.05rem;
            line-height: 1.85;
            max-width: 720px;
        }

        .hero-suggestions {
            display: flex;
            flex-wrap: wrap;
            gap: 0.65rem;
            margin-top: 1rem;
        }

        .hero-suggestions span {
            display: inline-flex;
            align-items: center;
            padding: 0.58rem 0.85rem;
            border-radius: 999px;
            background: var(--panel-soft);
            color: #374151;
            font-size: 0.92rem;
        }

        .chat-stream-shell {
            margin-top: 0.4rem;
        }

        .suggestion-title {
            margin: 0.2rem 0 0.7rem;
            color: var(--muted);
            font-size: 0.88rem;
        }

        .chat-spacer {
            height: 0.35rem;
        }

        .chat-row {
            display: flex;
            width: 100%;
            margin: 1rem 0;
        }

        .chat-row.user {
            justify-content: flex-end;
        }

        .chat-row.assistant {
            justify-content: flex-start;
            gap: 0.9rem;
        }

        .chat-bubble.user {
            max-width: min(72%, 560px);
            border-radius: 20px;
            background: var(--panel-soft);
            border: 1px solid var(--line);
            padding: 0.85rem 1rem;
            color: var(--ink);
            font-size: 1rem;
            line-height: 1.75;
            word-break: break-word;
        }

        .assistant-avatar {
            width: 36px;
            height: 36px;
            border-radius: 999px;
            background: linear-gradient(135deg, #4f8cff, #7ab2ff);
            color: white;
            font-size: 0.95rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            margin-top: 0.1rem;
        }

        .assistant-block {
            width: min(100%, 760px);
        }

        .assistant-card {
            display: flex;
            align-items: center;
            gap: 0.7rem;
            padding: 0.75rem 0.95rem;
            border: 1px solid var(--line);
            border-radius: 16px;
            background: var(--panel);
            margin-bottom: 0.9rem;
        }

        .assistant-card-icon {
            color: var(--brand);
            font-weight: 700;
        }

        .assistant-card-text {
            color: #4b5563;
            font-size: 0.95rem;
        }

        .assistant-message {
            color: var(--ink);
            font-size: 1.06rem;
            line-height: 1.95;
            padding: 0 0.05rem;
        }

        div[data-testid="stChatInput"] {
            position: sticky;
            bottom: 0;
            z-index: 20;
            margin-top: 0.75rem;
            padding-top: 0.9rem;
            background: linear-gradient(180deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.96) 24%, rgba(255,255,255,0.98) 100%);
        }

        div[data-testid="stChatInput"] textarea,
        div[data-testid="stChatInput"] input {
            background: #ffffff !important;
        }

        div[data-testid="stChatInput"] > div {
            border-radius: 28px !important;
            border: 1px solid var(--line) !important;
            box-shadow: var(--shadow);
            padding-top: 0.15rem;
            padding-bottom: 0.15rem;
        }

        div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 0;
        }

        div[data-testid="stAudioInput"] button {
            width: 56px;
            height: 56px;
            border-radius: 999px;
            background: var(--brand-soft);
            color: var(--brand);
            border: 1px solid #d8e5ff;
            box-shadow: none;
        }

        .result-shell {
            margin-top: 1.2rem;
            padding-top: 0.4rem;
            border-top: 1px solid var(--line);
        }

        .result-summary {
            padding: 0.6rem 0 1rem;
        }

        .result-summary-kicker {
            color: var(--brand);
            font-size: 0.84rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }

        .result-summary-title {
            color: var(--ink);
            font-size: 1.12rem;
            line-height: 1.8;
            font-weight: 600;
        }

        .result-summary-sub {
            margin-top: 0.45rem;
            color: var(--muted);
            font-size: 0.92rem;
        }

        .listing-card {
            padding: 1rem 0;
            border-bottom: 1px solid var(--line);
        }

        .listing-title {
            font-size: 1.08rem;
            font-weight: 700;
            color: var(--ink);
            margin-bottom: 0.35rem;
        }

        .listing-price-line {
            color: var(--brand);
            font-size: 1.15rem;
            font-weight: 700;
            margin-bottom: 0.4rem;
        }

        .listing-meta {
            color: var(--muted);
            font-size: 0.94rem;
            line-height: 1.85;
        }

        .tag-row {
            margin-top: 0.55rem;
        }

        .tag-pill {
            display: inline-block;
            margin: 0.12rem 0.35rem 0 0;
            padding: 0.24rem 0.58rem;
            border-radius: 999px;
            background: var(--panel-soft);
            color: #4b5563;
            font-size: 0.8rem;
        }

        .empty-photo {
            border-radius: 18px;
            border: 1px dashed var(--line-strong);
            background: var(--panel-muted);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--muted);
            font-size: 0.92rem;
        }

        .knowledge-hit {
            padding: 0.9rem 1rem;
            border-radius: 16px;
            background: var(--panel-soft);
            border: 1px solid var(--line);
            margin-bottom: 0.75rem;
        }

        .knowledge-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--ink);
        }

        .knowledge-snippet {
            margin-top: 0.35rem;
            color: #374151;
            line-height: 1.7;
        }

        .knowledge-source {
            margin-top: 0.45rem;
            color: var(--muted);
            font-size: 0.82rem;
        }

        @media (max-width: 900px) {
            .block-container {
                max-width: 100%;
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .hero-shell h1 {
                font-size: 2.2rem;
            }

            .chat-bubble.user,
            .assistant-block {
                max-width: 100%;
                width: 100%;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

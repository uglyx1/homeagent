from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #f4f6f8;
            --panel: #ffffff;
            --panel-soft: #f8fafb;
            --panel-muted: #eef3f4;
            --line: #dfe6e8;
            --line-strong: #c6d1d5;
            --ink: #182024;
            --muted: #637178;
            --muted-strong: #3d4b52;
            --brand: #0f766e;
            --brand-dark: #115e59;
            --brand-soft: #e7f5f2;
            --accent: #c05621;
            --accent-soft: #fff0e7;
            --gold: #a16207;
            --gold-soft: #fff7d6;
            --glass: rgba(255, 255, 255, 0.58);
            --glass-strong: rgba(255, 255, 255, 0.72);
            --glass-soft: rgba(255, 255, 255, 0.38);
            --glass-line: rgba(255, 255, 255, 0.64);
            --glass-shadow: 0 24px 80px rgba(31, 53, 58, 0.16);
            --shadow: 0 18px 48px rgba(32, 45, 50, 0.10);
            --shadow-soft: 0 8px 24px rgba(32, 45, 50, 0.08);
            --spring: cubic-bezier(0.18, 0.9, 0.22, 1.15);
        }

        .stApp {
            background:
                linear-gradient(135deg, rgba(238, 246, 244, 0.95) 0%, rgba(247, 250, 250, 0.84) 42%, rgba(242, 246, 248, 0.96) 100%),
                linear-gradient(90deg, rgba(15, 118, 110, 0.08) 1px, transparent 1px),
                linear-gradient(180deg, rgba(15, 118, 110, 0.06) 1px, transparent 1px);
            background-size: auto, 44px 44px, 44px 44px;
            color: var(--ink);
        }

        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background:
                linear-gradient(115deg, rgba(255, 255, 255, 0.55), rgba(255, 255, 255, 0) 42%),
                linear-gradient(180deg, rgba(15, 118, 110, 0.08), rgba(255, 255, 255, 0) 34%);
            z-index: 0;
        }

        .stApp > div {
            position: relative;
            z-index: 1;
        }

        .block-container {
            max-width: 1180px;
            padding-top: 1.2rem;
            padding-bottom: 6rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        header[data-testid="stHeader"] {
            background: rgba(244, 248, 248, 0.42);
            backdrop-filter: blur(24px) saturate(145%);
            -webkit-backdrop-filter: blur(24px) saturate(145%);
        }

        section[data-testid="stSidebar"] {
            background: rgba(251, 252, 252, 0.58);
            border-right: 1px solid rgba(255, 255, 255, 0.62);
            backdrop-filter: blur(28px) saturate(155%);
            -webkit-backdrop-filter: blur(28px) saturate(155%);
            box-shadow: 16px 0 50px rgba(32, 45, 50, 0.08);
        }

        section[data-testid="stSidebar"] .stButton button {
            border-radius: 8px;
            min-height: 2.55rem;
            font-weight: 650;
            background: rgba(255, 255, 255, 0.56);
            border: 1px solid rgba(255, 255, 255, 0.7);
            box-shadow: var(--shadow-soft);
            backdrop-filter: blur(18px) saturate(145%);
            -webkit-backdrop-filter: blur(18px) saturate(145%);
            transition: transform 360ms var(--spring), box-shadow 360ms var(--spring), border-color 220ms ease;
        }

        section[data-testid="stSidebar"] [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.54);
            border: 1px solid rgba(255, 255, 255, 0.72);
            border-radius: 8px;
            padding: 0.75rem 0.85rem;
            box-shadow: var(--shadow-soft);
            backdrop-filter: blur(18px) saturate(145%);
            -webkit-backdrop-filter: blur(18px) saturate(145%);
        }

        .sidebar-brand {
            padding: 0.85rem 0 0.35rem;
        }

        .sidebar-brand-title {
            font-size: 1.2rem;
            line-height: 1.2;
            font-weight: 800;
            color: var(--ink);
        }

        .sidebar-brand-subtitle {
            margin-top: 0.35rem;
            color: var(--muted);
            font-size: 0.88rem;
            line-height: 1.55;
        }

        .mini-topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.8rem 1rem;
            border: 1px solid rgba(255, 255, 255, 0.62);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.42);
            box-shadow: var(--shadow-soft);
            backdrop-filter: blur(22px) saturate(150%);
            -webkit-backdrop-filter: blur(22px) saturate(150%);
        }

        .mini-brand {
            font-size: 1.05rem;
            font-weight: 800;
            color: var(--ink);
        }

        .mini-subtitle {
            color: var(--muted);
            font-size: 0.9rem;
        }

        .mini-status {
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-end;
            gap: 0.45rem;
        }

        .mini-status span,
        .hero-chip,
        .result-pill,
        .tag-pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            white-space: nowrap;
        }

        .mini-status span {
            padding: 0.3rem 0.62rem;
            background: rgba(255, 255, 255, 0.48);
            border: 1px solid rgba(255, 255, 255, 0.72);
            color: var(--muted-strong);
            font-size: 0.78rem;
            font-weight: 650;
            backdrop-filter: blur(14px) saturate(145%);
            -webkit-backdrop-filter: blur(14px) saturate(145%);
        }

        .hero-shell {
            display: grid;
            grid-template-columns: minmax(0, 1.25fr) minmax(280px, 0.75fr);
            gap: 1rem;
            padding: 0.75rem 0 1rem;
            align-items: stretch;
        }

        .hero-main,
        .hero-rail,
        .assistant-card,
        .knowledge-hit,
        .summary-card,
        .listing-card,
        .detail-panel,
        .saved-note {
            border: 1px solid var(--line);
            background:
                linear-gradient(135deg, rgba(255, 255, 255, 0.74), rgba(255, 255, 255, 0.38)),
                rgba(255, 255, 255, 0.42);
            box-shadow: var(--glass-shadow);
            border-radius: 8px;
            backdrop-filter: blur(26px) saturate(160%);
            -webkit-backdrop-filter: blur(26px) saturate(160%);
            position: relative;
            overflow: hidden;
        }

        .hero-main::before,
        .hero-rail::before,
        .assistant-card::before,
        .knowledge-hit::before,
        .summary-card::before,
        .listing-card::before,
        .detail-panel::before,
        .saved-note::before {
            content: "";
            position: absolute;
            inset: 0;
            pointer-events: none;
            border-radius: inherit;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.72), rgba(255, 255, 255, 0.04) 46%, rgba(15, 118, 110, 0.06));
            opacity: 0.72;
        }

        .hero-main {
            padding: 1.6rem;
            min-height: 260px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .hero-rail {
            padding: 1.1rem;
            display: grid;
            gap: 0.75rem;
            align-content: start;
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(247, 251, 250, 0.32)),
                rgba(255, 255, 255, 0.38);
        }

        .hero-kicker,
        .result-summary-kicker {
            color: var(--brand);
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .hero-shell h1 {
            margin: 1rem 0 0;
            max-width: 760px;
            font-size: 2.9rem;
            line-height: 1.1;
            letter-spacing: 0;
            color: var(--ink);
        }

        .hero-shell p {
            margin: 0.85rem 0 0;
            color: var(--muted);
            font-size: 1.05rem;
            line-height: 1.75;
            max-width: 780px;
        }

        .hero-chips,
        .hero-suggestions {
            display: flex;
            flex-wrap: wrap;
            gap: 0.65rem;
            margin-top: 1rem;
        }

        .hero-chip {
            padding: 0.42rem 0.7rem;
            background: rgba(231, 245, 242, 0.54);
            border: 1px solid rgba(255, 255, 255, 0.72);
            color: var(--brand-dark);
            font-size: 0.83rem;
            font-weight: 700;
            backdrop-filter: blur(14px) saturate(145%);
            -webkit-backdrop-filter: blur(14px) saturate(145%);
        }

        .hero-suggestions span,
        .prompt-card {
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.68);
            background: rgba(255, 255, 255, 0.46);
            color: var(--muted-strong);
            box-shadow: var(--shadow-soft);
            backdrop-filter: blur(16px) saturate(145%);
            -webkit-backdrop-filter: blur(16px) saturate(145%);
            transition: transform 420ms var(--spring), box-shadow 420ms var(--spring), background 220ms ease;
        }

        .hero-suggestions span {
            padding: 0.58rem 0.85rem;
            font-size: 0.92rem;
        }

        .hero-rail-title {
            color: var(--ink);
            font-size: 0.95rem;
            font-weight: 800;
        }

        .hero-rail-item {
            padding: 0.75rem 0;
            border-top: 1px solid var(--line);
        }

        .hero-rail-value {
            color: var(--ink);
            font-size: 1.35rem;
            font-weight: 850;
            line-height: 1.15;
        }

        .hero-rail-label {
            margin-top: 0.25rem;
            color: var(--muted);
            font-size: 0.84rem;
        }

        .chat-stream-shell {
            margin-top: 0.5rem;
        }

        .suggestion-title {
            margin: 0.2rem 0 0.75rem;
            color: var(--muted);
            font-size: 0.88rem;
            font-weight: 700;
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
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.54);
            border: 1px solid rgba(255, 255, 255, 0.68);
            padding: 0.85rem 1rem;
            color: var(--ink);
            font-size: 1rem;
            line-height: 1.75;
            word-break: break-word;
            box-shadow: var(--shadow-soft);
            backdrop-filter: blur(18px) saturate(145%);
            -webkit-backdrop-filter: blur(18px) saturate(145%);
        }

        .assistant-avatar {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            background: linear-gradient(135deg, var(--brand), #38a89d);
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
            margin-bottom: 0.9rem;
            box-shadow: var(--shadow-soft);
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
            background: linear-gradient(180deg, rgba(244,246,248,0) 0%, rgba(244,246,248,0.62) 25%, rgba(244,246,248,0.88) 100%);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
        }

        div[data-testid="stChatInput"] textarea,
        div[data-testid="stChatInput"] input {
            background: rgba(255, 255, 255, 0.5) !important;
        }

        div[data-testid="stChatInput"] > div {
            border-radius: 8px !important;
            border: 1px solid rgba(255, 255, 255, 0.68) !important;
            box-shadow: var(--shadow);
            padding-top: 0.15rem;
            padding-bottom: 0.15rem;
            background: rgba(255, 255, 255, 0.52) !important;
            backdrop-filter: blur(22px) saturate(155%);
            -webkit-backdrop-filter: blur(22px) saturate(155%);
        }

        div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 0;
        }

        div[data-testid="stAudioInput"] button {
            width: 56px;
            height: 56px;
            border-radius: 8px;
            background: rgba(231, 245, 242, 0.58);
            color: var(--brand);
            border: 1px solid rgba(255, 255, 255, 0.72);
            box-shadow: none;
        }

        div[data-testid="stButton"] button,
        div[data-testid="stLinkButton"] a {
            border-radius: 8px;
            border-color: rgba(255, 255, 255, 0.72);
            font-weight: 650;
            background: rgba(255, 255, 255, 0.48);
            box-shadow: var(--shadow-soft);
            backdrop-filter: blur(16px) saturate(145%);
            -webkit-backdrop-filter: blur(16px) saturate(145%);
            transition: transform 360ms var(--spring), box-shadow 360ms var(--spring), color 180ms ease, border-color 180ms ease;
        }

        div[data-testid="stButton"] button:hover,
        div[data-testid="stLinkButton"] a:hover {
            border-color: var(--brand);
            color: var(--brand);
            transform: translateY(-2px) scale(1.012);
            box-shadow: 0 14px 32px rgba(15, 118, 110, 0.14);
        }

        .result-shell {
            margin-top: 1.2rem;
            padding-top: 0.8rem;
            border-top: 1px solid var(--line);
        }

        .result-summary-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.35fr) repeat(3, minmax(120px, 0.45fr));
            gap: 0.75rem;
            margin: 0.2rem 0 1rem;
        }

        .summary-card {
            padding: 1rem;
            box-shadow: var(--shadow-soft);
        }

        .summary-card.primary {
            background:
                linear-gradient(135deg, rgba(255, 255, 255, 0.76), rgba(255, 255, 255, 0.36)),
                rgba(255, 255, 255, 0.42);
        }

        .result-summary-title {
            color: var(--ink);
            font-size: 1.12rem;
            line-height: 1.7;
            font-weight: 700;
            margin-top: 0.35rem;
        }

        .result-summary-sub {
            margin-top: 0.45rem;
            color: var(--muted);
            font-size: 0.92rem;
        }

        .summary-number {
            font-size: 1.55rem;
            line-height: 1.05;
            color: var(--ink);
            font-weight: 850;
        }

        .summary-label {
            margin-top: 0.35rem;
            color: var(--muted);
            font-size: 0.82rem;
            line-height: 1.35;
        }

        .result-pill {
            margin-top: 0.7rem;
            padding: 0.28rem 0.55rem;
            background: rgba(255, 240, 231, 0.62);
            border: 1px solid rgba(255, 255, 255, 0.7);
            color: var(--accent);
            font-size: 0.78rem;
            font-weight: 750;
            backdrop-filter: blur(14px) saturate(145%);
            -webkit-backdrop-filter: blur(14px) saturate(145%);
        }

        .listing-card {
            display: grid;
            grid-template-columns: minmax(210px, 0.85fr) minmax(0, 1.35fr);
            gap: 1rem;
            padding: 0.85rem;
            margin: 0.85rem 0 0.4rem;
            box-shadow: var(--shadow-soft);
            transform: perspective(900px) rotateX(var(--tilt-x, 0deg)) rotateY(var(--tilt-y, 0deg)) translate3d(var(--magnet-x, 0px), var(--magnet-y, 0px), 0);
            transform-style: preserve-3d;
            transition: transform 520ms var(--spring), box-shadow 520ms var(--spring), border-color 220ms ease;
            will-change: transform;
        }

        .listing-card:hover,
        .hero-main:hover,
        .hero-rail:hover,
        .summary-card:hover {
            border-color: rgba(255, 255, 255, 0.88);
            box-shadow: 0 28px 90px rgba(31, 53, 58, 0.18);
        }

        .listing-media {
            position: relative;
            min-height: 220px;
            border-radius: 6px;
            overflow: hidden;
            background: rgba(238, 243, 244, 0.54);
            transform: translateZ(16px);
        }

        .listing-media img {
            width: 100%;
            height: 100%;
            min-height: 220px;
            object-fit: cover;
            display: block;
        }

        .listing-rank {
            position: absolute;
            left: 0.7rem;
            top: 0.7rem;
            padding: 0.28rem 0.52rem;
            border-radius: 6px;
            background: rgba(24, 32, 36, 0.56);
            color: #ffffff;
            font-size: 0.78rem;
            font-weight: 800;
            backdrop-filter: blur(14px) saturate(145%);
            -webkit-backdrop-filter: blur(14px) saturate(145%);
        }

        .listing-body {
            min-width: 0;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 0.75rem;
        }

        .listing-heading {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 0.75rem;
        }

        .listing-title {
            font-size: 1.14rem;
            line-height: 1.35;
            font-weight: 800;
            color: var(--ink);
        }

        .listing-price-line {
            color: var(--brand-dark);
            font-size: 1.2rem;
            font-weight: 850;
            white-space: nowrap;
            text-align: right;
        }

        .listing-meta-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.5rem;
        }

        .listing-meta-item {
            padding: 0.55rem 0.6rem;
            border: 1px solid rgba(255, 255, 255, 0.68);
            border-radius: 6px;
            background: rgba(248, 250, 251, 0.48);
            min-width: 0;
            backdrop-filter: blur(14px) saturate(145%);
            -webkit-backdrop-filter: blur(14px) saturate(145%);
        }

        .listing-meta-label {
            color: var(--muted);
            font-size: 0.75rem;
            line-height: 1.2;
        }

        .listing-meta-value {
            margin-top: 0.22rem;
            color: var(--ink);
            font-size: 0.9rem;
            font-weight: 720;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .listing-reason {
            padding: 0.72rem 0.8rem;
            border-left: 3px solid var(--brand);
            background: rgba(231, 245, 242, 0.54);
            color: var(--muted-strong);
            line-height: 1.65;
            font-size: 0.92rem;
            border-radius: 6px;
            backdrop-filter: blur(14px) saturate(145%);
            -webkit-backdrop-filter: blur(14px) saturate(145%);
        }

        .tag-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
        }

        .tag-pill {
            padding: 0.24rem 0.58rem;
            background: rgba(248, 250, 251, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.68);
            color: #4b5563;
            font-size: 0.8rem;
            font-weight: 650;
            backdrop-filter: blur(12px) saturate(140%);
            -webkit-backdrop-filter: blur(12px) saturate(140%);
        }

        .listing-status-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem;
        }

        .listing-status {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.22rem 0.52rem;
            background: rgba(255, 247, 214, 0.66);
            border: 1px solid rgba(255, 255, 255, 0.68);
            color: var(--gold);
            font-size: 0.76rem;
            font-weight: 750;
            backdrop-filter: blur(12px) saturate(140%);
            -webkit-backdrop-filter: blur(12px) saturate(140%);
        }

        .empty-photo {
            height: 100%;
            min-height: 210px;
            border-radius: 6px;
            border: 1px dashed var(--line-strong);
            background: rgba(238, 243, 244, 0.44);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--muted);
            font-size: 0.92rem;
        }

        .knowledge-hit {
            padding: 0.9rem 1rem;
            margin-bottom: 0.75rem;
            box-shadow: var(--shadow-soft);
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

        .detail-panel,
        .saved-note {
            padding: 1rem;
            margin: 0.75rem 0;
            box-shadow: var(--shadow-soft);
        }

        .favorite-line,
        .conversation-line {
            padding: 0.72rem 0;
            border-bottom: 1px solid var(--line);
        }

        .favorite-title {
            color: var(--ink);
            font-weight: 760;
        }

        .favorite-meta,
        .conversation-answer {
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.65;
            margin-top: 0.25rem;
        }

        .chaoxuan-cursor,
        .chaoxuan-cursor-dot {
            position: fixed;
            left: 0;
            top: 0;
            pointer-events: none;
            z-index: 2147483647;
            opacity: 0;
            display: none !important;
            transform: translate3d(-100px, -100px, 0);
            transition: opacity 180ms ease, width 240ms var(--spring), height 240ms var(--spring), border-color 180ms ease, background 180ms ease;
            mix-blend-mode: multiply;
        }

        .chaoxuan-cursor {
            width: 34px;
            height: 34px;
            margin-left: -17px;
            margin-top: -17px;
            border-radius: 999px;
            border: 1px solid rgba(15, 118, 110, 0.55);
            background: rgba(255, 255, 255, 0.22);
            box-shadow: 0 10px 34px rgba(15, 118, 110, 0.18);
            backdrop-filter: blur(8px) saturate(155%);
            -webkit-backdrop-filter: blur(8px) saturate(155%);
        }

        .chaoxuan-cursor-dot {
            width: 6px;
            height: 6px;
            margin-left: -3px;
            margin-top: -3px;
            border-radius: 999px;
            background: var(--brand);
            box-shadow: 0 0 16px rgba(15, 118, 110, 0.34);
        }

        body.chaoxuan-cursor-ready .chaoxuan-cursor,
        body.chaoxuan-cursor-ready .chaoxuan-cursor-dot {
            opacity: 1;
        }

        body.chaoxuan-cursor-hover .chaoxuan-cursor {
            width: 52px;
            height: 52px;
            margin-left: -26px;
            margin-top: -26px;
            border-color: rgba(192, 86, 33, 0.62);
            background: rgba(255, 240, 231, 0.28);
        }

        body.chaoxuan-cursor-down .chaoxuan-cursor {
            width: 26px;
            height: 26px;
            margin-left: -13px;
            margin-top: -13px;
        }

        .hero-main,
        .hero-rail,
        .summary-card,
        .listing-card,
        .chat-bubble.user,
        .assistant-card,
        .knowledge-hit,
        div[data-testid="stButton"] button,
        div[data-testid="stLinkButton"] a {
            cursor: auto;
        }

        @media (hover: none), (pointer: coarse), (prefers-reduced-motion: reduce) {
            .chaoxuan-cursor,
            .chaoxuan-cursor-dot {
                display: none;
            }

            .hero-main,
            .hero-rail,
            .summary-card,
            .listing-card,
            .chat-bubble.user,
            .assistant-card,
            .knowledge-hit,
            div[data-testid="stButton"] button,
            div[data-testid="stLinkButton"] a {
                cursor: auto;
            }

            .listing-card {
                transform: none !important;
            }
        }

        @media (max-width: 900px) {
            .block-container {
                max-width: 100%;
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .hero-shell,
            .result-summary-grid,
            .listing-card {
                grid-template-columns: 1fr;
            }

            .hero-shell h1 {
                font-size: 2.2rem;
            }

            .chat-bubble.user,
            .assistant-block {
                max-width: 100%;
                width: 100%;
            }

            .listing-meta-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .mini-topbar {
                align-items: flex-start;
                flex-direction: column;
            }

            .mini-status {
                justify-content: flex-start;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_motion() -> None:
    components.html(
        """
        <script>
        (() => {
            const doc = window.parent?.document;
            if (!doc) return;
            doc.querySelectorAll(".chaoxuan-cursor, .chaoxuan-cursor-dot").forEach((item) => item.remove());
            doc.body.classList.remove("chaoxuan-cursor-ready", "chaoxuan-cursor-hover", "chaoxuan-cursor-down");
            if (doc.getElementById("chaoxuan-motion-runtime")) return;
            const view = doc.defaultView || window.parent;
            const shouldSkipMotion =
                view.matchMedia?.("(hover: none)")?.matches ||
                view.matchMedia?.("(pointer: coarse)")?.matches ||
                view.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
            if (shouldSkipMotion) return;

            const marker = doc.createElement("script");
            marker.id = "chaoxuan-motion-runtime";
            marker.type = "text/plain";
            doc.head.appendChild(marker);

            function attachCardPhysics(root = doc) {
                root.querySelectorAll(".listing-card:not([data-spring-card])").forEach((card) => {
                    card.dataset.springCard = "1";
                    let raf = 0;

                    card.addEventListener("pointermove", (event) => {
                        cancelAnimationFrame(raf);
                        raf = requestAnimationFrame(() => {
                            const rect = card.getBoundingClientRect();
                            const relX = (event.clientX - rect.left) / rect.width - 0.5;
                            const relY = (event.clientY - rect.top) / rect.height - 0.5;
                            card.style.setProperty("--tilt-x", `${(-relY * 2.6).toFixed(3)}deg`);
                            card.style.setProperty("--tilt-y", `${(relX * 3.2).toFixed(3)}deg`);
                            card.style.setProperty("--magnet-x", `${(relX * 4).toFixed(2)}px`);
                            card.style.setProperty("--magnet-y", `${(relY * 4).toFixed(2)}px`);
                        });
                    }, { passive: true });

                    card.addEventListener("pointerleave", () => {
                        card.style.setProperty("--tilt-x", "0deg");
                        card.style.setProperty("--tilt-y", "0deg");
                        card.style.setProperty("--magnet-x", "0px");
                        card.style.setProperty("--magnet-y", "0px");
                    }, { passive: true });
                });
            }

            attachCardPhysics();
            new MutationObserver(() => attachCardPhysics()).observe(doc.body, { childList: true, subtree: true });
        })();
        </script>
        """,
        height=0,
        width=0,
    )

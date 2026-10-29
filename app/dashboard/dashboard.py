import html
import json
import sqlite3
from pathlib import Path

import joblib
import pandas as pd
import plotly.express as px
import streamlit as st


# ==================================================
# PATHS
# ==================================================
ROOT_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT_DIR / "data_fresh"
DB_PATH = DATA_DIR / "customerpulse.db"

MODEL_DIR = ROOT_DIR / "models"
SENTIMENT_MODEL_PATH = MODEL_DIR / "sentiment_model.joblib"
THEME_MODEL_PATH = MODEL_DIR / "theme_model.joblib"

REPORT_PATH = ROOT_DIR / "reports" / "model_evaluation.json"


# ==================================================
# PAGE CONFIGURATION
# ==================================================
st.set_page_config(
    page_title="CustomerPulse AI",
    page_icon="📊",
    layout="wide",
)


# ==================================================
# DESIGN SYSTEM (COLORS, FONTS, CSS)
# ==================================================
FONT_STACK = (
    "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, "
    "'Helvetica Neue', Arial, sans-serif"
)

COLOR_INDIGO = "#6366F1"
COLOR_CYAN = "#22D3EE"
COLOR_POSITIVE = "#34D399"
COLOR_NEUTRAL = "#FBBF24"
COLOR_NEGATIVE = "#F87171"
COLOR_SLATE = "#94A3B8"

THEME_PALETTE = [
    "#3B82F6", "#8B5CF6", "#22D3EE", "#6366F1",
    "#A78BFA", "#38BDF8", "#818CF8", "#67E8F9",
]

CUSTOM_CSS = """
<style>
/* ---------- Page background ---------- */
.stApp {
    background: linear-gradient(135deg, #0B1437 0%, #1E2A78 52%, #3B2A8F 100%);
    background-attachment: fixed;
    font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
        'Helvetica Neue', Arial, sans-serif;
    color: #E2E8F0;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stAppDeployButton"], .stDeployButton { display: none; }
.block-container {
    padding-top: 1.4rem;
    padding-bottom: 2rem;
    max-width: 1320px;
}
:where(.stApp) p, :where(.stApp) li, :where(.stApp) label { color: #CBD5E1; }
.stApp h1, .stApp h2, .stApp h3 { color: #FFFFFF; }
.stApp hr { border-color: rgba(255,255,255,0.10); }
.stApp [data-testid="stCaptionContainer"] { color: #94A3B8; }

/* ---------- Top bar ---------- */
.cp-topbar {
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 0.6rem;
    margin-bottom: 0.9rem;
}
.cp-crumb { color: #94A3B8; font-size: 0.85rem; }
.cp-crumb b { color: #FFFFFF; font-weight: 600; }
.cp-crumb span { margin: 0 0.35rem; }
.cp-badges { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.cp-badge {
    border-radius: 999px;
    padding: 0.2rem 0.75rem;
    font-size: 0.74rem;
    font-weight: 650;
    border: 1px solid transparent;
}
.cp-badge-blue  { background: rgba(59,130,246,0.18); color: #93C5FD; border-color: rgba(59,130,246,0.4); }
.cp-badge-amber { background: rgba(251,191,36,0.14); color: #FCD34D; border-color: rgba(251,191,36,0.35); }

/* ---------- Hero ---------- */
.cp-hero {
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: center;
    gap: 1rem;
    background:
        radial-gradient(circle at 92% 10%, rgba(34,211,238,0.20), rgba(34,211,238,0) 45%),
        linear-gradient(120deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 16px;
    padding: 1.3rem 1.6rem 1rem 1.6rem;
    margin-bottom: 1.2rem;
}
.cp-eyebrow {
    color: #A5B4FC;
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
}
.stApp .cp-hero h1 {
    color: #FFFFFF;
    font-size: 1.85rem;
    font-weight: 750;
    line-height: 1.2;
    margin: 0.25rem 0 0.35rem 0;
    padding: 0;
}
.cp-hero p { margin: 0; color: #CBD5E1; font-size: 0.95rem; line-height: 1.55; max-width: 720px; }
.cp-hero-art { opacity: 0.9; }
.cp-disclaimer {
    grid-column: 1 / -1;
    margin-top: 0.4rem;
    padding-top: 0.6rem;
    border-top: 1px solid rgba(255,255,255,0.12);
    color: #A5B4FC;
    font-size: 0.82rem;
}

/* ---------- Section headers ---------- */
.cp-label {
    color: #60A5FA;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
}
.cp-section-title { font-size: 1.3rem; font-weight: 700; color: #FFFFFF; margin: 0.1rem 0 0.1rem 0; }
.cp-section-desc  { color: #94A3B8; font-size: 0.92rem; margin: 0 0 1rem 0; }
.cp-subhead { margin: 0.4rem 0 0.6rem 0; }
.cp-subhead span { color: #94A3B8; font-size: 0.82rem; margin-left: 0.5rem; }

/* ---------- Glass cards ---------- */
.cp-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 14px;
    padding: 1.1rem 1.25rem;
    margin-bottom: 1rem;
}
.cp-card h4 { margin: 0 0 0.5rem 0; font-size: 1rem; font-weight: 700; color: #FFFFFF; }
.cp-card ul { margin: 0; padding-left: 1.1rem; }
.cp-card li, .cp-card p { color: #CBD5E1; font-size: 0.93rem; line-height: 1.65; }
.cp-card-warn { border-left: 4px solid #FBBF24; background: rgba(251,191,36,0.07); }
.cp-chip {
    display: inline-block;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    color: #E2E8F0;
    border-radius: 8px;
    padding: 0.2rem 0.65rem;
    font-size: 0.82rem;
    font-weight: 600;
    margin: 0.15rem 0.3rem 0.15rem 0;
}

/* ---------- Metric cards ---------- */
.cp-metric {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 14px;
    padding: 1rem 1.15rem;
    margin-bottom: 0.6rem;
    transition: border-color 0.2s ease, transform 0.2s ease;
}
.cp-metric:hover { border-color: rgba(96,165,250,0.5); transform: translateY(-1px); }
.cp-metric-top {
    display: flex; align-items: center; gap: 0.55rem;
    color: #94A3B8; font-size: 0.82rem; font-weight: 600;
}
.cp-metric-icon {
    width: 30px; height: 30px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.cp-metric-value { color: #FFFFFF; font-size: 1.9rem; font-weight: 750; line-height: 1.15; margin: 0.6rem 0 0.25rem 0; }
.cp-metric-value-sm { font-size: 1.3rem; word-break: break-word; }
.cp-metric-foot { font-size: 0.76rem; font-weight: 600; }
.cp-tone-blue   { box-shadow: inset 0 2px 0 #3B82F6; }
.cp-tone-violet { box-shadow: inset 0 2px 0 #8B5CF6; }
.cp-tone-cyan   { box-shadow: inset 0 2px 0 #22D3EE; }
.cp-tone-green  { box-shadow: inset 0 2px 0 #34D399; }
.cp-tone-amber  { box-shadow: inset 0 2px 0 #FBBF24; }
.cp-tone-red    { box-shadow: inset 0 2px 0 #F87171; }
.cp-tone-blue   .cp-metric-icon { background: rgba(59,130,246,0.20);  color: #60A5FA; }
.cp-tone-blue   .cp-metric-foot { color: #60A5FA; }
.cp-tone-violet .cp-metric-icon { background: rgba(139,92,246,0.22);  color: #A78BFA; }
.cp-tone-violet .cp-metric-foot { color: #A78BFA; }
.cp-tone-cyan   .cp-metric-icon { background: rgba(34,211,238,0.18);  color: #22D3EE; }
.cp-tone-cyan   .cp-metric-foot { color: #22D3EE; }
.cp-tone-green  .cp-metric-icon { background: rgba(52,211,153,0.18);  color: #34D399; }
.cp-tone-green  .cp-metric-foot { color: #34D399; }
.cp-tone-amber  .cp-metric-icon { background: rgba(251,191,36,0.18);  color: #FBBF24; }
.cp-tone-amber  .cp-metric-foot { color: #FBBF24; }
.cp-tone-red    .cp-metric-icon { background: rgba(248,113,113,0.18); color: #F87171; }
.cp-tone-red    .cp-metric-foot { color: #F87171; }

/* ---------- Charts as cards ---------- */
[data-testid="stPlotlyChart"] {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 14px;
    padding: 0.4rem 0.5rem;
    overflow: hidden;
}

/* ---------- Prediction results ---------- */
.cp-result-label { color: #94A3B8; font-size: 0.76rem; font-weight: 700; letter-spacing: 0.07em; text-transform: uppercase; }
.cp-pill {
    display: inline-block;
    border-radius: 999px;
    padding: 0.3rem 1rem;
    font-size: 1.15rem;
    font-weight: 700;
    margin: 0.55rem 0 0.9rem 0;
    border: 1px solid transparent;
}
.cp-pill-positive { background: rgba(52,211,153,0.15);  color: #6EE7B7; border-color: rgba(52,211,153,0.4); }
.cp-pill-neutral  { background: rgba(251,191,36,0.15);  color: #FCD34D; border-color: rgba(251,191,36,0.4); }
.cp-pill-negative { background: rgba(248,113,113,0.15); color: #FCA5A5; border-color: rgba(248,113,113,0.4); }
.cp-pill-theme    { background: rgba(139,92,246,0.20);  color: #C4B5FD; border-color: rgba(139,92,246,0.45); }
.cp-pill-other    { background: rgba(148,163,184,0.15); color: #E2E8F0; border-color: rgba(148,163,184,0.35); }
.cp-conf-text { color: #CBD5E1; font-size: 0.88rem; margin-bottom: 0.35rem; }
.cp-conf-track { background: rgba(255,255,255,0.10); border-radius: 999px; height: 8px; overflow: hidden; }
.cp-conf-fill  { height: 8px; border-radius: 999px; background: linear-gradient(90deg, #22D3EE, #6366F1, #8B5CF6); }

/* ---------- Match count ---------- */
.cp-count {
    display: inline-block;
    background: rgba(59,130,246,0.18);
    border: 1px solid rgba(59,130,246,0.4);
    color: #BFDBFE;
    border-radius: 999px;
    padding: 0.25rem 0.85rem;
    font-size: 0.85rem;
    font-weight: 600;
    margin: 0.3rem 0 0.7rem 0;
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0A1236 0%, #101B52 100%);
    border-right: 1px solid rgba(255,255,255,0.08);
}
[data-testid="stSidebar"] > div:first-child { background: transparent; }
.cp-side-brand { display: flex; align-items: center; gap: 0.7rem; }
.cp-logo {
    width: 38px; height: 38px; border-radius: 10px;
    background: linear-gradient(135deg, #3B82F6, #8B5CF6);
    color: #FFFFFF;
    display: flex; align-items: center; justify-content: center;
}
.cp-side-name { font-weight: 750; font-size: 1.02rem; color: #FFFFFF; line-height: 1.2; }
.cp-side-sub  { font-size: 0.74rem; color: #94A3B8; }
.cp-side-desc { font-size: 0.82rem; color: #94A3B8; margin: 0.8rem 0 0.2rem 0; line-height: 1.5; }
.cp-side-label {
    color: #60A5FA; font-size: 0.74rem; font-weight: 700;
    letter-spacing: 0.08em; text-transform: uppercase;
    margin: 0.6rem 0 0.2rem 0;
}
.cp-side-stat {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 10px;
    padding: 0.65rem 0.85rem;
    font-size: 0.82rem;
    color: #CBD5E1;
    margin-top: 0.5rem;
    line-height: 1.7;
}
.cp-side-stat b { color: #FFFFFF; }
.cp-status {
    display: inline-flex; align-items: center; gap: 0.45rem;
    background: rgba(52,211,153,0.12);
    border: 1px solid rgba(52,211,153,0.35);
    color: #6EE7B7;
    border-radius: 999px;
    padding: 0.2rem 0.7rem;
    font-size: 0.76rem;
    font-weight: 650;
    margin-top: 0.6rem;
}
.cp-dot { width: 7px; height: 7px; border-radius: 50%; background: #34D399; display: inline-block; }
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    max-height: 150px;
    overflow-y: auto;
}

/* ---------- Inputs ---------- */
[data-baseweb="input"],
[data-baseweb="textarea"] {
    background: rgba(15,23,42,0.55);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 10px;
}
[data-baseweb="base-input"] { background: transparent; }
.stApp input, .stApp textarea { color: #F8FAFC; }
.stApp input::placeholder,
.stApp textarea::placeholder { color: #94A3B8; opacity: 1; }
[data-baseweb="input"]:focus-within,
[data-baseweb="textarea"]:focus-within {
    border-color: #60A5FA;
    box-shadow: 0 0 0 3px rgba(96,165,250,0.25);
}
[data-baseweb="select"] > div {
    background-color: rgba(15,23,42,0.55);
    border-color: rgba(255,255,255,0.15);
    color: #F8FAFC;
}
[data-baseweb="tag"],
[data-testid="stMultiSelect"] [data-baseweb="tag"] {
    background-color: #2563EB !important;
    border-radius: 6px;
}
[data-baseweb="tag"] span,
[data-baseweb="tag"] svg { color: #FFFFFF !important; fill: #FFFFFF; }
[data-baseweb="popover"] ul[role="listbox"] { background: #0F172A; }
[data-baseweb="popover"] li[role="option"] { color: #E2E8F0; }

/* ---------- Buttons ---------- */
button[data-testid="stBaseButton-primary"],
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2563EB, #7C3AED);
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 0.55rem 1.6rem;
    font-weight: 650;
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}
button[data-testid="stBaseButton-primary"]:hover,
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 8px 20px rgba(59,130,246,0.40);
    color: #FFFFFF;
    transform: translateY(-1px);
}
[data-testid="stDownloadButton"] button,
.stDownloadButton > button {
    background: rgba(255,255,255,0.08);
    color: #FFFFFF;
    border: 1px solid rgba(255,255,255,0.20);
    border-radius: 10px;
    font-weight: 600;
}
[data-testid="stDownloadButton"] button:hover,
.stDownloadButton > button:hover { border-color: #60A5FA; color: #FFFFFF; }
button:focus-visible {
    outline: 3px solid #93C5FD;
    outline-offset: 2px;
}

/* ---------- Tabs as pill switcher ---------- */
[data-baseweb="tab-list"] {
    display: inline-flex;
    gap: 0.25rem;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 12px;
    padding: 4px;
    margin-bottom: 0.8rem;
}
[data-baseweb="tab-highlight"],
[data-baseweb="tab-border"] { display: none; }
[data-baseweb="tab"] {
    color: #94A3B8;
    background: transparent;
    border-radius: 9px;
    padding: 0.45rem 1rem;
    height: auto;
}
[data-baseweb="tab"] p { color: inherit; margin: 0; font-weight: 600; }
[data-baseweb="tab"]:hover { color: #FFFFFF; }
[data-baseweb="tab"][aria-selected="true"] { background: #2563EB; color: #FFFFFF; }
[data-baseweb="tab"][aria-selected="true"] p { color: #FFFFFF; }

/* ---------- Alerts and table ---------- */
[data-testid="stAlert"] {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 12px;
    color: #E2E8F0;
}
[data-testid="stDataFrame"] {
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 12px;
    overflow: hidden;
}

/* ---------- Footer ---------- */
.cp-footer {
    margin-top: 2rem;
    padding-top: 0.9rem;
    border-top: 1px solid rgba(255,255,255,0.10);
    color: #94A3B8;
    font-size: 0.78rem;
    text-align: center;
}

/* ---------- Responsive ---------- */
@media (max-width: 768px) {
    .cp-hero { grid-template-columns: 1fr; padding: 1.1rem; }
    .cp-hero-art { display: none; }
    .stApp .cp-hero h1 { font-size: 1.45rem; }
    .cp-metric-value { font-size: 1.5rem; }
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    [data-baseweb="tab-list"] { display: flex; overflow-x: auto; }
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==================================================
# SMALL UI HELPERS (PRESENTATION ONLY)
# ==================================================
# Simple inline SVG icons (no external assets).
ICON_PATHS = {
    "chat": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "box": (
        '<path d="m7.5 4.27 9 5.15"/>'
        '<path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/>'
        '<path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>'
    ),
    "layers": (
        '<path d="m12 2-10 5 10 5 10-5z"/>'
        '<path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/>'
    ),
    "check": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "bars": '<path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>',
    "smile": (
        '<circle cx="12" cy="12" r="10"/>'
        '<path d="M8 14s1.5 2 4 2 4-2 4-2"/>'
        '<path d="M9 9h.01"/><path d="M15 9h.01"/>'
    ),
    "tag": (
        '<path d="M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 8.704a2.426 2.426 0 0 0 3.42 0l6.58-6.58a2.426 2.426 0 0 0 0-3.42z"/>'
        '<circle cx="7.5" cy="7.5" r="1"/>'
    ),
    "calendar": (
        '<path d="M8 2v4"/><path d="M16 2v4"/>'
        '<rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/>'
    ),
}


def icon(name):
    """Return an inline SVG icon."""
    return (
        '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round">{ICON_PATHS[name]}</svg>'
    )


def section_header(label, title, description=""):
    """Render a small section label, title and description."""
    st.markdown(
        f'<div class="cp-label">{html.escape(label)}</div>'
        f'<div class="cp-section-title">{html.escape(title)}</div>'
        f'<div class="cp-section-desc">{html.escape(description)}</div>',
        unsafe_allow_html=True,
    )


def sub_header(label, note=""):
    """Render a small sub-section label with a muted note."""
    st.markdown(
        f'<div class="cp-subhead"><span class="cp-label">'
        f'{html.escape(label)}</span><span>{html.escape(note)}</span></div>',
        unsafe_allow_html=True,
    )


def metric_card(icon_name, label, value, foot="", tone="blue", small=False):
    """Render one glass metric card."""
    size_class = " cp-metric-value-sm" if small else ""
    st.markdown(
        f'<div class="cp-metric cp-tone-{tone}">'
        '<div class="cp-metric-top">'
        f'<span class="cp-metric-icon">{icon(icon_name)}</span>'
        f'<span>{html.escape(str(label))}</span></div>'
        f'<div class="cp-metric-value{size_class}">'
        f'{html.escape(str(value))}</div>'
        f'<div class="cp-metric-foot">{html.escape(str(foot))}</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def sentiment_pill_class(label):
    """Choose a badge color class for a sentiment label."""
    key = str(label).strip().lower()
    if key.startswith("pos"):
        return "cp-pill-positive"
    if key.startswith("neg"):
        return "cp-pill-negative"
    if key.startswith("neu"):
        return "cp-pill-neutral"
    return "cp-pill-other"


def sentiment_color(label):
    """Choose a chart color for a sentiment label."""
    key = str(label).strip().lower()
    if key.startswith("pos"):
        return COLOR_POSITIVE
    if key.startswith("neg"):
        return COLOR_NEGATIVE
    if key.startswith("neu"):
        return COLOR_NEUTRAL
    return COLOR_SLATE


def sentiment_tone(label):
    """Choose a metric card tone for a sentiment label."""
    key = str(label).strip().lower()
    if key.startswith("pos"):
        return "green"
    if key.startswith("neg"):
        return "red"
    if key.startswith("neu"):
        return "amber"
    return "blue"


def result_card(title, value, pill_class, confidence, confidence_label):
    """Render a prediction result card with a confidence bar."""
    if confidence is not None:
        percent = max(0.0, min(confidence, 1.0)) * 100
        confidence_html = (
            f'<div class="cp-conf-text">{html.escape(confidence_label)}: '
            f'<b>{confidence:.1%}</b></div>'
            '<div class="cp-conf-track">'
            f'<div class="cp-conf-fill" style="width:{percent:.1f}%"></div>'
            '</div>'
        )
    else:
        confidence_html = (
            '<div class="cp-conf-text">Confidence estimate '
            'is not available for this model.</div>'
        )

    st.markdown(
        '<div class="cp-card">'
        f'<div class="cp-result-label">{html.escape(title)}</div>'
        f'<span class="cp-pill {pill_class}">{html.escape(str(value))}</span>'
        f'{confidence_html}'
        '</div>',
        unsafe_allow_html=True,
    )


def style_figure(fig, title, subtitle, height=400):
    """Apply one consistent dark Plotly style to every chart."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_STACK, color="#CBD5E1", size=12),
        title=dict(
            text=(
                f"<b>{title}</b><br>"
                f"<span style='font-size:12px;color:#94A3B8'>"
                f"{subtitle}</span>"
            ),
            x=0.02,
            xanchor="left",
            font=dict(size=16, color="#FFFFFF"),
        ),
        margin=dict(l=20, r=20, t=80, b=20),
        height=height,
        hoverlabel=dict(
            bgcolor="#0F172A",
            bordercolor="#3B82F6",
            font=dict(family=FONT_STACK, size=13, color="#F8FAFC"),
        ),
    )
    return fig


def style_axes(fig, horizontal=False):
    """Dashed, faint gridlines on the value axis; clean category axis."""
    line_color = "rgba(148,163,184,0.35)"
    grid_color = "rgba(148,163,184,0.15)"

    if horizontal:
        fig.update_xaxes(
            showgrid=True,
            gridcolor=grid_color,
            griddash="dash",
            zeroline=False,
            linecolor=line_color,
        )
        fig.update_yaxes(
            showgrid=False,
            zeroline=False,
            linecolor=line_color,
        )
    else:
        fig.update_xaxes(
            showgrid=False,
            zeroline=False,
            linecolor=line_color,
        )
        fig.update_yaxes(
            showgrid=True,
            gridcolor=grid_color,
            griddash="dash",
            zeroline=False,
            linecolor=line_color,
        )
    return fig


# ==================================================
# DATABASE LOADING
# ==================================================
@st.cache_data(show_spinner=False)
def load_data(db_path, last_modified):
    """Load customer interactions from SQLite."""

    connection = sqlite3.connect(db_path, timeout=30)

    query = """
    SELECT
        i.interaction_id,
        i.interaction_date,
        sr.response_text AS survey_text,
        r.review_text,
        sm.message_text,
        p.product_name,
        ch.channel_name
    FROM interactions i
    LEFT JOIN survey_responses sr
        ON sr.response_id = i.survey_response_id
    LEFT JOIN reviews r
        ON r.review_id = i.review_id
    LEFT JOIN support_messages sm
        ON sm.message_id = i.support_message_id
    LEFT JOIN products p
        ON p.product_id = COALESCE(
            sr.product_id,
            r.product_id,
            sm.product_id
        )
    LEFT JOIN channels ch
        ON ch.channel_id = COALESCE(
            sr.channel_id,
            r.channel_id,
            sm.channel_id
        )
    """

    try:
        df = pd.read_sql_query(query, connection)
    finally:
        connection.close()

    # Combine the applicable feedback text.
    df["feedback_text"] = (
        df["survey_text"]
        .fillna(df["review_text"])
        .fillna(df["message_text"])
        .fillna("")
        .astype(str)
    )

    df["interaction_date"] = pd.to_datetime(
        df["interaction_date"],
        errors="coerce",
    )

    return df


# ==================================================
# MODEL LOADING
# ==================================================
@st.cache_resource
def load_models():
    """Load the trained sentiment and theme models."""

    sentiment_model = joblib.load(SENTIMENT_MODEL_PATH)
    theme_model = joblib.load(THEME_MODEL_PATH)

    return sentiment_model, theme_model


# ==================================================
# BATCH PREDICTIONS
# ==================================================
@st.cache_data(show_spinner=False)
def predict_batch(texts):
    """Predict sentiment and theme for multiple feedback records."""

    sentiment_model, theme_model = load_models()

    texts = list(texts)

    sentiments = sentiment_model.predict(texts)
    themes = theme_model.predict(texts)

    return list(sentiments), list(themes)


# ==================================================
# SINGLE FEEDBACK PREDICTION
# ==================================================
def predict_single_feedback(text):
    """Predict sentiment, theme and confidence estimates."""

    sentiment_model, theme_model = load_models()

    sentiment = sentiment_model.predict([text])[0]
    theme = theme_model.predict([text])[0]

    sentiment_confidence = None
    theme_confidence = None

    if hasattr(sentiment_model, "predict_proba"):
        sentiment_confidence = float(
            sentiment_model.predict_proba([text]).max()
        )

    if hasattr(theme_model, "predict_proba"):
        theme_confidence = float(
            theme_model.predict_proba([text]).max()
        )

    return (
        sentiment,
        theme,
        sentiment_confidence,
        theme_confidence,
    )


# ==================================================
# LOAD MODEL EVALUATION REPORT
# ==================================================
def load_evaluation_report():
    """Read the saved model evaluation report."""

    if not REPORT_PATH.exists():
        return None

    try:
        with open(REPORT_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return None


def display_model_metrics(report):
    """Display actual metrics from the evaluation report."""

    if not isinstance(report, dict):
        st.info(
            "No readable model evaluation report was found. "
            "Run the model training script to generate one."
        )
        return

    st.write(
        "The following metrics come from the saved "
        "synthetic-data evaluation report."
    )

    displayed = False

    model_columns = st.columns(2)

    for column, (model_key, display_name) in zip(
        model_columns,
        [
            ("sentiment", "Sentiment Model"),
            ("theme", "Theme Model"),
        ],
    ):
        section = report.get(model_key)

        # Support alternative report key names too.
        if not isinstance(section, dict):
            alternative_key = f"{model_key}_model"
            section = report.get(alternative_key)

        if not isinstance(section, dict):
            continue

        with column:

            st.markdown(f"### {display_name}")

            metrics_found = False

            accuracy = section.get("accuracy")

            if isinstance(accuracy, (int, float)):
                metric_card(
                    "target",
                    "Accuracy",
                    f"{accuracy:.2%}",
                    "From saved evaluation report",
                    "blue",
                )
                metrics_found = True
                displayed = True

            macro_f1 = (
                section.get("macro_f1")
                or section.get("macro_f1_score")
                or section.get("f1_macro")
            )

            if isinstance(macro_f1, (int, float)):
                metric_card(
                    "bars",
                    "Macro F1-score",
                    f"{macro_f1:.2%}",
                    "From saved evaluation report",
                    "violet",
                )
                metrics_found = True
                displayed = True

            if not metrics_found:
                st.caption(
                    "Accuracy and macro F1-score are not available "
                    "in this report section."
                )

    if not displayed:
        st.info(
            "The report does not contain recognized accuracy "
            "or macro F1-score values."
        )


# ==================================================
# HEADER / HERO
# ==================================================
st.markdown(
    """
<div class="cp-topbar">
<div class="cp-crumb">Dashboard <span>›</span> <b>Overview</b></div>
<div class="cp-badges">
<span class="cp-badge cp-badge-blue">✦ AI-Powered Prototype</span>
<span class="cp-badge cp-badge-amber">Synthetic Data</span>
</div>
</div>
<div class="cp-hero">
<div>
<div class="cp-eyebrow">📊 CustomerPulse AI · Customer Feedback Intelligence System</div>
<h1>Customer Intelligence Overview</h1>
<p>Analyze customer feedback, discover recurring themes, monitor sentiment, and generate predictions for new feedback.</p>
</div>
<div class="cp-hero-art">
<svg viewBox="0 0 220 80" width="220" height="80" fill="none"><defs><linearGradient id="cpg" x1="0" x2="1"><stop offset="0" stop-color="#22D3EE"/><stop offset="1" stop-color="#A78BFA"/></linearGradient></defs><polyline points="0,50 30,50 45,20 62,66 80,30 98,52 130,52 150,12 170,60 190,40 220,40" stroke="url(#cpg)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>
</div>
<div class="cp-disclaimer">Dataset: Synthetic customer feedback. Model evaluation on synthetic data does not guarantee performance on real-world feedback.</div>
</div>
""",
    unsafe_allow_html=True,
)


# ==================================================
# CHECK REQUIRED FILES
# ==================================================
missing_files = []

if not DB_PATH.exists():
    missing_files.append(f"Database: {DB_PATH}")

if not SENTIMENT_MODEL_PATH.exists():
    missing_files.append(
        f"Sentiment model: {SENTIMENT_MODEL_PATH}"
    )

if not THEME_MODEL_PATH.exists():
    missing_files.append(
        f"Theme model: {THEME_MODEL_PATH}"
    )

if missing_files:
    st.error("Some required files are missing:")

    for item in missing_files:
        st.write(f"- {item}")

    st.info(
        "Check the project paths and make sure the data "
        "generation and model training steps have completed."
    )

    st.stop()


# ==================================================
# LOAD DATA AND MODELS
# ==================================================
try:
    with st.spinner("Loading customer feedback data..."):
        df = load_data(
            str(DB_PATH),
            DB_PATH.stat().st_mtime,
        )

    sentiment_model, theme_model = load_models()

except Exception as error:
    st.error(f"Unable to load application resources: {error}")
    st.exception(error)
    st.stop()


if df.empty:
    st.warning("No interaction records were found in the database.")
    st.stop()


# ==================================================
# SIDEBAR: BRAND AND FILTERS
# ==================================================
st.sidebar.markdown(
    f"""
<div class="cp-side-brand">
<div class="cp-logo">{icon('bars')}</div>
<div>
<div class="cp-side-name">CustomerPulse AI</div>
<div class="cp-side-sub">Feedback Intelligence · Prototype</div>
</div>
</div>
<div class="cp-side-desc">Explore synthetic customer feedback, predicted sentiment and themes.</div>
<div class="cp-status"><span class="cp-dot"></span>Models loaded · Data ready</div>
<div class="cp-side-label">🔎 Dashboard Filters</div>
""",
    unsafe_allow_html=True,
)

products = sorted(
    df["product_name"].dropna().unique().tolist()
)

channels = sorted(
    df["channel_name"].dropna().unique().tolist()
)

selected_products = st.sidebar.multiselect(
    "Select products",
    options=products,
    default=products,
)

selected_channels = st.sidebar.multiselect(
    "Select channels",
    options=channels,
    default=channels,
)

filtered_df = df[
    df["product_name"].isin(selected_products)
    & df["channel_name"].isin(selected_channels)
].copy()

st.sidebar.markdown(
    '<div class="cp-side-stat">'
    f'Products selected: <b>{len(selected_products)}</b> of {len(products)}<br>'
    f'Channels selected: <b>{len(selected_channels)}</b> of {len(channels)}<br>'
    f'Showing <b>{len(filtered_df):,}</b> of {len(df):,} interactions'
    '</div>',
    unsafe_allow_html=True,
)


# ==================================================
# TABS
# ==================================================
overview_tab, explore_tab, predict_tab, about_tab = st.tabs(
    [
        "📈 Overview",
        "🔍 Explore Feedback",
        "🤖 Predict New Feedback",
        "ℹ️ About",
    ]
)


# ==================================================
# OVERVIEW TAB
# ==================================================
with overview_tab:

    section_header(
        "Overview",
        "Business Overview",
        "Key counts and model-predicted patterns for the "
        "currently selected products and channels.",
    )

    total_records = len(filtered_df)

    feedback_coverage = (
        filtered_df["feedback_text"]
        .str.strip()
        .ne("")
        .mean()
        * 100
        if total_records
        else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card(
            "chat",
            "Total Interactions",
            f"{total_records:,}",
            f"of {len(df):,} in database",
            "blue",
        )

    with col2:
        metric_card(
            "box",
            "Products",
            filtered_df["product_name"].nunique(),
            f"of {len(products)} available",
            "violet",
        )

    with col3:
        metric_card(
            "layers",
            "Channels",
            filtered_df["channel_name"].nunique(),
            f"of {len(channels)} available",
            "cyan",
        )

    with col4:
        metric_card(
            "check",
            "Feedback Coverage",
            f"{feedback_coverage:.1f}%",
            "records with feedback text",
            "green",
        )

    st.divider()

    if total_records == 0:

        st.warning("No records match your selected filters.")

    else:

        # Predict in batches instead of processing each row
        # separately. This is more efficient for large datasets.
        with st.spinner("Analyzing customer feedback..."):

            valid_mask = (
                filtered_df["feedback_text"]
                .str.strip()
                .ne("")
            )

            filtered_df["predicted_sentiment"] = "UNKNOWN"
            filtered_df["predicted_theme"] = "UNKNOWN"

            if valid_mask.any():

                valid_texts = (
                    filtered_df.loc[
                        valid_mask,
                        "feedback_text",
                    ]
                    .astype(str)
                    .tolist()
                )

                batch_sentiments, batch_themes = predict_batch(
                    tuple(valid_texts)
                )

                filtered_df.loc[
                    valid_mask,
                    "predicted_sentiment",
                ] = batch_sentiments

                filtered_df.loc[
                    valid_mask,
                    "predicted_theme",
                ] = batch_themes

        # Summaries used by the highlights row and the charts.
        sentiment_counts = (
            filtered_df["predicted_sentiment"]
            .value_counts()
            .rename_axis("Sentiment")
            .reset_index(name="Records")
        )

        theme_counts = (
            filtered_df["predicted_theme"]
            .value_counts()
            .rename_axis("Theme")
            .reset_index(name="Records")
        )

        date_counts = (
            filtered_df.dropna(
                subset=["interaction_date"]
            )
            .assign(
                Date=lambda frame: (
                    frame["interaction_date"].dt.date
                )
            )
            .groupby("Date")
            .size()
            .reset_index(name="Records")
        )

        # Prediction highlights (derived from the predictions above).
        sub_header(
            "Prediction highlights",
            "Derived from model predictions, not actual customer labels",
        )

        top_sentiment = sentiment_counts.iloc[0]
        top_theme = theme_counts.iloc[0]

        h1, h2, h3 = st.columns(3)

        with h1:
            metric_card(
                "smile",
                "Top Predicted Sentiment",
                top_sentiment["Sentiment"],
                f"{int(top_sentiment['Records']):,} records · "
                f"{top_sentiment['Records'] / total_records:.1%}",
                sentiment_tone(top_sentiment["Sentiment"]),
                small=True,
            )

        with h2:
            metric_card(
                "tag",
                "Top Predicted Theme",
                top_theme["Theme"],
                f"{int(top_theme['Records']):,} records · "
                f"{top_theme['Records'] / total_records:.1%}",
                "violet",
                small=True,
            )

        with h3:
            if not date_counts.empty:
                peak = date_counts.loc[date_counts["Records"].idxmax()]
                metric_card(
                    "calendar",
                    "Peak Volume Day",
                    str(peak["Date"]),
                    f"{int(peak['Records']):,} interactions",
                    "cyan",
                    small=True,
                )
            else:
                metric_card(
                    "calendar",
                    "Peak Volume Day",
                    "N/A",
                    "no valid dates",
                    "cyan",
                    small=True,
                )

        # Sentiment and theme charts.
        chart_height = max(
            400,
            min(640, 38 * len(theme_counts) + 150),
        )

        col1, col2 = st.columns(2)

        with col1:

            sentiment_colors = {
                label: sentiment_color(label)
                for label in sentiment_counts["Sentiment"]
            }

            fig = px.pie(
                sentiment_counts,
                names="Sentiment",
                values="Records",
                hole=0.55,
                color="Sentiment",
                color_discrete_map=sentiment_colors,
            )

            fig.update_traces(
                textinfo="percent",
                textfont=dict(color="#FFFFFF", size=13),
                marker=dict(line=dict(color="#1E1B4B", width=2)),
                hovertemplate=(
                    "%{label}<br>%{value:,} records "
                    "(%{percent})<extra></extra>"
                ),
            )

            fig.update_layout(
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.02,
                    xanchor="center",
                    x=0.5,
                    title_text="",
                ),
            )

            style_figure(
                fig,
                "Predicted Sentiment Distribution",
                "Model-Predicted Sentiment (not actual customer sentiment)",
                height=chart_height,
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        with col2:

            fig = px.bar(
                theme_counts,
                x="Records",
                y="Theme",
                orientation="h",
                color="Theme",
                color_discrete_sequence=THEME_PALETTE,
                labels={
                    "Theme": "Feedback Theme",
                    "Records": "Number of Interactions",
                },
            )

            fig.update_traces(
                hovertemplate=(
                    "%{y}<br>%{x:,} interactions<extra></extra>"
                ),
            )

            fig.update_layout(
                showlegend=False,
                bargap=0.3,
                yaxis=dict(categoryorder="total ascending"),
            )

            style_figure(
                fig,
                "Predicted Feedback Themes",
                "Model-Predicted Themes",
                height=chart_height,
            )
            style_axes(fig, horizontal=True)

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        # Feedback volume over time.
        if not date_counts.empty:

            fig = px.line(
                date_counts,
                x="Date",
                y="Records",
                markers=True,
                labels={
                    "Date": "Interaction Date",
                    "Records": "Number of Interactions",
                },
            )

            fig.update_traces(
                line=dict(color=COLOR_CYAN, width=2.5),
                marker=dict(size=5, color=COLOR_CYAN),
                fill="tozeroy",
                fillcolor="rgba(34,211,238,0.10)",
                hovertemplate=(
                    "%{x}<br>%{y:,} interactions<extra></extra>"
                ),
            )

            style_figure(
                fig,
                "Feedback Volume Over Time",
                "Customer Feedback Volume",
                height=370,
            )
            style_axes(fig)

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        else:
            st.info("No valid interaction dates are available.")


# ==================================================
# EXPLORE FEEDBACK TAB
# ==================================================
with explore_tab:

    section_header(
        "Workspace",
        "Explore Customer Feedback",
        "Search the feedback text of the interactions that match "
        "your sidebar filters.",
    )

    search_text = st.text_input(
        "Search feedback text",
        placeholder="Enter a word or phrase, e.g. delivery, refund, slow...",
        key="feedback_search",
        help="Case-insensitive search for the exact text you type.",
    )

    explore_df = filtered_df.copy()

    if search_text.strip():

        explore_df = explore_df[
            explore_df["feedback_text"].str.contains(
                search_text,
                case=False,
                regex=False,
                na=False,
            )
        ]

    st.markdown(
        f'<span class="cp-count">Matching records: '
        f'{len(explore_df):,}</span>',
        unsafe_allow_html=True,
    )

    if len(explore_df) == 0:
        st.info(
            "No feedback matches your search and filters. "
            "Try a different word or adjust the sidebar filters."
        )

    table_columns = [
        "interaction_id",
        "interaction_date",
        "product_name",
        "channel_name",
        "feedback_text",
    ]

    # Give the long feedback text a wider column when supported.
    column_settings = None

    if hasattr(st, "column_config"):
        column_settings = {
            "feedback_text": st.column_config.TextColumn(
                "feedback_text",
                width="large",
            ),
        }

    st.dataframe(
        explore_df[table_columns],
        use_container_width=True,
        hide_index=True,
        column_config=column_settings,
    )

    csv_data = explore_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="⬇️ Download filtered feedback as CSV",
        data=csv_data,
        file_name="customerpulse_feedback.csv",
        mime="text/csv",
    )


# ==================================================
# PREDICT NEW FEEDBACK TAB
# ==================================================
with predict_tab:

    section_header(
        "AI Workspace",
        "Analyze New Customer Feedback",
        "Paste a piece of customer feedback to see the trained "
        "models' predicted sentiment and theme.",
    )

    user_feedback = st.text_area(
        "Enter customer feedback",
        placeholder=(
            "Example: The delivery was late, "
            "and customer support did not respond."
        ),
        height=150,
        key="new_feedback",
    )

    if st.button(
        "Analyze Feedback",
        type="primary",
    ):

        cleaned_feedback = user_feedback.strip()

        if not cleaned_feedback:

            st.warning(
                "Please enter some feedback first."
            )

        else:

            try:

                with st.spinner("Analyzing feedback..."):
                    (
                        sentiment,
                        theme,
                        sentiment_confidence,
                        theme_confidence,
                    ) = predict_single_feedback(
                        cleaned_feedback
                    )

                col1, col2 = st.columns(2)

                with col1:
                    result_card(
                        "Predicted Sentiment",
                        sentiment,
                        sentiment_pill_class(sentiment),
                        sentiment_confidence,
                        "Sentiment Model Confidence",
                    )

                with col2:
                    result_card(
                        "Predicted Theme",
                        theme,
                        "cp-pill-theme",
                        theme_confidence,
                        "Theme Model Confidence",
                    )

                st.caption(
                    "Confidence scores are model probability "
                    "estimates, not guarantees that a prediction "
                    "is correct."
                )

                st.info(
                    "This prediction is generated by the trained "
                    "model. Review it before using it to make "
                    "business decisions."
                )

            except Exception as error:

                st.error(
                    f"Prediction failed: {error}"
                )


# ==================================================
# ABOUT TAB
# ==================================================
with about_tab:

    section_header(
        "About",
        "About CustomerPulse AI",
        "A customer feedback intelligence prototype designed to "
        "analyze sentiment and feedback themes.",
    )

    about_col1, about_col2 = st.columns(2)

    with about_col1:
        st.markdown(
            """
<div class="cp-card">
<h4>🧠 Machine Learning</h4>
<ul>
<li>TF-IDF text features</li>
<li>Logistic Regression</li>
<li>Sentiment classification</li>
<li>Theme classification</li>
</ul>
</div>
""",
            unsafe_allow_html=True,
        )

    with about_col2:
        st.markdown(
            """
<div class="cp-card">
<h4>🗂️ Dataset</h4>
<ul>
<li>70,000 synthetic customer interaction records</li>
<li>Survey responses, product reviews, and support messages</li>
</ul>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown(
        """
<div class="cp-card cp-card-warn">
<h4>⚠️ Important Limitations</h4>
<ul>
<li>The dataset contains synthetic, not genuine, feedback.</li>
<li>Synthetic-data metrics may not generalize to real customers.</li>
<li>Predictions should be reviewed before business decisions.</li>
<li>A predicted theme is the model's primary classification, not proof that the feedback contains only one theme.</li>
</ul>
</div>
""",
        unsafe_allow_html=True,
    )

    st.subheader("Model Evaluation")

    evaluation_report = load_evaluation_report()

    display_model_metrics(evaluation_report)

    st.caption(
        "Metrics are loaded from the saved model evaluation report. "
        "Retrain and reevaluate the models before applying them "
        "to different data."
    )

    st.markdown(
        """
<div class="cp-card">
<h4>🧰 Technology Stack</h4>
<span class="cp-chip">Python</span><span class="cp-chip">Streamlit</span><span class="cp-chip">SQLite</span><span class="cp-chip">Pandas</span><span class="cp-chip">scikit-learn</span><span class="cp-chip">Joblib</span><span class="cp-chip">Plotly</span>
</div>
""",
        unsafe_allow_html=True,
    )


# ==================================================
# FOOTER
# ==================================================
st.markdown(
    '<div class="cp-footer">CustomerPulse AI · AI-powered prototype · '
    'Synthetic data only · Review predictions before business decisions . '
    'Designed by VIGNESH ALAHARI'
    '</div>',
    unsafe_allow_html=True,
)

st.sidebar.divider()

st.sidebar.caption(
    "CustomerPulse AI | Prototype"
)

st.sidebar.caption(
    "Built with Python, SQLite, scikit-learn and Streamlit."
)
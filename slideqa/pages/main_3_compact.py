"""Main content preview — Variation 3: Score-first compact table-like layout"""
import streamlit as st

st.set_page_config(page_title="Main 3 — Score-first Compact", layout="wide")

st.markdown("""
<style>
.block-container { padding-top: 2rem !important; max-width: 960px; }
</style>
""", unsafe_allow_html=True)

st.caption("PREVIEW · Variation 3 of 3")
st.markdown("### Score-First Compact")
st.markdown("Pill metadata · left-border gold quote · baselines as a table with scores right-aligned")
st.divider()

QUESTION = "What new ideas were introduced from EE & ASR during the statistical revolution of the 1990s?"
GOLD = "HMMs, Gaussian mixture models, and discriminative training brought to NLP from speech recognition."
BASELINES = [
    ("ColPali RAG", "#6366f1", "4.2", "0.41", "HMMs, GMMs, and discriminative training transferred from speech recognition research."),
    ("Oracle VLM",  "#0d9488", "4.7", "0.53", "Statistical methods including HMMs and GMMs were introduced from EE and ASR communities."),
    ("Text BM25",   "#94a3b8", "2.1", "0.18", "N-gram language models and statistical methods were widely adopted in this period."),
    ("Closed-Book", "#cbd5e1", "1.9", "0.11", "New ideas included neural networks and deep learning architectures."),
]

st.selectbox("Select a question", [f"cs224n_q0001 — {QUESTION[:70]}…"], label_visibility="visible")

# Question
st.markdown(f"## {QUESTION}")

# Pill metadata
st.markdown("""
<div style="display:flex;gap:6px;margin-top:-6px;margin-bottom:16px;flex-wrap:wrap;font-family:system-ui;">
  <span style="background:#eef2ff;color:#6366f1;font-size:0.65rem;font-weight:700;
               padding:3px 10px;border-radius:20px;letter-spacing:0.04em;">TEXT ONLY</span>
  <span style="background:#f1f5f9;color:#64748b;font-size:0.65rem;font-weight:700;
               padding:3px 10px;border-radius:20px;letter-spacing:0.04em;">MEDIUM</span>
  <span style="background:#f1f5f9;color:#94a3b8;font-size:0.65rem;
               padding:3px 10px;border-radius:20px;">cs224n_q0001</span>
</div>
""", unsafe_allow_html=True)

st.divider()

# Gold + slide
col_gold, col_slide = st.columns([1, 2])
with col_gold:
    st.markdown("""<div style="font-size:0.65rem;font-weight:700;letter-spacing:0.09em;
                text-transform:uppercase;color:#94a3b8;margin-bottom:6px;font-family:system-ui;">
                Gold Answer</div>""", unsafe_allow_html=True)
    st.markdown(f"""<div style="padding-left:12px;border-left:3px solid #0d9488;
                font-size:0.88rem;color:#0f172a;line-height:1.6;font-family:system-ui;">
                {GOLD}</div>""", unsafe_allow_html=True)
    st.caption("lecture_01/slide_012.png")
with col_slide:
    st.markdown("""<div style="background:#f1f5f9;border-radius:8px;height:160px;
                display:flex;align-items:center;justify-content:center;
                color:#94a3b8;font-size:0.8rem;font-family:system-ui;">
                [ slide image ]</div>""", unsafe_allow_html=True)

st.divider()

# Table header
st.markdown("""
<div style="display:grid;grid-template-columns:160px 1fr 52px 52px;gap:8px;
            font-size:0.62rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;
            color:#94a3b8;padding:0 4px 8px;border-bottom:1px solid #e2e8f0;
            font-family:system-ui;">
  <span>Baseline</span>
  <span>Answer</span>
  <span style="text-align:right;">Judge</span>
  <span style="text-align:right;">F1</span>
</div>
""", unsafe_allow_html=True)

for name, color, judge, f1, answer in BASELINES:
    st.markdown(f"""
<div style="display:grid;grid-template-columns:160px 1fr 52px 52px;gap:8px;
            padding:11px 4px;border-bottom:1px solid #f1f5f9;
            align-items:start;font-family:system-ui;">
  <div style="font-size:0.75rem;font-weight:600;color:#0f172a;
              display:flex;align-items:center;gap:7px;padding-top:2px;">
    <span style="width:3px;height:14px;background:{color};border-radius:2px;
                 display:inline-block;flex-shrink:0;"></span>
    {name}
  </div>
  <div style="font-size:0.82rem;color:#475569;line-height:1.5;">{answer}</div>
  <div style="font-size:0.85rem;font-weight:700;color:{color};text-align:right;padding-top:2px;">{judge}</div>
  <div style="font-size:0.82rem;color:#94a3b8;text-align:right;padding-top:2px;">{f1}</div>
</div>
""", unsafe_allow_html=True)

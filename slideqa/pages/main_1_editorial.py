"""Main content preview — Variation 1: Clean editorial"""
import streamlit as st

st.set_page_config(page_title="Main 1 — Editorial", layout="wide")

st.markdown("""
<style>
.block-container { padding-top: 2rem !important; max-width: 960px; }
</style>
""", unsafe_allow_html=True)

st.caption("PREVIEW · Variation 1 of 3")
st.markdown("### Clean Editorial")
st.markdown("Metadata row above question · teal left-border gold answer · 2×2 grid baseline cards")
st.divider()

QUESTION = "What new ideas were introduced from EE & ASR during the statistical revolution of the 1990s?"
GOLD = "HMMs, Gaussian mixture models, and discriminative training brought to NLP from speech recognition."
BASELINES = [
    ("ColPali RAG", "4.2", "0.41", "HMMs, GMMs, and discriminative training transferred from speech recognition research."),
    ("Oracle VLM",  "4.7", "0.53", "Statistical methods including HMMs and GMMs were introduced from EE and ASR communities."),
    ("Text BM25",   "2.1", "0.18", "N-gram language models and statistical methods were widely adopted in this period."),
    ("Closed-Book", "1.9", "0.11", "New ideas included neural networks and deep learning architectures."),
]

# Question selector (mock)
st.selectbox("Select a question", [f"cs224n_q0001 — {QUESTION[:70]}…"], label_visibility="visible")

# Metadata + question
col_q, col_meta = st.columns([4, 1])
with col_q:
    st.markdown(f"## {QUESTION}")
with col_meta:
    st.markdown("""
<div style="display:flex;flex-direction:column;gap:6px;align-items:flex-end;padding-top:8px;font-family:system-ui;">
  <span style="font-size:0.68rem;font-weight:700;color:#6366f1;letter-spacing:0.06em;
               text-transform:uppercase;border:1px solid #c7d2fe;background:#eef2ff;
               padding:2px 9px;border-radius:4px;">Text Only</span>
  <span style="font-size:0.68rem;font-weight:700;color:#64748b;letter-spacing:0.06em;
               text-transform:uppercase;border:1px solid #e2e8f0;background:#f8fafc;
               padding:2px 9px;border-radius:4px;">medium</span>
  <span style="font-size:0.68rem;color:#cbd5e1;">cs224n_q0001</span>
</div>
""", unsafe_allow_html=True)

st.divider()

# Gold answer + slide
col_gold, col_slide = st.columns([1, 2])
with col_gold:
    st.markdown("""<div style="font-size:0.65rem;font-weight:700;letter-spacing:0.09em;
                text-transform:uppercase;color:#0d9488;margin-bottom:6px;font-family:system-ui;">
                Gold Answer</div>""", unsafe_allow_html=True)
    st.markdown(f"""<div style="border:1px solid #e2e8f0;border-left:3px solid #0d9488;
                border-radius:0 6px 6px 0;padding:12px 14px;font-size:0.88rem;
                color:#1e293b;line-height:1.6;background:#f8fffd;font-family:system-ui;">
                {GOLD}</div>""", unsafe_allow_html=True)
    st.caption("lecture_01/slide_012.png")
with col_slide:
    st.markdown("""<div style="background:#f1f5f9;border-radius:8px;height:160px;
                display:flex;align-items:center;justify-content:center;
                color:#94a3b8;font-size:0.8rem;font-family:system-ui;">
                [ slide image ]</div>""", unsafe_allow_html=True)

st.divider()

# Baseline cards — 2×2 grid
st.markdown("""<div style="font-size:0.65rem;font-weight:700;letter-spacing:0.09em;
            text-transform:uppercase;color:#6366f1;margin-bottom:12px;font-family:system-ui;">
            Baseline Answers</div>""", unsafe_allow_html=True)

row1 = st.columns(2, gap="medium")
row2 = st.columns(2, gap="medium")
for col, (name, judge, f1, answer) in zip(row1 + row2, BASELINES):
    with col:
        with st.container(border=True):
            st.markdown(f"**{name}**")
            st.caption(f"Judge {judge} / 5  ·  F1 {f1}")
            st.markdown(answer)

"""Main content preview — Variation 2: Full-width answer cards with left border strip"""
import streamlit as st

st.set_page_config(page_title="Main 2 — Full-width Cards", layout="wide")

st.markdown("""
<style>
.block-container { padding-top: 2rem !important; max-width: 960px; }
</style>
""", unsafe_allow_html=True)

st.caption("PREVIEW · Variation 2 of 3")
st.markdown("### Full-Width Answer Cards")
st.markdown("Inline metadata dots · teal-tinted gold answer · baselines stacked with colored left-border strip + right-aligned scores")
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

# Question + inline metadata
st.markdown(f"## {QUESTION}")
st.markdown("""
<div style="display:flex;gap:8px;align-items:center;margin-top:-8px;margin-bottom:8px;font-family:system-ui;">
  <span style="font-size:0.68rem;font-weight:700;color:#6366f1;letter-spacing:0.05em;text-transform:uppercase;">Text Only</span>
  <span style="color:#cbd5e1;">·</span>
  <span style="font-size:0.68rem;font-weight:700;color:#64748b;letter-spacing:0.05em;text-transform:uppercase;">medium</span>
  <span style="color:#cbd5e1;">·</span>
  <span style="font-size:0.68rem;color:#cbd5e1;">cs224n_q0001</span>
</div>
""", unsafe_allow_html=True)

st.divider()

# Gold answer full-width + slide
col_gold, col_slide = st.columns([1, 2])
with col_gold:
    st.markdown("""<div style="font-size:0.65rem;font-weight:700;letter-spacing:0.09em;
                text-transform:uppercase;color:#0d9488;margin-bottom:6px;font-family:system-ui;">
                Gold Answer · lecture_01/slide_012.png</div>""", unsafe_allow_html=True)
    st.markdown(f"""<div style="border:1px solid #ccfbf1;background:#f0fdf9;border-radius:6px;
                padding:12px 16px;font-size:0.88rem;color:#134e4a;
                line-height:1.6;font-family:system-ui;">{GOLD}</div>""", unsafe_allow_html=True)
with col_slide:
    st.markdown("""<div style="background:#f1f5f9;border-radius:8px;height:160px;
                display:flex;align-items:center;justify-content:center;
                color:#94a3b8;font-size:0.8rem;font-family:system-ui;">
                [ slide image ]</div>""", unsafe_allow_html=True)

st.divider()

st.markdown("""<div style="font-size:0.65rem;font-weight:700;letter-spacing:0.09em;
            text-transform:uppercase;color:#6366f1;margin-bottom:10px;font-family:system-ui;">
            Baselines</div>""", unsafe_allow_html=True)

for name, color, judge, f1, answer in BASELINES:
    st.markdown(f"""
<div style="display:flex;align-items:stretch;border:1px solid #e2e8f0;border-radius:6px;
            overflow:hidden;margin-bottom:8px;font-family:system-ui;">
  <div style="width:4px;background:{color};flex-shrink:0;"></div>
  <div style="padding:11px 14px;flex:1;display:flex;align-items:flex-start;gap:12px;">
    <div style="flex:1;">
      <div style="font-size:0.75rem;font-weight:600;color:#0f172a;margin-bottom:4px;">{name}</div>
      <div style="font-size:0.82rem;color:#475569;line-height:1.5;">{answer}</div>
    </div>
    <div style="text-align:right;flex-shrink:0;padding-top:2px;">
      <div style="font-size:0.82rem;font-weight:700;color:{color};">{judge}<span style="font-size:0.65rem;color:#94a3b8;font-weight:400;"> /5</span></div>
      <div style="font-size:0.72rem;color:#94a3b8;">F1 {f1}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

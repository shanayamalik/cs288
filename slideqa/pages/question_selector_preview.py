"""Question selector preview — Options A vs C side by side"""
import streamlit as st

st.set_page_config(page_title="Question Selector Preview", layout="wide")
st.markdown("""
<style>
.block-container { padding-top: 2rem !important; }
</style>
""", unsafe_allow_html=True)

st.caption("PREVIEW · Question Selector")
st.markdown("### How should questions be shown in the dropdown?")
st.divider()

QUESTIONS = [
    ("cs288_q0062", "Which option corresponds to the probability of a sentence under a bigram language model?"),
    ("cs288_q0041", "What is the purpose of Laplace smoothing in language models?"),
    ("cs288_q0017", "What does the term perplexity measure in the context of language models?"),
    ("cs288_q0008", "Which assumption does a unigram model make about word sequences?"),
    ("cs288_q0031", "How does beam search differ from greedy decoding in sequence generation?"),
]

col_a, col_c = st.columns(2)

with col_a:
    st.markdown(
        '<div style="font-size:0.65rem;font-weight:700;letter-spacing:0.09em;'
        'text-transform:uppercase;color:#6366f1;border-top:3px solid #6366f1;'
        'padding-top:10px;margin-bottom:12px;font-family:system-ui;">'
        'Option A — Short ID prefix</div>',
        unsafe_allow_html=True,
    )
    st.caption("Format:  [q0062]  Question text…")
    st.selectbox(
        "Select a question",
        range(len(QUESTIONS)),
        format_func=lambda i: (
            "[" + QUESTIONS[i][0].split("_")[1] + "]  "
            + QUESTIONS[i][1][:80]
            + ("..." if len(QUESTIONS[i][1]) > 80 else "")
        ),
        key="sel_a",
    )
    st.markdown(
        '<div style="margin-top:8px;padding:10px 14px;border:1px solid #e2e8f0;'
        'border-radius:6px;font-size:0.82rem;color:#475569;font-family:system-ui;">'
        'ID shortened to just the number so the question text gets more room. '
        'Still scannable at a glance.'
        '</div>',
        unsafe_allow_html=True,
    )

with col_c:
    st.markdown(
        '<div style="font-size:0.65rem;font-weight:700;letter-spacing:0.09em;'
        'text-transform:uppercase;color:#0d9488;border-top:3px solid #0d9488;'
        'padding-top:10px;margin-bottom:12px;font-family:system-ui;">'
        'Option C — Question text only</div>',
        unsafe_allow_html=True,
    )
    st.caption("Format:  Question text only — ID appears in metadata once selected")
    st.selectbox(
        "Select a question",
        range(len(QUESTIONS)),
        format_func=lambda i: (
            QUESTIONS[i][1][:95]
            + ("..." if len(QUESTIONS[i][1]) > 95 else "")
        ),
        key="sel_c",
    )
    st.markdown(
        '<div style="margin-top:8px;padding:10px 14px;border:1px solid #e2e8f0;'
        'border-radius:6px;font-size:0.82rem;color:#475569;font-family:system-ui;">'
        'Dropdown is purely about content. The ID still appears in the '
        'category/difficulty/id metadata line once a question is selected.'
        '</div>',
        unsafe_allow_html=True,
    )

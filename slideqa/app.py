"""SlideQA Demo — Streamlit app.

Browses pre-computed baseline predictions and shows slide images.
No GPU or API calls at runtime — all answers are cached from prior runs.

Run locally:
    streamlit run slideqa/app.py

Deploy on Streamlit Community Cloud:
    Point to this file as the entrypoint.
    Set SLIDE_BASE_URL in st.secrets if serving images from a remote URL,
    or leave unset to load images from the local slideqa/data/slides/ directory.
"""

import json
from pathlib import Path
from typing import Optional

import streamlit as st
from PIL import Image

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "slideqa" / "data"
ANNOTATIONS_DIR = DATA_DIR / "annotations"
RESULTS_DIR = DATA_DIR / "results"
SLIDES_DIR = DATA_DIR / "slides"

COURSES = {
    "CS 288 — Berkeley NLP": "cs288",
    "CS 601 — JHU Robotics": "cs601",
    "CS 224N — Stanford NLP": "cs224n",
}

BASELINES = {
    "ColPali RAG (our method)": "colpali_rag",
    "Text-Only BM25": "text_only",
    "Oracle VLM (upper bound)": "zero_shot_vlm",
    "Closed-Book (no context)": "closed_book",
}

CATEGORY_LABELS = {
    "text_only": "Text Only",
    "image_diagram": "Image / Diagram",
    "table": "Table",
    "chart_graph": "Chart / Graph",
    "layout_aware": "Layout Aware",
}

CATEGORY_COLORS = {
    "text_only": "#4A90D9",
    "image_diagram": "#E8A838",
    "table": "#5BAD6F",
    "chart_graph": "#C0544C",
    "layout_aware": "#9B6BB5",
}




# ---------------------------------------------------------------------------
# Data loading (cached so Streamlit doesn't reload on every interaction)
# ---------------------------------------------------------------------------
@st.cache_data
def load_qa(course: str) -> list[dict]:
    path = ANNOTATIONS_DIR / f"{course}_qa.json"
    with open(path) as f:
        return json.load(f)


@st.cache_data
def load_preds(course: str, baseline: str) -> dict:
    path = RESULTS_DIR / f"{course}_{baseline}_preds.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return {p["question_id"]: p for p in json.load(f)}


@st.cache_data
def load_judge_details(course: str, baseline: str) -> dict:
    path = RESULTS_DIR / f"{course}_{baseline}_judge_details.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return {q["question_id"]: q for q in json.load(f)}


@st.cache_data
def load_summary_csv() -> str:
    path = RESULTS_DIR / "all_courses_judge_summary.csv"
    return path.read_text() if path.exists() else ""


def get_slide_image(course: str, slide_id: str) -> Optional[Image.Image]:
    """Load a slide image from disk. slide_id is like 'lecture_04/slide_012.png'."""
    path = SLIDES_DIR / course / slide_id
    if path.exists():
        return Image.open(path)
    return None


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="SlideQA",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ── Main content ─────────────────────────────────────────────── */
.block-container { padding-top: 1.75rem !important; padding-bottom: 2rem !important; }

/* ── Sidebar background ───────────────────────────────────────── */
section[data-testid="stSidebar"] > div:first-child {
    background: #f8fafc;
    border-right: 1px solid #e2e8f0;
}
section[data-testid="stSidebar"] .block-container { padding-top: 2.5rem !important; }

/* Sidebar app name */
.sidebar-title {
    font-size: 1.05rem; font-weight: 800; letter-spacing: -0.02em;
    color: #0f172a; margin-bottom: 2px;
}
.sidebar-sub {
    font-size: 0.71rem; color: #64748b; margin-top: 0; margin-bottom: 1rem;
}

/* Sidebar section labels — border-top acts as card accent */
.sidebar-label-indigo {
    font-size: 0.62rem; font-weight: 700; letter-spacing: 0.09em;
    text-transform: uppercase; color: #6366f1;
    border-top: 3px solid #6366f1;
    padding-top: 10px; margin-top: 4px; margin-bottom: 0;
}
.sidebar-label-teal {
    font-size: 0.62rem; font-weight: 700; letter-spacing: 0.09em;
    text-transform: uppercase; color: #0d9488;
    border-top: 3px solid #0d9488;
    padding-top: 10px; margin-top: 4px; margin-bottom: 0;
}

/* Count chip */
.sidebar-chip {
    display: inline-block; background: #6366f1; color: #fff;
    font-size: 0.76rem; font-weight: 700; padding: 2px 10px;
    border-radius: 20px; margin-right: 6px;
}

/* Sidebar selectbox: smaller text, white bg */
section[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background: #fff !important;
    border-color: #e2e8f0 !important;
    font-size: 0.78rem !important;
    min-height: 2rem !important;
}
section[data-testid="stSidebar"] [data-testid="stSelectbox"] span {
    font-size: 0.78rem !important;
}
/* Sidebar widget labels */
section[data-testid="stSidebar"] label[data-testid="stWidgetLabel"] p {
    font-size: 0.68rem !important; color: #94a3b8 !important;
    font-weight: 500 !important;
}
/* Sidebar caption / small text */
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    font-size: 0.68rem !important;
}

/* ── Tabs ─────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 1px solid #e2e8f0;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    font-size: 0.8rem; font-weight: 600; letter-spacing: 0.05em;
    text-transform: uppercase; padding: 0.6rem 1.25rem;
    border-radius: 0; color: #94a3b8;
    border-bottom: 2px solid transparent;
}
.stTabs [aria-selected="true"] {
    color: #6366f1 !important;
    border-bottom: 2px solid #6366f1 !important;
    background: transparent !important;
}

/* ── Misc ─────────────────────────────────────────────────────── */
hr { border-color: #f1f5f9 !important; margin: 0.8rem 0 !important; }
[data-testid="stDataFrame"] > div { border-radius: 6px; overflow: hidden; }
.streamlit-expander { border: 1px solid #e2e8f0 !important; border-radius: 6px !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar — course + filter controls
# ---------------------------------------------------------------------------
st.sidebar.markdown(
    '<p class="sidebar-title">SlideQA</p>'
    '<p class="sidebar-sub">Multimodal QA benchmark</p>',
    unsafe_allow_html=True,
)

st.sidebar.markdown('<p class="sidebar-label-indigo">Course</p>', unsafe_allow_html=True)
course_label = st.sidebar.selectbox("Course", list(COURSES.keys()), label_visibility="collapsed")
course = COURSES[course_label]

st.sidebar.markdown('<p class="sidebar-label-teal">Filter</p>', unsafe_allow_html=True)
CATEGORY_ICONS = {
    "All":           "·· All categories",
    "text_only":     "¶  Text Only",
    "image_diagram": "◈  Image / Diagram",
    "table":         "⊞  Table",
    "chart_graph":   "↗  Chart / Graph",
    "layout_aware":  "⊟  Layout Aware",
}
DIFFICULTY_ICONS = {
    "All":    "·· All",
    "easy":   "○  Easy",
    "medium": "◑  Medium",
    "hard":   "●  Hard",
}
filter_category = st.sidebar.selectbox(
    "Category",
    ["All"] + list(CATEGORY_LABELS.keys()),
    format_func=lambda x: CATEGORY_ICONS.get(x, x),
)
filter_difficulty = st.sidebar.selectbox(
    "Difficulty", ["All", "easy", "medium", "hard"],
    format_func=lambda x: DIFFICULTY_ICONS.get(x, x),
)

# ---------------------------------------------------------------------------
# Load data for selected course
# ---------------------------------------------------------------------------
qa_list = load_qa(course)

# Apply filters
filtered = qa_list
if filter_category != "All":
    filtered = [q for q in filtered if q.get("category") == filter_category]
if filter_difficulty != "All":
    filtered = [q for q in filtered if q.get("difficulty") == filter_difficulty]

st.sidebar.markdown(
    f'<span class="sidebar-chip">{len(filtered)}</span>'
    f'<span style="font-size:0.72rem;color:#64748b;">of {len(qa_list)} questions</span>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Main content — tabs
# ---------------------------------------------------------------------------
tab_browse, tab_compare, tab_leaderboard = st.tabs(
    ["Browse Questions", "Compare Baselines", "Leaderboard"]
)

# ==========================================================================
# TAB 1: Browse individual questions
# ==========================================================================
with tab_browse:
    if not filtered:
        st.warning("No questions match the selected filters.")
    else:
        # Question selector
        q_labels = [
            f"{q['question_id']} — {q['question'][:70]}{'…' if len(q['question']) > 70 else ''}"
            for q in filtered
        ]
        selected_idx = st.selectbox(
            "Select a question",
            range(len(filtered)),
            format_func=lambda i: q_labels[i],
        )
        qa = filtered[selected_idx]
        qid = qa["question_id"]

        # Question metadata strip
        cat = qa.get("category", "unknown")
        diff = qa.get("difficulty", "unknown")
        cat_color = CATEGORY_COLORS.get(cat, "#888")
        cat_label = CATEGORY_LABELS.get(cat, cat)

        col_q, col_meta = st.columns([4, 1])
        with col_q:
            st.markdown(f"### {qa['question']}")
        with col_meta:
            st.markdown(
                f"<span style='display:inline-block;border:1px solid #cbd5e1;"
                f"color:#475569;padding:2px 8px;border-radius:4px;"
                f"font-size:0.78rem;font-weight:500;letter-spacing:0.03em'>{cat_label}</span>"
                f"&nbsp;"
                f"<span style='display:inline-block;border:1px solid #cbd5e1;"
                f"color:#475569;padding:2px 8px;border-radius:4px;"
                f"font-size:0.78rem;font-weight:500;letter-spacing:0.03em'>{diff}</span>",
                unsafe_allow_html=True,
            )
            st.caption(qid)

        st.markdown("---")

        # Gold answer + evidence slide
        col_gold, col_slide = st.columns([1, 2])
        with col_gold:
            st.markdown("**Gold Answer**")
            with st.container(border=True):
                st.markdown(qa["answer"])

            evidence = qa.get("evidence_slides", [])
            if evidence:
                st.caption(f"Evidence: {evidence[0]}")

        with col_slide:
            evidence = qa.get("evidence_slides", [])
            if evidence:
                img = get_slide_image(course, evidence[0])
                if img:
                    st.markdown("**Evidence Slide**")
                    st.image(img, use_container_width=True)
                else:
                    st.caption(f"Slide image not available locally: {evidence[0]}")

        st.markdown("---")

        # Baseline answers
        st.markdown("**Baseline Answers**")

        baseline_cols = st.columns(len(BASELINES))
        for col, (bl_label, bl_key) in zip(baseline_cols, BASELINES.items()):
            preds = load_preds(course, bl_key)
            judge = load_judge_details(course, bl_key)

            pred = preds.get(qid, {})
            judge_entry = judge.get(qid, {})
            scores = judge_entry.get("scores", {})

            answer = pred.get("predicted_answer", "_No prediction cached_")
            judge_score = scores.get("llm_judge")
            f1 = scores.get("token_f1")

            with col:
                with st.container(border=True):
                    st.markdown(f"**{bl_label}**")
                    if judge_score is not None:
                        st.caption(f"Judge {judge_score:.1f} / 5  ·  F1 {f1:.2f}")
                    st.markdown(answer)

                    # Show retrieved slides for ColPali RAG
                    if bl_key == "colpali_rag":
                        retrieved = pred.get("retrieved_slides", [])
                        if retrieved:
                            with st.expander("Retrieved slides"):
                                for i, slide_id in enumerate(retrieved[:5]):
                                    img = get_slide_image(course, slide_id)
                                    is_gold = slide_id in (qa.get("evidence_slides") or [])
                                    label = f"#{i+1} · {slide_id}" + (" · gold" if is_gold else "")
                                    st.caption(label)
                                    if img:
                                        st.image(img, use_container_width=True)
                                    else:
                                        st.caption("Image not available locally")
                                    if i < 4:
                                        st.markdown("---")

# ==========================================================================
# TAB 2: Compare baselines across all questions
# ==========================================================================
with tab_compare:
    st.markdown("### Per-Category Performance")
    st.caption("Macro-averaged from cached evaluation runs. Judge score = GPT-4o rating on a 1–5 scale.")

    # Build a summary table from judge_details for the current course
    import pandas as pd

    rows = []
    for bl_label, bl_key in BASELINES.items():
        judge_details = load_judge_details(course, bl_key)
        if not judge_details:
            continue
        for cat_key, cat_label in CATEGORY_LABELS.items():
            entries = [v for v in judge_details.values() if v.get("category") == cat_key]
            if not entries:
                continue
            f1_vals = [e["scores"]["token_f1"] for e in entries if "scores" in e]
            j_vals = [e["scores"]["llm_judge"] for e in entries if "scores" in e]
            rows.append(
                {
                    "Baseline": bl_label,
                    "Category": cat_label,
                    "N": len(entries),
                    "Token F1": round(sum(f1_vals) / len(f1_vals), 3) if f1_vals else 0,
                    "Judge (1–5)": round(sum(j_vals) / len(j_vals), 2) if j_vals else 0,
                }
            )

    if rows:
        df = pd.DataFrame(rows)

        # Pivot for judge scores
        pivot_judge = df.pivot(index="Category", columns="Baseline", values="Judge (1–5)")
        pivot_f1 = df.pivot(index="Category", columns="Baseline", values="Token F1")

        col_j, col_f = st.columns(2)
        with col_j:
            st.caption("LM-as-Judge Score (1–5)")
            st.dataframe(pivot_judge, use_container_width=True)
        with col_f:
            st.caption("Token F1")
            st.dataframe(pivot_f1, use_container_width=True)

    # Recall@k table
    recall_path = RESULTS_DIR / "colpali_rag_recall_at_k.csv"
    if recall_path.exists():
        st.markdown("---")
        st.markdown("### ColPali RAG — Recall@k")
        st.caption("Fraction of questions where the gold slide is in the top-k retrieved results.")
        recall_df = pd.read_csv(recall_path)
        course_recall = recall_df[recall_df["course"] == course].copy()
        if not course_recall.empty:
            course_recall = course_recall.drop(columns=["course"])
            course_recall = course_recall.set_index("category")
            st.dataframe(course_recall, use_container_width=True)

# ==========================================================================
# TAB 3: Leaderboard (all 3 courses)
# ==========================================================================
with tab_leaderboard:
    st.markdown("### Overall Results")
    st.caption("Macro-averaged over all 150 questions per course.")

    summary_rows = []
    for course_label_lb, course_key in COURSES.items():
        for bl_label, bl_key in BASELINES.items():
            judge_details = load_judge_details(course_key, bl_key)
            if not judge_details:
                continue
            all_entries = list(judge_details.values())
            f1_vals = [e["scores"]["token_f1"] for e in all_entries if "scores" in e]
            j_vals = [e["scores"]["llm_judge"] for e in all_entries if "scores" in e]
            em_vals = [e["scores"]["exact_match"] for e in all_entries if "scores" in e]
            summary_rows.append(
                {
                    "Course": course_label_lb.split("—")[0].strip(),
                    "Baseline": bl_label,
                    "EM": round(sum(em_vals) / len(em_vals), 3) if em_vals else 0,
                    "Token F1": round(sum(f1_vals) / len(f1_vals), 3) if f1_vals else 0,
                    "Judge (1–5)": round(sum(j_vals) / len(j_vals), 2) if j_vals else 0,
                    "N": len(all_entries),
                }
            )

    if summary_rows:
        import pandas as pd
        lb_df = pd.DataFrame(summary_rows)
        lb_pivot = lb_df.pivot_table(
            index="Baseline", columns="Course", values="Judge (1–5)"
        )
        st.caption("LM-as-Judge Score by Course")
        st.dataframe(lb_pivot, use_container_width=True)

        st.caption("Full Results")
        st.dataframe(
            lb_df.sort_values(["Course", "Judge (1–5)"], ascending=[True, False]),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")
    st.markdown("### ColPali RAG — Recall@k")
    recall_path = RESULTS_DIR / "colpali_rag_recall_at_k.csv"
    if recall_path.exists():
        import pandas as pd
        recall_df = pd.read_csv(recall_path)
        overall_recall = recall_df[recall_df["category"] == "OVERALL"].copy()
        overall_recall = overall_recall.drop(columns=["category", "n"]).set_index("course")
        st.dataframe(overall_recall, use_container_width=True)

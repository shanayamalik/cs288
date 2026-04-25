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
import random
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

BASELINE_COLORS = {
    "colpali_rag":  "#6366f1",
    "zero_shot_vlm": "#0d9488",
    "text_only":    "#94a3b8",
    "closed_book":  "#cbd5e1",
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
.block-container { padding-top: 3rem !important; padding-bottom: 2rem !important; }

/* ── Sidebar background ───────────────────────────────────────── */
section[data-testid="stSidebar"] > div:first-child {
    background: #f8fafc;
    border-right: 1px solid #e2e8f0;
}
section[data-testid="stSidebar"] .block-container { padding-top: 2.5rem !important; }

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

/* ── Buttons — minimal ghost style ───────────────────────────── */
.stButton > button {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    color: #475569;
    font-size: 1.25rem;
    font-weight: 400;
    padding: 0.3rem 0.6rem;
    transition: border-color 0.15s, color 0.15s, background 0.15s;
}
.stButton > button:hover {
    border-color: #6366f1;
    color: #6366f1;
    background: #f5f3ff;
}
.stButton > button:active {
    background: #ede9fe;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar — course + filter controls
# ---------------------------------------------------------------------------
st.sidebar.markdown(
    '<p style="font-size:1.25rem;font-weight:800;letter-spacing:-0.03em;'
    'color:#0f172a;margin:0 0 2px 0;line-height:1.2;">'
    '<span style="color:#6366f1;">Slide</span>QA</p>'
    '<p style="font-size:0.72rem;color:#64748b;margin:0 0 4px 0;">'
    'Multimodal QA over lecture slides &nbsp;·&nbsp; CS 288</p>'
    '<p style="font-size:0.68rem;color:#db2777;margin:0 0 1rem 0;">'
    'Nathan McNaughton &nbsp;·&nbsp; Shanaya Malik &nbsp;·&nbsp; Nicholas Eliacin</p>',
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
    "easy":   "▮      Easy",
    "medium": "▮▮    Medium",
    "hard":   "▮▮▮  Hard",
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
        # Question selector — init / clamp session state index
        if "q_idx" not in st.session_state:
            st.session_state["q_idx"] = 0
        st.session_state["q_idx"] = min(st.session_state["q_idx"], len(filtered) - 1)

        # Navigation row: dropdown | ‹ | › | 🔀
        nav_dd, nav_l, nav_r, nav_rand = st.columns([10, 1, 1, 2])
        with nav_dd:
            selected_idx = st.selectbox(
                "Select a question",
                range(len(filtered)),
                index=st.session_state["q_idx"],
                format_func=lambda i: (
                    filtered[i]["question"][:95]
                    + ("..." if len(filtered[i]["question"]) > 95 else "")
                ),
                label_visibility="collapsed",
            )
            st.session_state["q_idx"] = selected_idx
        with nav_l:
            if st.button("❮", width="stretch", key="nav_prev"):
                st.session_state["q_idx"] = (st.session_state["q_idx"] - 1) % len(filtered)
        with nav_r:
            if st.button("❯", width="stretch", key="nav_next"):
                st.session_state["q_idx"] = (st.session_state["q_idx"] + 1) % len(filtered)
        with nav_rand:
            if st.button("Shuffle", width="stretch", key="nav_rand"):
                st.session_state["q_idx"] = random.randrange(len(filtered))

        qa = filtered[selected_idx]
        qid = qa["question_id"]

        # Question + inline metadata (Main 2 style: dots below title)
        cat = qa.get("category", "unknown")
        diff = qa.get("difficulty", "unknown")
        cat_label = CATEGORY_LABELS.get(cat, cat)

        st.markdown(f"### {qa['question']}")
        st.markdown(
            f'<div style="display:flex;gap:8px;align-items:center;margin-top:-8px;'
            f'margin-bottom:8px;font-family:system-ui;">'
            f'<span style="font-size:0.68rem;font-weight:700;color:#6366f1;'
            f'letter-spacing:0.05em;text-transform:uppercase;">{cat_label}</span>'
            f'<span style="color:#cbd5e1;">·</span>'
            f'<span style="font-size:0.68rem;font-weight:700;color:#64748b;'
            f'letter-spacing:0.05em;text-transform:uppercase;">{diff}</span>'
            f'<span style="color:#cbd5e1;">·</span>'
            f'<span style="font-size:0.68rem;color:#cbd5e1;">{qid}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.divider()

        # Gold answer + evidence slide (Main 3 style: left-border teal, no box)
        evidence = qa.get("evidence_slides", [])
        col_gold, col_slide = st.columns([1, 2])
        with col_gold:
            st.markdown(
                '<div style="font-size:0.65rem;font-weight:700;letter-spacing:0.09em;'
                'text-transform:uppercase;color:#94a3b8;margin-bottom:6px;font-family:system-ui;">'
                'Gold Answer</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="padding-left:12px;border-left:3px solid #0d9488;'
                f'font-size:0.88rem;color:#0f172a;line-height:1.6;font-family:system-ui;">'
                f'{qa["answer"]}</div>',
                unsafe_allow_html=True,
            )
            if evidence:
                st.caption(evidence[0])

        with col_slide:
            if evidence:
                img = get_slide_image(course, evidence[0])
                if img:
                    st.image(img, use_container_width=True)
                else:
                    st.caption(f"Slide image not available locally: {evidence[0]}")

        st.divider()

        # Baseline answers — stacked cards (Main 2 left strip + Main 3 Judge/F1 columns)
        st.markdown(
            '<div style="display:grid;grid-template-columns:190px 1fr 56px 46px;gap:8px;'
            'font-size:0.62rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;'
            'color:#94a3b8;padding:0 4px 8px;border-bottom:1px solid #e2e8f0;'
            'font-family:system-ui;">'
            '<span>Baseline</span><span>Answer</span>'
            '<span style="text-align:right;">Judge</span>'
            '<span style="text-align:right;">F1</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        colpali_pred = None
        for bl_label, bl_key in BASELINES.items():
            preds = load_preds(course, bl_key)
            judge_details_bl = load_judge_details(course, bl_key)

            pred = preds.get(qid, {})
            judge_entry = judge_details_bl.get(qid, {})
            scores = judge_entry.get("scores", {})

            answer = pred.get("predicted_answer", "No prediction cached")
            judge_score = scores.get("llm_judge")
            f1 = scores.get("token_f1")
            color = BASELINE_COLORS.get(bl_key, "#94a3b8")

            judge_str = f"{judge_score:.1f}" if judge_score is not None else "—"
            f1_str = f"{f1:.2f}" if f1 is not None else "—"

            st.markdown(
                f'<div style="display:grid;grid-template-columns:190px 1fr 56px 46px;gap:8px;'
                f'padding:11px 4px;border-bottom:1px solid #f1f5f9;'
                f'align-items:start;font-family:system-ui;">'
                f'<div style="font-size:0.75rem;font-weight:600;color:#0f172a;'
                f'display:flex;align-items:center;gap:7px;padding-top:2px;">'
                f'<span style="width:3px;height:14px;background:{color};border-radius:2px;'
                f'display:inline-block;flex-shrink:0;"></span>{bl_label}</div>'
                f'<div style="font-size:0.82rem;color:#475569;line-height:1.5;">{answer}</div>'
                f'<div style="font-size:0.85rem;font-weight:700;color:{color};'
                f'text-align:right;padding-top:2px;">{judge_str}</div>'
                f'<div style="font-size:0.82rem;color:#94a3b8;'
                f'text-align:right;padding-top:2px;">{f1_str}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            if bl_key == "colpali_rag":
                colpali_pred = pred

        if colpali_pred:
            retrieved = colpali_pred.get("retrieved_slides", [])
            if retrieved:
                with st.expander("View ColPali RAG retrieved slides"):
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
    st.caption("Macro-averaged scores across all questions for the selected course. Judge = GPT-4o rating on a 1–5 scale.")

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

        # Shorten baseline labels for pivot column headers
        SHORT_LABELS = {
            "ColPali RAG (our method)": "ColPali RAG",
            "Text-Only BM25":           "Text BM25",
            "Oracle VLM (upper bound)": "Oracle VLM",
            "Closed-Book (no context)": "Closed-Book",
        }
        df["Baseline"] = df["Baseline"].map(lambda x: SHORT_LABELS.get(x, x))

        pivot_judge = df.pivot(index="Category", columns="Baseline", values="Judge (1–5)")
        pivot_f1    = df.pivot(index="Category", columns="Baseline", values="Token F1")
        pivot_judge.columns.name = None
        pivot_f1.columns.name    = None

        # Build column_config with progress bars so values are visually encoded
        judge_col_cfg = {
            col: st.column_config.ProgressColumn(
                col, min_value=0, max_value=5, format="%.2f"
            )
            for col in pivot_judge.columns
        }
        f1_col_cfg = {
            col: st.column_config.ProgressColumn(
                col, min_value=0, max_value=1, format="%.2f"
            )
            for col in pivot_f1.columns
        }

        col_j, col_f = st.columns(2)
        with col_j:
            st.markdown(
                '<div style="font-size:0.65rem;font-weight:700;letter-spacing:0.09em;'
                'text-transform:uppercase;color:#6366f1;margin-bottom:6px;font-family:system-ui;">'
                'LM-as-Judge Score (1–5)</div>',
                unsafe_allow_html=True,
            )
            st.dataframe(pivot_judge, use_container_width=True, column_config=judge_col_cfg)
        with col_f:
            st.markdown(
                '<div style="font-size:0.65rem;font-weight:700;letter-spacing:0.09em;'
                'text-transform:uppercase;color:#0d9488;margin-bottom:6px;font-family:system-ui;">'
                'Token F1</div>',
                unsafe_allow_html=True,
            )
            st.dataframe(pivot_f1, use_container_width=True, column_config=f1_col_cfg)

    # Recall@k table
    recall_path = RESULTS_DIR / "colpali_rag_recall_at_k.csv"
    if recall_path.exists():
        st.divider()
        st.markdown(
            '<div style="font-size:0.65rem;font-weight:700;letter-spacing:0.09em;'
            'text-transform:uppercase;color:#94a3b8;margin-bottom:6px;font-family:system-ui;">'
            'ColPali RAG — Recall@k</div>',
            unsafe_allow_html=True,
        )
        st.caption("Fraction of questions where the gold slide is in the top-k retrieved results.")
        recall_df = pd.read_csv(recall_path)
        course_recall = recall_df[recall_df["course"] == course].copy()
        if not course_recall.empty:
            k_cols = [c for c in course_recall.columns if c not in ("course", "category", "n")]
            recall_col_cfg = {
                c: st.column_config.ProgressColumn(c, min_value=0, max_value=1, format="%.2f")
                for c in k_cols
            }
            course_recall = course_recall.drop(columns=["course"])
            course_recall = course_recall.set_index("category")
            st.dataframe(course_recall, use_container_width=True, column_config=recall_col_cfg)

# ==========================================================================
# TAB 3: Leaderboard (all 3 courses)
# ==========================================================================
with tab_leaderboard:
    st.markdown("### Overall Results")
    st.caption("Macro-averaged judge score and token F1 across all questions per course.")

    # Build per-course, per-baseline summary
    lb_data: dict = {}  # {course_short: {bl_label: (judge, f1)}}
    for course_label_lb, course_key in COURSES.items():
        course_short = course_label_lb.split("—")[0].strip()
        lb_data[course_short] = {}
        for bl_label, bl_key in BASELINES.items():
            judge_details_lb = load_judge_details(course_key, bl_key)
            if not judge_details_lb:
                continue
            entries = list(judge_details_lb.values())
            f1_vals = [e["scores"]["token_f1"] for e in entries if "scores" in e]
            j_vals  = [e["scores"]["llm_judge"]  for e in entries if "scores" in e]
            short_label = {
                "ColPali RAG (our method)": "ColPali RAG",
                "Text-Only BM25":           "Text BM25",
                "Oracle VLM (upper bound)": "Oracle VLM",
                "Closed-Book (no context)": "Closed-Book",
            }.get(bl_label, bl_label)
            lb_data[course_short][short_label] = (
                round(sum(j_vals)  / len(j_vals),  2) if j_vals  else 0,
                round(sum(f1_vals) / len(f1_vals), 3) if f1_vals else 0,
            )

    BASELINE_COLOR_MAP = {
        "ColPali RAG": "#6366f1",
        "Oracle VLM":  "#0d9488",
        "Text BM25":   "#94a3b8",
        "Closed-Book": "#cbd5e1",
    }

    if lb_data:
        course_cols = st.columns(len(lb_data))
        for col, (course_short, bl_scores) in zip(course_cols, lb_data.items()):
            with col:
                st.markdown(
                    f'<div style="font-size:0.65rem;font-weight:700;letter-spacing:0.09em;'
                    f'text-transform:uppercase;color:#6366f1;border-top:3px solid #6366f1;'
                    f'padding-top:10px;margin-bottom:12px;font-family:system-ui;">'
                    f'{course_short}</div>',
                    unsafe_allow_html=True,
                )
                ranked = sorted(bl_scores.items(), key=lambda x: x[1][0], reverse=True)
                for rank, (bl, (judge, f1)) in enumerate(ranked, 1):
                    color = BASELINE_COLOR_MAP.get(bl, "#94a3b8")
                    bar_pct = int(judge / 5 * 100)
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:10px;'
                        f'padding:9px 0;border-bottom:1px solid #f1f5f9;font-family:system-ui;">'
                        f'<span style="font-size:0.7rem;font-weight:700;color:#94a3b8;width:14px;">#{rank}</span>'
                        f'<span style="width:3px;height:28px;background:{color};border-radius:2px;flex-shrink:0;"></span>'
                        f'<div style="flex:1;">'
                        f'<div style="font-size:0.75rem;font-weight:600;color:#0f172a;">{bl}</div>'
                        f'<div style="height:4px;background:#f1f5f9;border-radius:2px;margin-top:4px;">'
                        f'<div style="width:{bar_pct}%;height:4px;background:{color};border-radius:2px;"></div>'
                        f'</div></div>'
                        f'<div style="text-align:right;flex-shrink:0;">'
                        f'<div style="font-size:0.82rem;font-weight:700;color:{color};">{judge:.1f}</div>'
                        f'<div style="font-size:0.68rem;color:#94a3b8;">F1 {f1:.2f}</div>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )

    # Recall@k
    recall_path = RESULTS_DIR / "colpali_rag_recall_at_k.csv"
    if recall_path.exists():
        st.divider()
        st.markdown(
            '<div style="font-size:0.65rem;font-weight:700;letter-spacing:0.09em;'
            'text-transform:uppercase;color:#94a3b8;margin-bottom:6px;font-family:system-ui;">'
            'ColPali RAG — Recall@k (overall)</div>',
            unsafe_allow_html=True,
        )
        recall_df = pd.read_csv(recall_path)
        overall_recall = recall_df[recall_df["category"] == "OVERALL"].copy()
        if not overall_recall.empty:
            k_cols = [c for c in overall_recall.columns if c not in ("course", "category", "n")]
            recall_col_cfg = {
                c: st.column_config.ProgressColumn(c, min_value=0, max_value=1, format="%.2f")
                for c in k_cols
            }
            overall_recall = overall_recall.drop(columns=["category", "n"]).set_index("course")
            st.dataframe(overall_recall, use_container_width=True, column_config=recall_col_cfg)

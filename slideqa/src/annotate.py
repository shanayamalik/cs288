#!/usr/bin/env python3
"""Step 4B: Streamlit-based human review and annotation tool.

Usage:
    streamlit run annotate.py -- --course cs288
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# ──────────────────────────────────────────────
# Data helpers
# ──────────────────────────────────────────────

def load_drafts(course: str) -> list[dict]:
    path = DATA_DIR / "annotations" / f"{course}_qa_drafts.json"
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def load_approved(course: str) -> list[dict]:
    path = DATA_DIR / "annotations" / f"{course}_qa.json"
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def save_approved(course: str, approved: list[dict]) -> None:
    path = DATA_DIR / "annotations" / f"{course}_qa.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(approved, f, indent=2)


def save_drafts_back(course: str, drafts: list[dict]) -> None:
    path = DATA_DIR / "annotations" / f"{course}_qa_drafts.json"
    with open(path, "w") as f:
        json.dump(drafts, f, indent=2)


def get_slide_image_path(course: str, evidence_slide: str) -> Path:
    return DATA_DIR / "slides" / course / evidence_slide


# ──────────────────────────────────────────────
# Streamlit App
# ──────────────────────────────────────────────

def run_app(course: str):
    try:
        import streamlit as st
    except ImportError:
        print("Install streamlit: pip install streamlit")
        sys.exit(1)

    st.set_page_config(page_title=f"SlideQA Annotator — {course}", layout="wide")
    st.title(f"SlideQA Annotation Tool — {course.upper()}")

    # Load data into session state
    if "drafts" not in st.session_state:
        st.session_state.drafts = load_drafts(course)
    if "approved" not in st.session_state:
        st.session_state.approved = load_approved(course)

    drafts = st.session_state.drafts

    # Filter to slides that have QA pairs (not empty)
    slides_with_qa = [d for d in drafts if d.get("qa_pairs")]

    if not slides_with_qa:
        st.warning("No draft QA pairs found. Run generate_qa.py first.")
        return

    # ── Sidebar: progress + navigation ──
    total_pairs = sum(len(d["qa_pairs"]) for d in slides_with_qa)
    reviewed = sum(
        1
        for d in slides_with_qa
        for qa in d["qa_pairs"]
        if qa.get("status") in ("approved", "rejected")
    )
    st.sidebar.metric("Total QA Pairs", total_pairs)
    st.sidebar.metric("Reviewed", f"{reviewed}/{total_pairs}")
    st.sidebar.progress(reviewed / total_pairs if total_pairs > 0 else 0)

    # Filter by status
    status_filter = st.sidebar.selectbox("Filter by status", ["all", "draft", "approved", "rejected"])

    # Slide selector
    slide_labels = [d["evidence_slide"] for d in slides_with_qa]
    selected_slide = st.sidebar.selectbox("Select slide", slide_labels)

    slide_data = next(d for d in slides_with_qa if d["evidence_slide"] == selected_slide)

    # ── Main area ──
    col_img, col_qa = st.columns([1, 1])

    with col_img:
        img_path = get_slide_image_path(course, selected_slide)
        if img_path.exists():
            st.image(str(img_path), use_container_width=True)
        else:
            st.error(f"Image not found: {img_path}")

    with col_qa:
        for idx, qa in enumerate(slide_data["qa_pairs"]):
            current_status = qa.get("status", "draft")

            if status_filter != "all" and current_status != status_filter:
                continue

            st.markdown(f"---\n**QA #{idx + 1}** — Status: `{current_status}`")

            # Editable fields
            qa["question"] = st.text_area(
                f"Question #{idx + 1}", value=qa.get("question", ""), key=f"q_{selected_slide}_{idx}"
            )
            qa["answer"] = st.text_area(
                f"Answer #{idx + 1}", value=qa.get("answer", ""), key=f"a_{selected_slide}_{idx}"
            )
            qa["category"] = st.selectbox(
                f"Category #{idx + 1}",
                ["text_only", "image_diagram", "table", "chart_graph", "layout_aware"],
                index=["text_only", "image_diagram", "table", "chart_graph", "layout_aware"].index(
                    qa.get("category", "text_only")
                ),
                key=f"c_{selected_slide}_{idx}",
            )
            qa["difficulty"] = st.selectbox(
                f"Difficulty #{idx + 1}",
                ["easy", "medium", "hard"],
                index=["easy", "medium", "hard"].index(qa.get("difficulty", "medium")),
                key=f"d_{selected_slide}_{idx}",
            )

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button(f"✅ Approve #{idx + 1}", key=f"approve_{selected_slide}_{idx}"):
                    qa["status"] = "approved"
                    qa["annotator"] = "human_verified"
                    # Add to approved list
                    approved_entry = {
                        "question_id": qa.get("question_id", f"{course}_q_manual"),
                        "question": qa["question"],
                        "answer": qa["answer"],
                        "category": qa["category"],
                        "evidence_slides": [selected_slide],
                        "course": course,
                        "difficulty": qa["difficulty"],
                        "requires_multi_slide": False,
                        "metadata": {
                            "annotator": "human_verified",
                            "question_type": "single",
                        },
                    }
                    st.session_state.approved.append(approved_entry)
                    save_approved(course, st.session_state.approved)
                    save_drafts_back(course, drafts)
                    st.success("Approved and saved!")
            with btn_col2:
                if st.button(f"❌ Reject #{idx + 1}", key=f"reject_{selected_slide}_{idx}"):
                    qa["status"] = "rejected"
                    save_drafts_back(course, drafts)
                    st.info("Rejected.")

        # ── Add new QA pair manually ──
        st.markdown("---")
        st.subheader("Add new QA pair")
        new_q = st.text_area("New question", key=f"new_q_{selected_slide}")
        new_a = st.text_area("New answer", key=f"new_a_{selected_slide}")
        new_cat = st.selectbox(
            "Category",
            ["text_only", "image_diagram", "table", "chart_graph", "layout_aware"],
            key=f"new_cat_{selected_slide}",
        )
        new_diff = st.selectbox("Difficulty", ["easy", "medium", "hard"], key=f"new_diff_{selected_slide}")
        if st.button("➕ Add & Approve", key=f"add_{selected_slide}"):
            if new_q.strip() and new_a.strip():
                new_entry = {
                    "question_id": f"{course}_q_manual_{len(st.session_state.approved) + 1:04d}",
                    "question": new_q.strip(),
                    "answer": new_a.strip(),
                    "category": new_cat,
                    "evidence_slides": [selected_slide],
                    "course": course,
                    "difficulty": new_diff,
                    "requires_multi_slide": False,
                    "metadata": {"annotator": "human"},
                }
                st.session_state.approved.append(new_entry)
                save_approved(course, st.session_state.approved)
                st.success("New QA pair added!")


if __name__ == "__main__":
    # Parse --course from streamlit args (after --)
    parser = argparse.ArgumentParser()
    parser.add_argument("--course", default="cs288")
    # Streamlit passes its own args; isolate ours
    try:
        idx = sys.argv.index("--")
        args = parser.parse_args(sys.argv[idx + 1 :])
    except ValueError:
        args = parser.parse_args([])
    run_app(args.course)

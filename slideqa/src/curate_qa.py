#!/usr/bin/env python3
"""Auto-curate QA drafts into a quality-filtered subset for the benchmark.

Applies heuristic filters to remove low-quality pairs, then samples a balanced
subset across categories, difficulties, and lectures.

Usage:
    python curate_qa.py --course cs288
    python curate_qa.py --course cs288 --target 100
"""

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

CATEGORIES = ["text_only", "image_diagram", "table", "chart_graph", "layout_aware"]

# ──────────────────────────────────────────────
# Quality filters
# ──────────────────────────────────────────────

def is_trivial(qa: dict) -> bool:
    """Reject trivially shallow questions."""
    q = qa["question"].lower()
    trivial_patterns = [
        "what is the title",
        "what is the course",
        "what time does",
        "what date",
        "what is the email",
        "what is the url",
        "what is the website",
        "what is the name of the file",
    ]
    return any(p in q for p in trivial_patterns)


def is_too_short(qa: dict, min_answer_len: int = 2) -> bool:
    """Reject answers that are too terse to be meaningful."""
    return len(qa["answer"].strip()) < min_answer_len


def is_too_long_answer(qa: dict, max_words: int = 10) -> bool:
    """Reject answers that are too long for EM/F1 evaluation."""
    return len(qa["answer"].split()) > max_words


def is_too_vague(qa: dict) -> bool:
    """Reject vague questions about slide layout that aren't really testing comprehension."""
    q = qa["question"].lower()
    vague_patterns = [
        "how does the layout",
        "how is the slide organized",
        "what does the layout suggest",
        "how are the elements arranged",
    ]
    return any(p in q for p in vague_patterns)


def is_self_referential(qa: dict) -> bool:
    """Reject questions that reference 'this slide' without real content."""
    q = qa["question"].lower()
    if q.startswith("what is shown on this slide") or q.startswith("what is the main topic of this slide"):
        return True
    return False


def passes_quality(qa: dict) -> bool:
    """Return True if the QA pair passes all quality filters."""
    if is_trivial(qa):
        return False
    if is_too_short(qa):
        return False
    if is_too_long_answer(qa):
        return False
    if is_too_vague(qa):
        return False
    if is_self_referential(qa):
        return False
    return True


# ──────────────────────────────────────────────
# Balanced sampling
# ──────────────────────────────────────────────

def balanced_sample(qa_pool: list[dict], target: int, seed: int = 42) -> list[dict]:
    """Sample a balanced subset across categories and difficulties.

    Strategy:
    - Allocate minimum slots per category to ensure coverage
    - Within each category, prefer medium/hard over easy
    - Spread across lectures
    """
    rng = random.Random(seed)

    # Group by category
    by_cat = defaultdict(list)
    for q in qa_pool:
        by_cat[q["category"]].append(q)

    # Minimum allocation: ensure every category with data gets at least 10% of target
    min_per_cat = max(5, target // 10)

    # First pass: allocate minimums
    selected = []
    leftover = []
    for cat in CATEGORIES:
        pool = by_cat.get(cat, [])
        # Sort: hard first, then medium, then easy
        priority = {"hard": 0, "medium": 1, "easy": 2}
        pool.sort(key=lambda q: priority.get(q["difficulty"], 1))
        # Shuffle within same difficulty for lecture spread
        rng.shuffle(pool)
        pool.sort(key=lambda q: priority.get(q["difficulty"], 1))

        take = min(len(pool), min_per_cat)
        selected.extend(pool[:take])
        leftover.extend(pool[take:])

    # Second pass: fill remaining slots from leftover, preferring multimodal
    remaining = target - len(selected)
    if remaining > 0:
        priority = {"hard": 0, "medium": 1, "easy": 2}
        # Prefer non-text_only in leftover
        multimodal_left = [q for q in leftover if q["category"] != "text_only"]
        text_left = [q for q in leftover if q["category"] == "text_only"]
        rng.shuffle(multimodal_left)
        multimodal_left.sort(key=lambda q: priority.get(q["difficulty"], 1))
        rng.shuffle(text_left)
        text_left.sort(key=lambda q: priority.get(q["difficulty"], 1))

        for pool in [multimodal_left, text_left]:
            take = min(len(pool), remaining)
            selected.extend(pool[:take])
            remaining -= take
            if remaining <= 0:
                break

    return selected[:target]


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def curate(course: str, target: int = 100) -> None:
    # Find the drafts file
    candidates = sorted(DATA_DIR.glob(f"annotations/{course}_qa_drafts_*.json"))
    if not candidates:
        drafts_path = DATA_DIR / "annotations" / f"{course}_qa_drafts.json"
    else:
        drafts_path = candidates[0]

    if not drafts_path.exists():
        raise FileNotFoundError(f"No drafts found at {drafts_path}")

    with open(drafts_path) as f:
        slides = json.load(f)

    # Flatten all QA pairs with slide context
    all_qa = []
    for slide in slides:
        for qa in slide.get("qa_pairs", []):
            qa["evidence_slide"] = slide["evidence_slide"]
            qa["course"] = slide.get("course", course)
            # Extract lecture from path
            qa["lecture"] = slide["evidence_slide"].split("/")[0]
            all_qa.append(qa)

    print(f"Total QA pairs: {len(all_qa)}")

    # Apply quality filters
    passed = [q for q in all_qa if passes_quality(q)]
    rejected = len(all_qa) - len(passed)
    print(f"After quality filtering: {len(passed)} kept, {rejected} removed")

    # Show what was filtered
    filter_reasons = defaultdict(int)
    for q in all_qa:
        if not passes_quality(q):
            if is_trivial(q):
                filter_reasons["trivial"] += 1
            elif is_too_short(q):
                filter_reasons["too_short"] += 1
            elif is_too_long_answer(q):
                filter_reasons["too_long_answer"] += 1
            elif is_too_vague(q):
                filter_reasons["too_vague"] += 1
            elif is_self_referential(q):
                filter_reasons["self_referential"] += 1
    print(f"  Filter reasons: {dict(filter_reasons)}")

    # Balanced sample
    selected = balanced_sample(passed, target)
    print(f"\nSelected {len(selected)} QA pairs:")

    # Stats
    cat_counts = defaultdict(int)
    diff_counts = defaultdict(int)
    lec_counts = defaultdict(int)
    for q in selected:
        cat_counts[q["category"]] += 1
        diff_counts[q["difficulty"]] += 1
        lec_counts[q["lecture"]] += 1

    print("\n  By category:")
    for c in CATEGORIES:
        print(f"    {c}: {cat_counts.get(c, 0)}")

    print("\n  By difficulty:")
    for d in ["easy", "medium", "hard"]:
        print(f"    {d}: {diff_counts.get(d, 0)}")

    print("\n  By lecture:")
    for l in sorted(lec_counts):
        print(f"    {l}: {lec_counts[l]}")

    # Format for the final benchmark
    benchmark = []
    for i, q in enumerate(selected, 1):
        benchmark.append({
            "question_id": f"{course}_q{i:04d}",
            "question": q["question"],
            "answer": q["answer"],
            "category": q["category"],
            "difficulty": q["difficulty"],
            "evidence_slides": [q["evidence_slide"]],
            "course": course,
            "lecture": q["lecture"],
            "requires_multi_slide": False,
            "metadata": {
                "annotator": q.get("annotator", "llm_gpt-4o"),
                "curation": "auto_filtered",
            },
        })

    # Save
    out_path = DATA_DIR / "annotations" / f"{course}_qa.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(benchmark, f, indent=2)
    print(f"\nSaved to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Auto-curate QA drafts into a quality benchmark subset")
    parser.add_argument("--course", required=True, help="Course identifier")
    parser.add_argument("--target", type=int, default=100, help="Target number of QA pairs (default: 100)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()
    curate(args.course, target=args.target)


if __name__ == "__main__":
    main()

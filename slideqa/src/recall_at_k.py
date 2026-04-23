#!/usr/bin/env python3
"""Compute Recall@k for the ColPali RAG baseline.

Loads the saved colpali_rag predictions (which include retrieved_slides top-5)
and computes Recall@k for k=1,2,3,5, both overall and per category.
No API calls needed — works entirely off cached prediction files.

Usage:
    python slideqa/src/recall_at_k.py
    python slideqa/src/recall_at_k.py --course cs288
"""

import argparse
import csv
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
ANNOTATIONS_DIR = DATA_DIR / "annotations"

COURSES = ["cs288", "cs601", "cs224n"]
KS = [1, 2, 3, 5]
CATEGORIES = ["text_only", "image_diagram", "table", "chart_graph", "layout_aware"]


def recall_at_k(gold_slides: list[str], retrieved: list[str], k: int) -> int:
    """Return 1 if any gold slide is in the top-k retrieved, else 0."""
    return int(bool(set(gold_slides) & set(retrieved[:k])))


def compute_recall(course: str) -> dict:
    """Compute Recall@k for one course. Returns nested dict."""
    qa_path = ANNOTATIONS_DIR / f"{course}_qa.json"
    preds_path = RESULTS_DIR / f"{course}_colpali_rag_preds.json"

    if not preds_path.exists():
        logger.warning(f"No colpali_rag predictions found for {course}: {preds_path}")
        return {}

    with open(qa_path) as f:
        qa_list = json.load(f)
    with open(preds_path) as f:
        preds_list = json.load(f)

    qa_by_id = {q["question_id"]: q for q in qa_list}
    preds_by_id = {p["question_id"]: p for p in preds_list}

    # Collect per-question hits for each k
    results = {k: {"overall": [], "per_category": {cat: [] for cat in CATEGORIES}} for k in KS}

    for qid, qa in qa_by_id.items():
        gold = qa.get("evidence_slides", [])
        if not gold:
            continue
        pred = preds_by_id.get(qid, {})
        retrieved = pred.get("retrieved_slides", [])
        cat = qa.get("category", "unknown")

        for k in KS:
            hit = recall_at_k(gold, retrieved, k)
            results[k]["overall"].append(hit)
            if cat in results[k]["per_category"]:
                results[k]["per_category"][cat].append(hit)

    # Aggregate
    summary = {}
    for k in KS:
        overall = results[k]["overall"]
        summary[k] = {
            "overall": round(sum(overall) / len(overall), 4) if overall else 0.0,
            "overall_hits": sum(overall),
            "overall_total": len(overall),
            "per_category": {},
        }
        for cat in CATEGORIES:
            hits = results[k]["per_category"][cat]
            summary[k]["per_category"][cat] = {
                "recall": round(sum(hits) / len(hits), 4) if hits else 0.0,
                "hits": sum(hits),
                "total": len(hits),
            }

    return summary


def print_recall_table(all_results: dict) -> None:
    """Print Recall@k table: rows=course, cols=k."""
    print(f"\n{'=' * 70}")
    print("  ColPali RAG — Recall@k (fraction with gold slide in top-k)")
    print(f"{'=' * 70}")
    header = f"{'Course':<10}" + "".join(f"  {'R@'+str(k):>8}" for k in KS)
    print(header)
    print("-" * len(header))
    for course, summary in all_results.items():
        if not summary:
            continue
        line = f"{course:<10}" + "".join(
            f"  {summary[k]['overall']:>8.3f}" for k in KS
        )
        print(line)
    print("=" * 70)

    # Per-category for each course
    for course, summary in all_results.items():
        if not summary:
            continue
        print(f"\n  {course} — per category:")
        cat_header = f"  {'Category':<16}" + "".join(f"  {'R@'+str(k):>8}" for k in KS)
        print(cat_header)
        print("  " + "-" * (len(cat_header) - 2))
        for cat in CATEGORIES:
            cat_data = summary[KS[0]]["per_category"].get(cat)
            if not cat_data or cat_data["total"] == 0:
                continue
            n = cat_data["total"]
            line = f"  {cat:<16}" + "".join(
                f"  {summary[k]['per_category'][cat]['recall']:>8.3f}" for k in KS
            )
            print(f"{line}  (n={n})")


def save_recall_csv(all_results: dict) -> None:
    """Save Recall@k to CSV."""
    path = RESULTS_DIR / "colpali_rag_recall_at_k.csv"
    rows = []
    header = ["course", "category"] + [f"recall_at_{k}" for k in KS] + ["n"]

    for course, summary in all_results.items():
        if not summary:
            continue
        # Overall row
        rows.append(
            [course, "OVERALL"]
            + [f"{summary[k]['overall']:.4f}" for k in KS]
            + [str(summary[KS[0]]["overall_total"])]
        )
        # Per-category rows
        for cat in CATEGORIES:
            cat_data = summary[KS[0]]["per_category"].get(cat, {})
            n = cat_data.get("total", 0)
            if n == 0:
                continue
            rows.append(
                [course, cat]
                + [f"{summary[k]['per_category'][cat]['recall']:.4f}" for k in KS]
                + [str(n)]
            )

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    logger.info(f"Saved Recall@k to {path}")


def main():
    parser = argparse.ArgumentParser(description="Compute Recall@k for ColPali RAG")
    parser.add_argument("--course", choices=COURSES, default=None)
    args = parser.parse_args()

    courses = [args.course] if args.course else COURSES
    all_results = {}
    for course in courses:
        logger.info(f"Computing Recall@k for {course} ...")
        all_results[course] = compute_recall(course)

    print_recall_table(all_results)
    save_recall_csv(all_results)
    logger.info("Done!")


if __name__ == "__main__":
    main()

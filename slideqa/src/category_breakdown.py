#!/usr/bin/env python3
"""Produce a per-category performance breakdown across all courses and baselines.

Reads existing *_all_results.json files (no API calls, no re-evaluation).
Outputs:
  - Console table per course
  - slideqa/data/results/all_courses_category_breakdown.csv  (one row per course+category)
  - slideqa/data/results/category_avg_breakdown.csv          (macro-averaged across courses)

Usage:
    python slideqa/src/category_breakdown.py
    python slideqa/src/category_breakdown.py --baselines text_only zero_shot_vlm
"""

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "data" / "results"

COURSES = ["cs288", "cs601", "cs224n"]
COURSE_LABELS = {"cs288": "CS 288 (Berkeley)", "cs601": "CS 601 (JHU)", "cs224n": "CS 224N (Stanford)"}
CATEGORIES = ["text_only", "image_diagram", "table", "chart_graph", "layout_aware"]
CAT_SHORT = {"text_only": "TO", "image_diagram": "ID", "table": "TB", "chart_graph": "CG", "layout_aware": "LA"}
DEFAULT_BASELINES = ["text_only", "zero_shot_vlm"]
BASELINE_LABELS = {
    "text_only": "Text-Only",
    "zero_shot_vlm": "Oracle VLM",
    "closed_book": "Closed-Book",
    "colpali_rag": "ColPali RAG",
}
METRICS = ["exact_match", "token_f1"]
METRIC_LABELS = {"exact_match": "EM", "token_f1": "F1"}


def load_results(course: str, baselines: list[str]) -> dict:
    """Load per-category results for a course from all_results.json."""
    path = RESULTS_DIR / f"{course}_all_results.json"
    if not path.exists():
        print(f"[WARN] Results not found for {course}: {path}", file=sys.stderr)
        return {}
    with open(path) as f:
        data = json.load(f)
    # Only keep requested baselines that exist
    return {bl: data[bl] for bl in baselines if bl in data}


def print_course_table(course: str, results: dict) -> None:
    """Print a per-category breakdown table for one course."""
    baselines = list(results.keys())
    if not baselines:
        return

    col_w = 10
    label = COURSE_LABELS.get(course, course)
    print(f"\n{'=' * 70}")
    print(f"  {label}")
    print(f"{'=' * 70}")

    # Header
    header = f"{'Category':<14} {'N':>4}"
    for bl in baselines:
        bl_label = BASELINE_LABELS.get(bl, bl)
        for m in METRICS:
            header += f"  {(bl_label[:6] + '_' + METRIC_LABELS[m]):>{col_w}}"
    print(header)
    print("-" * len(header))

    # Per-category rows
    for cat in CATEGORIES:
        n = 0
        for bl in baselines:
            cat_data = results[bl]["per_category"].get(cat, {})
            if cat_data.get("count", 0) > 0:
                n = cat_data["count"]
                break
        if n == 0:
            continue
        short = CAT_SHORT.get(cat, cat)
        line = f"{cat:<14} {n:>4}"
        for bl in baselines:
            cat_data = results[bl]["per_category"].get(cat, {})
            for m in METRICS:
                line += f"  {cat_data.get(m, 0.0):>{col_w}.4f}"
        print(line)

    # Overall row
    print("-" * len(header))
    n_overall = results[baselines[0]]["overall"]["count"]
    line = f"{'OVERALL':<14} {n_overall:>4}"
    for bl in baselines:
        for m in METRICS:
            line += f"  {results[bl]['overall'].get(m, 0.0):>{col_w}.4f}"
    print(line)
    print("=" * len(header))


def save_combined_csv(all_results: dict, baselines: list[str], path: Path) -> None:
    """Save one row per (course, category) with metrics for all baselines."""
    path.parent.mkdir(parents=True, exist_ok=True)

    header = ["course", "category", "n"]
    for bl in baselines:
        for m in METRICS:
            header.append(f"{bl}_{m}")

    rows = []
    for course in COURSES:
        results = all_results.get(course, {})
        if not results:
            continue

        for cat in CATEGORIES:
            n = 0
            for bl in baselines:
                cat_data = results.get(bl, {}).get("per_category", {}).get(cat, {})
                if cat_data.get("count", 0) > 0:
                    n = cat_data["count"]
                    break
            if n == 0:
                continue
            row = [course, cat, str(n)]
            for bl in baselines:
                cat_data = results.get(bl, {}).get("per_category", {}).get(cat, {})
                for m in METRICS:
                    row.append(f"{cat_data.get(m, 0.0):.4f}")
            rows.append(row)

        # Overall row per course
        n_overall = results.get(baselines[0], {}).get("overall", {}).get("count", 0)
        row = [course, "OVERALL", str(n_overall)]
        for bl in baselines:
            for m in METRICS:
                row.append(f"{results.get(bl, {}).get('overall', {}).get(m, 0.0):.4f}")
        rows.append(row)

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"\nSaved combined breakdown to {path}")


def save_avg_csv(all_results: dict, baselines: list[str], path: Path) -> None:
    """Save macro-averaged per-category metrics across all courses."""
    path.parent.mkdir(parents=True, exist_ok=True)

    header = ["category", "total_n"]
    for bl in baselines:
        for m in METRICS:
            header.append(f"{bl}_{m}_avg")

    rows = []
    for cat in CATEGORIES:
        total_n = 0
        sums = {bl: {m: 0.0 for m in METRICS} for bl in baselines}
        n_courses = 0

        for course in COURSES:
            results = all_results.get(course, {})
            if not results:
                continue
            n = 0
            for bl in baselines:
                cat_data = results.get(bl, {}).get("per_category", {}).get(cat, {})
                if cat_data.get("count", 0) > 0:
                    n = cat_data["count"]
                    break
            if n == 0:
                continue
            total_n += n
            n_courses += 1
            for bl in baselines:
                cat_data = results.get(bl, {}).get("per_category", {}).get(cat, {})
                for m in METRICS:
                    sums[bl][m] += cat_data.get(m, 0.0)

        if n_courses == 0:
            continue
        row = [cat, str(total_n)]
        for bl in baselines:
            for m in METRICS:
                row.append(f"{sums[bl][m] / n_courses:.4f}")
        rows.append(row)

    # Macro-avg overall
    overall_n = sum(
        all_results.get(c, {}).get(baselines[0], {}).get("overall", {}).get("count", 0)
        for c in COURSES
    )
    sums = {bl: {m: 0.0 for m in METRICS} for bl in baselines}
    n_courses = 0
    for course in COURSES:
        results = all_results.get(course, {})
        if not results:
            continue
        n_courses += 1
        for bl in baselines:
            for m in METRICS:
                sums[bl][m] += results.get(bl, {}).get("overall", {}).get(m, 0.0)
    row = ["OVERALL (macro-avg)", str(overall_n)]
    for bl in baselines:
        for m in METRICS:
            row.append(f"{sums[bl][m] / max(n_courses, 1):.4f}")
    rows.append(row)

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"Saved macro-avg breakdown to {path}")


def main():
    parser = argparse.ArgumentParser(description="Per-category performance breakdown across all courses")
    parser.add_argument(
        "--baselines",
        nargs="+",
        default=DEFAULT_BASELINES,
        choices=["text_only", "zero_shot_vlm", "closed_book", "colpali_rag"],
        help="Which baselines to include (default: text_only zero_shot_vlm)",
    )
    args = parser.parse_args()

    # Load results for all courses
    all_results = {}
    for course in COURSES:
        results = load_results(course, args.baselines)
        if results:
            all_results[course] = results

    if not all_results:
        print("No results found. Run run_baselines.py first.", file=sys.stderr)
        sys.exit(1)

    # Print per-course tables
    for course in COURSES:
        if course in all_results:
            print_course_table(course, all_results[course])

    # Save CSVs
    save_combined_csv(
        all_results,
        args.baselines,
        RESULTS_DIR / "all_courses_category_breakdown.csv",
    )
    save_avg_csv(
        all_results,
        args.baselines,
        RESULTS_DIR / "category_avg_breakdown.csv",
    )


if __name__ == "__main__":
    main()

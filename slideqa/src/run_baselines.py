#!/usr/bin/env python3
"""Run all baselines on the curated SlideQA dataset and produce results.

Runs:
  1. Text-only baseline (BM25 retrieval + LLM, no vision)
  2. Zero-shot VLM baseline (oracle slide + VLM)
  3. Evaluates both with EM, Token-F1, and LLM-as-Judge
  4. Outputs summary table + per-question details

Usage:
    python run_baselines.py --course cs288
    python run_baselines.py --course cs288 --skip-judge    # faster, no LLM judge
    python run_baselines.py --course cs288 --only text_only
"""

import argparse
import csv
import json
import logging
import os
import sys
import time
from pathlib import Path

# Add parent to path so imports work
sys.path.insert(0, str(Path(__file__).resolve().parent))

from baselines.text_only import run_text_only_baseline
from baselines.zero_shot_vlm import run_zero_shot_vlm_baseline
from evaluate import evaluate, print_results_table

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"

CATEGORIES = ["text_only", "image_diagram", "table", "chart_graph", "layout_aware"]


def save_predictions(preds: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(preds, f, indent=2)
    logger.info(f"Saved {len(preds)} predictions to {path}")


def save_summary_csv(all_results: dict, path: Path) -> None:
    """Save a combined summary CSV with both baselines side by side."""
    path.parent.mkdir(parents=True, exist_ok=True)

    # Determine metric columns from first baseline
    first_baseline = next(iter(all_results.values()))
    metrics = [k for k in first_baseline["summary"]["overall"] if k != "count"]
    baselines = list(all_results.keys())

    # Build header
    header = ["category", "n"]
    for bl in baselines:
        for m in metrics:
            header.append(f"{bl}_{m}")

    rows = []
    # Per-category rows
    for cat in CATEGORIES:
        row = [cat]
        # Use count from first baseline that has this category
        n = 0
        for bl in baselines:
            cat_data = all_results[bl]["summary"]["per_category"].get(cat, {})
            if cat_data.get("count", 0) > 0:
                n = cat_data["count"]
                break
        row.append(str(n))
        for bl in baselines:
            cat_data = all_results[bl]["summary"]["per_category"].get(cat, {})
            for m in metrics:
                row.append(f"{cat_data.get(m, 0):.4f}")
        rows.append(row)

    # Overall row
    row = ["OVERALL"]
    overall_n = all_results[baselines[0]]["summary"]["overall"]["count"]
    row.append(str(overall_n))
    for bl in baselines:
        for m in metrics:
            row.append(f"{all_results[bl]['summary']['overall'].get(m, 0):.4f}")
    rows.append(row)

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    logger.info(f"Saved summary CSV to {path}")


def print_combined_table(all_results: dict) -> None:
    """Print a combined results table for all baselines."""
    baselines = list(all_results.keys())
    first = all_results[baselines[0]]
    metrics = [k for k in first["summary"]["overall"] if k != "count"]

    # Header
    col_w = 12
    header = f"{'Category':<18} {'N':>4}"
    for bl in baselines:
        for m in metrics:
            label = f"{bl[:8]}_{m[:4]}"
            header += f"  {label:>{col_w}}"
    print(f"\n{'=' * len(header)}")
    print("  SlideQA Baseline Results")
    print(f"{'=' * len(header)}")
    print(header)
    print("-" * len(header))

    for cat in CATEGORIES:
        n = 0
        for bl in baselines:
            cd = all_results[bl]["summary"]["per_category"].get(cat, {})
            if cd.get("count", 0) > 0:
                n = cd["count"]
                break
        if n == 0:
            continue
        line = f"{cat:<18} {n:>4}"
        for bl in baselines:
            cd = all_results[bl]["summary"]["per_category"].get(cat, {})
            for m in metrics:
                line += f"  {cd.get(m, 0):>{col_w}.4f}"
        print(line)

    print("-" * len(header))
    line = f"{'OVERALL':<18} {first['summary']['overall']['count']:>4}"
    for bl in baselines:
        for m in metrics:
            line += f"  {all_results[bl]['summary']['overall'].get(m, 0):>{col_w}.4f}"
    print(line)
    print("=" * len(header))


def main():
    parser = argparse.ArgumentParser(description="Run SlideQA baselines and evaluate")
    parser.add_argument("--course", required=True)
    parser.add_argument("--model", default="openai/gpt-4o", help="OpenRouter model for all baselines")
    parser.add_argument("--only", choices=["text_only", "zero_shot_vlm"], help="Run only one baseline")
    parser.add_argument("--rate-limit", type=float, default=1.5, help="Seconds between API calls")
    args = parser.parse_args()

    # Load dataset
    qa_path = DATA_DIR / "annotations" / f"{args.course}_qa.json"
    if not qa_path.exists():
        raise FileNotFoundError(f"Dataset not found: {qa_path}")
    with open(qa_path) as f:
        qa_pairs = json.load(f)
    logger.info(f"Loaded {len(qa_pairs)} QA pairs from {qa_path}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    all_results = {}

    # ── Text-only baseline ──
    if args.only is None or args.only == "text_only":
        logger.info("=" * 50)
        logger.info("Running TEXT-ONLY baseline (BM25 + LLM)")
        logger.info("=" * 50)
        text_preds_path = RESULTS_DIR / f"{args.course}_text_only_preds.json"

        if text_preds_path.exists():
            logger.info(f"Loading cached predictions from {text_preds_path}")
            with open(text_preds_path) as f:
                text_preds = json.load(f)
        else:
            text_preds = run_text_only_baseline(
                qa_pairs, args.course, model=args.model, rate_limit=args.rate_limit
            )
            save_predictions(text_preds, text_preds_path)

        text_results = evaluate(qa_pairs, text_preds)
        print_results_table(text_results, "Text-Only (BM25 + LLM)")
        all_results["text_only"] = text_results

        # Save detailed results
        with open(RESULTS_DIR / f"{args.course}_text_only_details.json", "w") as f:
            json.dump(text_results, f, indent=2)

    # ── Zero-shot VLM baseline ──
    if args.only is None or args.only == "zero_shot_vlm":
        logger.info("=" * 50)
        logger.info("Running ZERO-SHOT VLM baseline (oracle slide + VLM)")
        logger.info("=" * 50)
        vlm_preds_path = RESULTS_DIR / f"{args.course}_zero_shot_vlm_preds.json"

        if vlm_preds_path.exists():
            logger.info(f"Loading cached predictions from {vlm_preds_path}")
            with open(vlm_preds_path) as f:
                vlm_preds = json.load(f)
        else:
            vlm_preds = run_zero_shot_vlm_baseline(
                qa_pairs, args.course, model=args.model, rate_limit=args.rate_limit
            )
            save_predictions(vlm_preds, vlm_preds_path)

        vlm_results = evaluate(qa_pairs, vlm_preds)
        print_results_table(vlm_results, "Zero-Shot VLM (Oracle Slide)")
        all_results["zero_shot_vlm"] = vlm_results

        # Save detailed results
        with open(RESULTS_DIR / f"{args.course}_zero_shot_vlm_details.json", "w") as f:
            json.dump(vlm_results, f, indent=2)

    # ── Combined output ──
    if len(all_results) > 1:
        print_combined_table(all_results)
        save_summary_csv(all_results, RESULTS_DIR / f"{args.course}_baseline_summary.csv")

    # Save combined details
    with open(RESULTS_DIR / f"{args.course}_all_results.json", "w") as f:
        json.dump({k: v["summary"] for k, v in all_results.items()}, f, indent=2)

    logger.info("Done!")


if __name__ == "__main__":
    main()

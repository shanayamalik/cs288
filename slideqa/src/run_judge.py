#!/usr/bin/env python3
"""Run LLM-as-judge scoring on all cached baseline predictions.

Loads existing *_preds.json files — no re-retrieval or re-generation needed.
Judge scores are saved incrementally so the run can be safely interrupted
and resumed without re-scoring already-judged questions.

Outputs per baseline+course:
  slideqa/data/results/{course}_{baseline}_judge_scores.json  — per-question scores (cache)
  slideqa/data/results/{course}_{baseline}_judge_details.json — full details with judge scores

Combined output:
  slideqa/data/results/all_courses_judge_summary.csv

Usage:
    # Score all baselines for all courses:
    python slideqa/src/run_judge.py

    # Score only one course:
    python slideqa/src/run_judge.py --course cs288

    # Score only specific baselines:
    python slideqa/src/run_judge.py --baselines text_only closed_book

    # Resume an interrupted run (already-scored questions are skipped):
    python slideqa/src/run_judge.py
"""

import argparse
import csv
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate import llm_judge_score, token_f1, exact_match

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
ANNOTATIONS_DIR = DATA_DIR / "annotations"

COURSES = ["cs288", "cs601", "cs224n"]
BASELINES = ["text_only", "zero_shot_vlm", "closed_book", "colpali_rag", "dense_text_rag"]
CATEGORIES = ["text_only", "image_diagram", "table", "chart_graph", "layout_aware"]

OPENROUTER_BASE = "https://openrouter.ai/api/v1"


def load_qa(course: str) -> dict:
    """Load QA annotations, keyed by question_id."""
    path = ANNOTATIONS_DIR / f"{course}_qa.json"
    with open(path) as f:
        qa_list = json.load(f)
    return {q["question_id"]: q for q in qa_list}


def load_preds(course: str, baseline: str) -> Optional[dict]:
    """Load cached predictions for a baseline, keyed by question_id. Returns None if missing."""
    path = RESULTS_DIR / f"{course}_{baseline}_preds.json"
    if not path.exists():
        logger.warning(f"Predictions not found: {path} — skipping")
        return None
    with open(path) as f:
        preds = json.load(f)
    return {p["question_id"]: p for p in preds}


def load_judge_cache(course: str, baseline: str) -> dict:
    """Load already-computed judge scores (question_id -> score). Empty dict if none."""
    path = RESULTS_DIR / f"{course}_{baseline}_judge_scores.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def save_judge_cache(cache: dict, course: str, baseline: str) -> None:
    path = RESULTS_DIR / f"{course}_{baseline}_judge_scores.json"
    with open(path, "w") as f:
        json.dump(cache, f, indent=2)


def run_judge_for_baseline(
    course: str,
    baseline: str,
    qa: dict,
    preds: dict,
    client,
    model: str,
    rate_limit: float,
) -> dict:
    """Score all predictions for one course+baseline with the LLM judge.

    Skips already-cached scores. Saves cache incrementally.
    Returns summary dict: {overall: {...}, per_category: {...}}.
    """
    cache = load_judge_cache(course, baseline)
    total = len(qa)
    scored = 0
    skipped = 0

    logger.info(f"  {course} / {baseline}: {len(cache)}/{total} already cached")

    for i, (qid, gt) in enumerate(qa.items()):
        if qid in cache:
            skipped += 1
            continue

        pred_entry = preds.get(qid, {})
        pred_answer = pred_entry.get("predicted_answer", "")
        gold = gt["answer"]

        score = llm_judge_score(
            gt["question"], pred_answer, gold, client=client, model=model
        )
        cache[qid] = score
        scored += 1

        if scored % 10 == 0:
            save_judge_cache(cache, course, baseline)
            logger.info(f"  [{i+1}/{total}] scored {scored} new, {skipped} cached")

        time.sleep(rate_limit)

    # Final save
    save_judge_cache(cache, course, baseline)
    logger.info(f"  Done. Scored {scored} new, {skipped} from cache. Total: {len(cache)}/{total}")

    # Build per-question details
    per_question = []
    for qid, gt in qa.items():
        pred_entry = preds.get(qid, {})
        pred_answer = pred_entry.get("predicted_answer", "")
        gold = gt["answer"]
        per_question.append({
            "question_id": qid,
            "question": gt["question"],
            "gold_answer": gold,
            "predicted_answer": pred_answer,
            "category": gt["category"],
            "difficulty": gt.get("difficulty", "unknown"),
            "scores": {
                "exact_match": exact_match(pred_answer, gold),
                "token_f1": token_f1(pred_answer, gold),
                "llm_judge": cache.get(qid, 3),
            },
        })

    # Save full details file
    details_path = RESULTS_DIR / f"{course}_{baseline}_judge_details.json"
    with open(details_path, "w") as f:
        json.dump(per_question, f, indent=2)

    # Compute summary
    summary = {"overall": {}, "per_category": {}}
    metrics = ["exact_match", "token_f1", "llm_judge"]

    summary["overall"]["count"] = len(per_question)
    for m in metrics:
        vals = [r["scores"][m] for r in per_question]
        summary["overall"][m] = round(sum(vals) / len(vals), 4) if vals else 0.0

    for cat in CATEGORIES:
        cat_qs = [r for r in per_question if r["category"] == cat]
        if not cat_qs:
            continue
        summary["per_category"][cat] = {"count": len(cat_qs)}
        for m in metrics:
            vals = [r["scores"][m] for r in cat_qs]
            summary["per_category"][cat][m] = round(sum(vals) / len(vals), 4) if vals else 0.0

    return summary


def print_judge_table(all_summaries: dict) -> None:
    """Print a compact summary table: course x baseline, showing judge scores."""
    print(f"\n{'=' * 80}")
    print("  LLM-as-Judge Summary (1–5 scale, macro-averaged)")
    print(f"{'=' * 80}")
    header = f"{'Course':<14}"
    for bl in BASELINES:
        header += f"  {bl[:12]:>14}"
    print(header)
    print("-" * len(header))
    for course in COURSES:
        line = f"{course:<14}"
        for bl in BASELINES:
            s = all_summaries.get((course, bl), {})
            score = s.get("overall", {}).get("llm_judge", None)
            line += f"  {score:>14.3f}" if score is not None else f"  {'—':>14}"
        print(line)
    print("=" * 80)


def save_judge_summary_csv(all_summaries: dict, baselines: list[str]) -> None:
    path = RESULTS_DIR / "all_courses_judge_summary.csv"
    metrics = ["exact_match", "token_f1", "llm_judge"]

    header = ["course", "category", "n"]
    for bl in baselines:
        for m in metrics:
            header.append(f"{bl}_{m}")

    rows = []
    for course in COURSES:
        for cat in CATEGORIES:
            n = 0
            for bl in baselines:
                s = all_summaries.get((course, bl), {})
                n = s.get("per_category", {}).get(cat, {}).get("count", 0)
                if n > 0:
                    break
            if n == 0:
                continue
            row = [course, cat, str(n)]
            for bl in baselines:
                s = all_summaries.get((course, bl), {})
                cat_data = s.get("per_category", {}).get(cat, {})
                for m in metrics:
                    row.append(f"{cat_data.get(m, 0.0):.4f}")
            rows.append(row)

        # Overall row
        n_overall = all_summaries.get((course, baselines[0]), {}).get("overall", {}).get("count", 0)
        row = [course, "OVERALL", str(n_overall)]
        for bl in baselines:
            s = all_summaries.get((course, bl), {})
            for m in metrics:
                row.append(f"{s.get('overall', {}).get(m, 0.0):.4f}")
        rows.append(row)

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    logger.info(f"Saved judge summary to {path}")


def load_summary_from_details(course: str, baseline: str) -> Optional[dict]:
    """Reconstruct a summary dict from an existing judge_details.json file."""
    path = RESULTS_DIR / f"{course}_{baseline}_judge_details.json"
    if not path.exists():
        return None
    with open(path) as f:
        per_question = json.load(f)
    if not per_question:
        return None

    metrics = ["exact_match", "token_f1", "llm_judge"]
    summary = {"overall": {}, "per_category": {}}
    summary["overall"]["count"] = len(per_question)
    for m in metrics:
        vals = [r["scores"][m] for r in per_question]
        summary["overall"][m] = round(sum(vals) / len(vals), 4) if vals else 0.0

    for cat in CATEGORIES:
        cat_qs = [r for r in per_question if r["category"] == cat]
        if not cat_qs:
            continue
        summary["per_category"][cat] = {"count": len(cat_qs)}
        for m in metrics:
            vals = [r["scores"][m] for r in cat_qs]
            summary["per_category"][cat][m] = round(sum(vals) / len(vals), 4) if vals else 0.0

    return summary


def main():
    parser = argparse.ArgumentParser(description="Run LLM-as-judge on all cached predictions")
    parser.add_argument("--course", choices=COURSES, default=None, help="Score one course only")
    parser.add_argument("--baselines", nargs="+", choices=BASELINES, default=BASELINES)
    parser.add_argument("--model", default="openai/gpt-4o", help="Judge model (OpenRouter)")
    parser.add_argument("--rate-limit", type=float, default=0.5, help="Seconds between judge calls")
    args = parser.parse_args()

    courses = [args.course] if args.course else COURSES

    from openai import OpenAI
    client = OpenAI(
        base_url=OPENROUTER_BASE,
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    all_summaries = {}

    for course in courses:
        qa = load_qa(course)
        for baseline in args.baselines:
            logger.info(f"{'=' * 50}")
            logger.info(f"Judging: {course} / {baseline}")
            logger.info(f"{'=' * 50}")

            preds = load_preds(course, baseline)
            if preds is None:
                continue

            summary = run_judge_for_baseline(
                course, baseline, qa, preds, client, args.model, args.rate_limit
            )
            all_summaries[(course, baseline)] = summary

            logger.info(
                f"  Overall: EM={summary['overall']['exact_match']:.4f}  "
                f"F1={summary['overall']['token_f1']:.4f}  "
                f"Judge={summary['overall']['llm_judge']:.3f}"
            )

    # Backfill summaries from existing judge_details.json for baselines not in this run
    for course in COURSES:
        for baseline in BASELINES:
            if (course, baseline) not in all_summaries:
                cached = load_summary_from_details(course, baseline)
                if cached is not None:
                    all_summaries[(course, baseline)] = cached

    print_judge_table(all_summaries)
    save_judge_summary_csv(all_summaries, BASELINES)
    logger.info("All done!")


if __name__ == "__main__":
    main()

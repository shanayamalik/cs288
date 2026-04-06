#!/usr/bin/env python3
"""Evaluation module: score model predictions against SlideQA ground truth.

Metrics: Exact Match, Token-F1, LLM-as-Judge (1-5 scale via OpenRouter).

Usage:
    python evaluate.py --course cs288 --predictions predictions.json
    python evaluate.py --course cs288 --predictions predictions.json --llm-judge
"""

import argparse
import json
import logging
import os
import re
import string
import time
from collections import Counter
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

CATEGORIES = ["text_only", "image_diagram", "table", "chart_graph", "layout_aware"]

OPENROUTER_BASE = "https://openrouter.ai/api/v1"


# ──────────────────────────────────────────────
# Text normalization (SQuAD-style)
# ──────────────────────────────────────────────
def normalize_text(text: str) -> str:
    """Lowercase, strip articles/punctuation/extra whitespace."""
    text = text.lower().strip()
    # Remove articles
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ──────────────────────────────────────────────
# Metrics
# ──────────────────────────────────────────────
def exact_match(pred: str, gold: str) -> float:
    return float(normalize_text(pred) == normalize_text(gold))


def token_f1(pred: str, gold: str) -> float:
    pred_tokens = normalize_text(pred).split()
    gold_tokens = normalize_text(gold).split()
    if not pred_tokens and not gold_tokens:
        return 1.0
    if not pred_tokens or not gold_tokens:
        return 0.0
    common = Counter(pred_tokens) & Counter(gold_tokens)
    num_common = sum(common.values())
    if num_common == 0:
        return 0.0
    precision = num_common / len(pred_tokens)
    recall = num_common / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def llm_judge_score(
    question: str, pred: str, gold: str,
    client=None, model: str = "openai/gpt-4o",
    max_retries: int = 3,
) -> int:
    """Use an LLM to judge answer quality on a 1-5 scale."""
    if client is None:
        from openai import OpenAI
        client = OpenAI(
            base_url=OPENROUTER_BASE,
            api_key=os.environ["OPENROUTER_API_KEY"],
        )

    prompt = f"""You are an expert evaluator for a lecture slide QA benchmark. Rate how well the predicted answer matches the gold answer for the given question.

Question: {question}
Gold answer: {gold}
Predicted answer: {pred}

Rating rubric:
5 = Fully correct, captures all key information
4 = Mostly correct, minor omissions or imprecisions
3 = Partially correct, captures some key points but misses others
2 = Mostly incorrect, but shows some relevant understanding
1 = Completely incorrect or irrelevant

Respond with ONLY a single integer (1-5)."""

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=5,
            )
            score = int(response.choices[0].message.content.strip())
            return max(1, min(5, score))
        except Exception as e:
            logger.warning(f"LLM judge attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(1.0 * attempt)
    return 3  # neutral fallback


# ──────────────────────────────────────────────
# Full evaluation
# ──────────────────────────────────────────────
def evaluate(
    ground_truth: list[dict],
    predictions: list[dict],
    use_llm_judge: bool = False,
    judge_model: str = "openai/gpt-4o",
) -> dict:
    """Evaluate predictions against ground truth.

    Args:
        ground_truth: list of QA dicts with question_id, question, answer, category
        predictions: list of dicts with question_id, predicted_answer
        use_llm_judge: whether to run LLM-as-judge scoring
        judge_model: OpenRouter model ID for LLM judge

    Returns:
        dict with "per_question" results and "summary" table
    """
    gt_by_id = {q["question_id"]: q for q in ground_truth}
    pred_by_id = {p["question_id"]: p for p in predictions}

    client = None
    if use_llm_judge:
        from openai import OpenAI
        client = OpenAI(
            base_url=OPENROUTER_BASE,
            api_key=os.environ["OPENROUTER_API_KEY"],
        )

    per_question = []
    for qid, gt in gt_by_id.items():
        pred_entry = pred_by_id.get(qid, {})
        pred_answer = pred_entry.get("predicted_answer", "")
        gold = gt["answer"]

        scores = {
            "exact_match": exact_match(pred_answer, gold),
            "token_f1": token_f1(pred_answer, gold),
        }
        if use_llm_judge:
            scores["llm_judge"] = llm_judge_score(
                gt["question"], pred_answer, gold, client=client, model=judge_model
            )
            time.sleep(0.5)  # rate limiting

        per_question.append({
            "question_id": qid,
            "question": gt["question"],
            "gold_answer": gold,
            "predicted_answer": pred_answer,
            "category": gt["category"],
            "difficulty": gt.get("difficulty", "unknown"),
            "evidence_slides": gt.get("evidence_slides", []),
            "retrieved_slides": pred_entry.get("retrieved_slides", []),
            "scores": scores,
        })

    # Build summary
    metric_names = ["exact_match", "token_f1"] + (["llm_judge"] if use_llm_judge else [])
    summary = {"overall": {}, "per_category": {}}

    # Overall
    summary["overall"]["count"] = len(per_question)
    for m in metric_names:
        vals = [r["scores"][m] for r in per_question]
        summary["overall"][m] = round(sum(vals) / len(vals), 4) if vals else 0

    # Per category
    for cat in CATEGORIES:
        cat_results = [r for r in per_question if r["category"] == cat]
        if not cat_results:
            continue
        summary["per_category"][cat] = {"count": len(cat_results)}
        for m in metric_names:
            vals = [r["scores"][m] for r in cat_results]
            summary["per_category"][cat][m] = round(sum(vals) / len(vals), 4) if vals else 0

    return {"per_question": per_question, "summary": summary}


def print_results_table(results: dict, baseline_name: str = "Baseline") -> None:
    """Pretty-print a results summary table."""
    summary = results["summary"]
    metrics = [k for k in summary["overall"] if k != "count"]

    header = f"{'Category':<18} {'N':>4}"
    for m in metrics:
        header += f"  {m:>14}"
    print(f"\n{'=' * len(header)}")
    print(f"  {baseline_name}")
    print(f"{'=' * len(header)}")
    print(header)
    print("-" * len(header))

    for cat in CATEGORIES:
        if cat not in summary["per_category"]:
            continue
        row = summary["per_category"][cat]
        line = f"{cat:<18} {row['count']:>4}"
        for m in metrics:
            line += f"  {row.get(m, 0):>14.4f}"
        print(line)

    print("-" * len(header))
    overall = summary["overall"]
    line = f"{'OVERALL':<18} {overall['count']:>4}"
    for m in metrics:
        line += f"  {overall.get(m, 0):>14.4f}"
    print(line)
    print("=" * len(header))


def main():
    parser = argparse.ArgumentParser(description="Evaluate predictions against SlideQA ground truth")
    parser.add_argument("--course", required=True)
    parser.add_argument("--predictions", required=True, help="Path to predictions JSON")
    parser.add_argument("--llm-judge", action="store_true")
    parser.add_argument("--output", help="Save detailed results JSON to this path")
    args = parser.parse_args()

    gt_path = DATA_DIR / "annotations" / f"{args.course}_qa.json"
    with open(gt_path) as f:
        ground_truth = json.load(f)
    with open(args.predictions) as f:
        predictions = json.load(f)

    results = evaluate(ground_truth, predictions, use_llm_judge=args.llm_judge)
    print_results_table(results, "Evaluation")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved to {args.output}")


if __name__ == "__main__":
    main()

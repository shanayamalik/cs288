#!/usr/bin/env python3
"""Evaluation script: score model predictions against SlideQA ground truth.

Supports multiple metrics: Exact Match, Token-F1, ROUGE-L, BERTScore, and LLM-as-judge.

Usage:
    python evaluate.py --course cs288 --predictions predictions.json
    python evaluate.py --course cs288 --predictions predictions.json --metrics token_f1 rouge_l --llm-judge
"""

import argparse
import json
import logging
import re
import string
from collections import Counter
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"

CATEGORIES = ["text_only", "image_diagram", "table", "chart_graph", "layout_aware"]


# ──────────────────────────────────────────────
# Text normalization (for EM / F1)
# ──────────────────────────────────────────────
def normalize_text(text: str) -> str:
    """Lowercase, strip punctuation and extra whitespace."""
    text = text.lower().strip()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text)
    return text


# ──────────────────────────────────────────────
# Metrics
# ──────────────────────────────────────────────
def exact_match(pred: str, gold: str) -> float:
    return float(normalize_text(pred) == normalize_text(gold))


def token_f1(pred: str, gold: str) -> float:
    pred_tokens = normalize_text(pred).split()
    gold_tokens = normalize_text(gold).split()
    if not pred_tokens or not gold_tokens:
        return float(pred_tokens == gold_tokens)
    common = Counter(pred_tokens) & Counter(gold_tokens)
    num_common = sum(common.values())
    if num_common == 0:
        return 0.0
    precision = num_common / len(pred_tokens)
    recall = num_common / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def compute_rouge_l(pred: str, gold: str) -> float:
    """ROUGE-L F1 using longest common subsequence."""
    pred_tokens = normalize_text(pred).split()
    gold_tokens = normalize_text(gold).split()
    if not pred_tokens or not gold_tokens:
        return float(pred_tokens == gold_tokens)

    # LCS via DP
    m, n = len(pred_tokens), len(gold_tokens)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if pred_tokens[i - 1] == gold_tokens[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    lcs_len = dp[m][n]
    if lcs_len == 0:
        return 0.0
    precision = lcs_len / m
    recall = lcs_len / n
    return 2 * precision * recall / (precision + recall)


def llm_judge_score(question: str, pred: str, gold: str, model: str = "gpt-4o") -> float:
    """Use an LLM to judge answer quality on a 1-5 scale, return normalized to [0, 1]."""
    from openai import OpenAI

    client = OpenAI()
    prompt = f"""You are an expert evaluator. Rate how well the predicted answer matches the gold answer for the given question.

Question: {question}
Gold answer: {gold}
Predicted answer: {pred}

Rate on a scale of 1-5:
1 = Completely wrong or irrelevant
2 = Partially relevant but mostly incorrect
3 = Partially correct, captures some key points
4 = Mostly correct with minor omissions or inaccuracies
5 = Fully correct and complete

Respond with ONLY a single integer (1-5)."""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=5,
    )
    try:
        score = int(response.choices[0].message.content.strip())
        return (score - 1) / 4.0  # normalize to [0, 1]
    except ValueError:
        logger.warning(f"LLM judge returned non-integer: {response.choices[0].message.content}")
        return 0.0


# ──────────────────────────────────────────────
# Main evaluation
# ──────────────────────────────────────────────
def evaluate(
    course: str,
    predictions_path: Path,
    metrics: list[str] = None,
    use_llm_judge: bool = False,
) -> dict:
    if metrics is None:
        metrics = ["exact_match", "token_f1", "rouge_l"]

    # Load ground truth
    gt_path = DATA_DIR / "annotations" / f"{course}_qa.json"
    if not gt_path.exists():
        raise FileNotFoundError(f"Ground truth not found: {gt_path}")
    with open(gt_path) as f:
        ground_truth = json.load(f)
    gt_by_id = {q["question_id"]: q for q in ground_truth}

    # Load predictions: expected format [{"question_id": ..., "predicted_answer": ...}, ...]
    with open(predictions_path) as f:
        predictions = json.load(f)
    pred_by_id = {p["question_id"]: p["predicted_answer"] for p in predictions}

    metric_fns = {
        "exact_match": exact_match,
        "token_f1": token_f1,
        "rouge_l": compute_rouge_l,
    }

    # Per-question scores
    results = []
    for qid, gt_entry in gt_by_id.items():
        pred = pred_by_id.get(qid, "")
        gold = gt_entry["answer"]
        category = gt_entry["category"]

        scores = {}
        for m in metrics:
            if m in metric_fns:
                scores[m] = metric_fns[m](pred, gold)
        if use_llm_judge:
            scores["llm_judge"] = llm_judge_score(gt_entry["question"], pred, gold)

        results.append({"question_id": qid, "category": category, "scores": scores})

    # Aggregate: overall and per-category
    all_metrics = metrics + (["llm_judge"] if use_llm_judge else [])
    summary = {"overall": {}, "per_category": {}}

    for m in all_metrics:
        vals = [r["scores"].get(m, 0) for r in results]
        summary["overall"][m] = sum(vals) / len(vals) if vals else 0

    for cat in CATEGORIES:
        cat_results = [r for r in results if r["category"] == cat]
        if not cat_results:
            continue
        summary["per_category"][cat] = {}
        for m in all_metrics:
            vals = [r["scores"].get(m, 0) for r in cat_results]
            summary["per_category"][cat][m] = sum(vals) / len(vals) if vals else 0
        summary["per_category"][cat]["count"] = len(cat_results)

    summary["total_questions"] = len(results)
    summary["total_predictions"] = len(pred_by_id)
    summary["missing_predictions"] = len(gt_by_id) - len(pred_by_id)

    return summary


def main():
    parser = argparse.ArgumentParser(description="Evaluate predictions against SlideQA ground truth")
    parser.add_argument("--course", required=True)
    parser.add_argument("--predictions", required=True, help="Path to predictions JSON")
    parser.add_argument("--metrics", nargs="+", default=["exact_match", "token_f1", "rouge_l"])
    parser.add_argument("--llm-judge", action="store_true", help="Also run LLM-as-judge scoring")
    parser.add_argument("--output", help="Save results JSON to this path")
    args = parser.parse_args()

    summary = evaluate(args.course, Path(args.predictions), args.metrics, args.llm_judge)

    print(json.dumps(summary, indent=2))

    if args.output:
        with open(args.output, "w") as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Results saved to {args.output}")


if __name__ == "__main__":
    main()

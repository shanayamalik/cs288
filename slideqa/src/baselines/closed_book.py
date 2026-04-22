#!/usr/bin/env python3
"""Closed-book baseline: question only, no slide image, no retrieved text.

Measures what GPT-4o knows from pretraining alone, with zero access to
lecture content. Acts as the lowest-bound baseline — any retrieval or
vision system should outperform this.

Usage:
    python -m baselines.closed_book --course cs288
"""

import json
import logging
import os
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

OPENROUTER_BASE = "https://openrouter.ai/api/v1"


def answer_closed_book(
    question: str,
    client,
    model: str = "openai/gpt-4o",
    max_retries: int = 3,
) -> str:
    """Answer a question with no context (closed-book)."""
    prompt = (
        "You are answering a question about NLP course lecture material. "
        "Answer as concisely and accurately as possible based on your knowledge. "
        "If you are unsure, give your best short answer.\n\n"
        f"Question: {question}\n\nAnswer:"
    )

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=256,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Closed-book attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(1.0 * attempt)
    return ""


def run_closed_book_baseline(
    qa_pairs: list[dict],
    course: str,
    model: str = "openai/gpt-4o",
    rate_limit: float = 1.0,
) -> list[dict]:
    """Run closed-book baseline on all QA pairs.

    Returns list of prediction dicts with question_id and predicted_answer.
    """
    from openai import OpenAI

    client = OpenAI(
        base_url=OPENROUTER_BASE,
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    predictions = []
    for i, qa in enumerate(qa_pairs):
        qid = qa["question_id"]
        question = qa["question"]

        answer = answer_closed_book(question, client, model=model)

        predictions.append({
            "question_id": qid,
            "predicted_answer": answer,
            "retrieved_slides": [],
            "baseline": "closed_book",
        })

        logger.info(f"[{i+1}/{len(qa_pairs)}] {qid}: {answer[:80]}...")
        time.sleep(rate_limit)

    return predictions


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--course", required=True)
    parser.add_argument("--model", default="openai/gpt-4o")
    parser.add_argument("--output", default=None)
    parser.add_argument("--rate-limit", type=float, default=1.0)
    args = parser.parse_args()

    qa_path = DATA_DIR / "annotations" / f"{args.course}_qa.json"
    with open(qa_path) as f:
        qa_pairs = json.load(f)

    preds = run_closed_book_baseline(
        qa_pairs, args.course, model=args.model, rate_limit=args.rate_limit
    )

    out = args.output or str(DATA_DIR / "results" / f"{args.course}_closed_book_preds.json")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(preds, f, indent=2)
    logger.info(f"Saved {len(preds)} predictions to {out}")

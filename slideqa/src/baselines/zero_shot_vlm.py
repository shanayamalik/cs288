#!/usr/bin/env python3
"""Zero-shot VLM baseline: oracle slide retrieval + VLM question answering.

Given the correct slide image, ask the VLM to answer directly.
Tests VLM comprehension with perfect retrieval (upper bound).

Usage:
    python -m baselines.zero_shot_vlm --course cs288
"""

import base64
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


def encode_image_b64(image_path: Path) -> str:
    return base64.b64encode(image_path.read_bytes()).decode("utf-8")


def answer_with_vlm(
    question: str,
    image_path: Path,
    client,
    model: str = "openai/gpt-4o",
    max_retries: int = 3,
) -> str:
    """Send slide image + question to VLM, return answer."""
    b64 = encode_image_b64(image_path)

    prompt = (
        "You are answering a question about a lecture slide. "
        "Look at the slide image carefully and answer the question "
        "as accurately and concisely as possible.\n\n"
        f"Question: {question}\n\nAnswer:"
    )

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"},
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
                temperature=0.0,
                max_tokens=256,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"VLM attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(1.0 * attempt)
    return ""


def run_zero_shot_vlm_baseline(
    qa_pairs: list[dict],
    course: str,
    model: str = "openai/gpt-4o",
    rate_limit: float = 1.5,
) -> list[dict]:
    """Run zero-shot VLM baseline on all QA pairs.

    Uses oracle retrieval — the evidence_slides field tells us which slide to show.
    """
    from openai import OpenAI

    client = OpenAI(
        base_url=OPENROUTER_BASE,
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    slides_dir = DATA_DIR / "slides" / course
    predictions = []

    for i, qa in enumerate(qa_pairs):
        qid = qa["question_id"]
        question = qa["question"]
        evidence = qa.get("evidence_slides", [])

        if not evidence:
            logger.warning(f"No evidence slides for {qid}, skipping")
            predictions.append({
                "question_id": qid,
                "predicted_answer": "",
                "retrieved_slides": [],
                "baseline": "zero_shot_vlm",
            })
            continue

        # Use the first evidence slide (single-slide questions)
        slide_ref = evidence[0]
        img_path = slides_dir / slide_ref

        if not img_path.exists():
            logger.warning(f"Image not found: {img_path}")
            predictions.append({
                "question_id": qid,
                "predicted_answer": "",
                "retrieved_slides": [slide_ref],
                "baseline": "zero_shot_vlm",
            })
            continue

        answer = answer_with_vlm(question, img_path, client, model=model)

        predictions.append({
            "question_id": qid,
            "predicted_answer": answer,
            "retrieved_slides": [slide_ref],
            "baseline": "zero_shot_vlm",
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
    args = parser.parse_args()

    qa_path = DATA_DIR / "annotations" / f"{args.course}_qa.json"
    with open(qa_path) as f:
        qa_pairs = json.load(f)

    preds = run_zero_shot_vlm_baseline(qa_pairs, args.course, model=args.model)

    out = args.output or str(DATA_DIR / "results" / f"{args.course}_zero_shot_vlm_preds.json")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(preds, f, indent=2)
    logger.info(f"Saved {len(preds)} predictions to {out}")

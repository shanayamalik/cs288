#!/usr/bin/env python3
"""Text-only baseline: BM25 retrieval over extracted slide text + LLM generation.

No vision — tests whether the questions require visual understanding.

Usage:
    python -m baselines.text_only --course cs288
"""

import json
import logging
import os
import time
from pathlib import Path

from rank_bm25 import BM25Okapi

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

OPENROUTER_BASE = "https://openrouter.ai/api/v1"


# ──────────────────────────────────────────────
# Text index
# ──────────────────────────────────────────────
class SlideTextIndex:
    """BM25 index over extracted slide text files."""

    def __init__(self, course: str):
        self.course = course
        self.text_dir = DATA_DIR / "text" / course
        if not self.text_dir.exists():
            raise FileNotFoundError(f"Text directory not found: {self.text_dir}")

        self.doc_ids = []   # e.g. "lecture_01/slide_010.txt"
        self.doc_texts = []

        for lecture_dir in sorted(self.text_dir.iterdir()):
            if not lecture_dir.is_dir():
                continue
            for txt_file in sorted(lecture_dir.glob("*.txt")):
                text = txt_file.read_text(encoding="utf-8").strip()
                if text:
                    rel = f"{lecture_dir.name}/{txt_file.stem}.png"
                    self.doc_ids.append(rel)
                    self.doc_texts.append(text)

        tokenized = [doc.lower().split() for doc in self.doc_texts]
        self.bm25 = BM25Okapi(tokenized)
        logger.info(f"Built BM25 index over {len(self.doc_ids)} slide texts")

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        """Retrieve top-k slide texts for a query."""
        tokens = query.lower().split()
        scores = self.bm25.get_scores(tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [
            {"slide_id": self.doc_ids[i], "text": self.doc_texts[i], "score": float(scores[i])}
            for i in top_indices
        ]


# ──────────────────────────────────────────────
# LLM answer generation
# ──────────────────────────────────────────────
def generate_answer(
    question: str,
    context_texts: list[str],
    client,
    model: str = "openai/gpt-4o",
    max_retries: int = 3,
) -> str:
    """Generate an answer from retrieved text context (no vision)."""
    context = "\n\n---\n\n".join(context_texts)
    prompt = f"""You are answering a question about lecture slides. Use ONLY the provided text context to answer. Be concise and specific.

Context from lecture slides:
{context}

Question: {question}

Answer:"""

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
            logger.warning(f"Generation attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(1.0 * attempt)
    return ""


# ──────────────────────────────────────────────
# Run baseline
# ──────────────────────────────────────────────
def run_text_only_baseline(
    qa_pairs: list[dict],
    course: str,
    model: str = "openai/gpt-4o",
    top_k: int = 3,
    rate_limit: float = 1.0,
) -> list[dict]:
    """Run text-only baseline on all QA pairs.

    Returns list of prediction dicts with question_id, predicted_answer, retrieved_slides.
    """
    from openai import OpenAI

    client = OpenAI(
        base_url=OPENROUTER_BASE,
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    index = SlideTextIndex(course)
    predictions = []

    for i, qa in enumerate(qa_pairs):
        qid = qa["question_id"]
        question = qa["question"]

        # Retrieve
        retrieved = index.retrieve(question, top_k=top_k)
        context_texts = [r["text"] for r in retrieved]
        retrieved_slides = [r["slide_id"] for r in retrieved]

        # Generate
        answer = generate_answer(question, context_texts, client, model=model)

        predictions.append({
            "question_id": qid,
            "predicted_answer": answer,
            "retrieved_slides": retrieved_slides,
            "baseline": "text_only",
        })

        logger.info(f"[{i+1}/{len(qa_pairs)}] {qid}: {answer[:80]}...")
        time.sleep(rate_limit)

    return predictions


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--course", required=True)
    parser.add_argument("--model", default="openai/gpt-4o")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    qa_path = DATA_DIR / "annotations" / f"{args.course}_qa.json"
    with open(qa_path) as f:
        qa_pairs = json.load(f)

    preds = run_text_only_baseline(qa_pairs, args.course, model=args.model, top_k=args.top_k)

    out = args.output or str(DATA_DIR / "results" / f"{args.course}_text_only_preds.json")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(preds, f, indent=2)
    logger.info(f"Saved {len(preds)} predictions to {out}")

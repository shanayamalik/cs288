#!/usr/bin/env python3
"""ColPali RAG baseline: multimodal retrieval + VLM question answering.

Retrieves the most relevant slide image using ColPali (late-interaction MaxSim
scoring), then passes it to GPT-4o to generate an answer.

This mirrors zero_shot_vlm.py but uses learned retrieval instead of oracle
evidence_slides — making it the primary engineering contribution of SlideQA.

Retrieval:
  1. Encode query with ColPali query encoder  → (N_tokens, 128) token embeddings
  2. For each slide in the pre-built index   → (N_patches, 128) patch embeddings
  3. MaxSim score: sum_t max_p sim(t, p)     → scalar score per slide
  4. Rank slides by score, return top-k

Answer generation:
  - Top-1 retrieved slide image + question → GPT-4o (via OpenRouter)

Outputs per prediction:
  - predicted_answer: str
  - retrieved_slides:  list of top-k slide IDs (e.g. ["lecture_04/slide_012.png"])
  - retrieval_score:   MaxSim score for the top-1 slide

Also computes Recall@k (fraction of questions where gold slide is in top-k).

Prerequisites:
  - Build the index first: python slideqa/src/build_index.py --course {course}
  - Index must exist at slideqa/data/colpali_index/{course}/embeddings.npy

Usage (called from run_baselines.py, or directly):
    python -m baselines.colpali_rag --course cs288
"""

import base64
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

import numpy as np
import torch
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INDEX_DIR = DATA_DIR / "colpali_index"

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
MODEL_NAME = "vidore/colpali-v1.2"


# ---------------------------------------------------------------------------
# Index loading
# ---------------------------------------------------------------------------

def load_index(course: str) -> tuple[np.ndarray, list[str]]:
    """Load pre-built ColPali index for a course.

    Returns:
        embeddings: float32 array of shape (N_slides, N_patches, dim)
        slide_ids:  list of N_slides slide ID strings
    """
    index_dir = INDEX_DIR / course
    emb_path = index_dir / "embeddings.npy"
    ids_path = index_dir / "slide_ids.json"

    if not emb_path.exists() or not ids_path.exists():
        raise FileNotFoundError(
            f"ColPali index not found for {course}. "
            f"Run: python slideqa/src/build_index.py --course {course}"
        )

    logger.info(f"  Loading index for {course} from {index_dir} ...")
    embeddings = np.load(emb_path)          # (N_slides, N_patches, dim)
    with open(ids_path) as f:
        slide_ids = json.load(f)

    logger.info(f"  Index: {embeddings.shape[0]} slides, {embeddings.shape[1]} patches, dim={embeddings.shape[2]}")
    return embeddings, slide_ids


# ---------------------------------------------------------------------------
# ColPali query encoder (loaded once, shared across all questions)
# ---------------------------------------------------------------------------

def load_query_encoder():
    """Load ColPali model + processor for query encoding only."""
    from colpali_engine.models import ColPali, ColPaliProcessor

    if torch.backends.mps.is_available():
        device = torch.device("mps")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")

    logger.info(f"  Loading ColPali query encoder on {device} ...")
    model = ColPali.from_pretrained(
        MODEL_NAME,
        dtype=torch.float32,
        device_map=None,
    ).to(device).eval()
    processor = ColPaliProcessor.from_pretrained(MODEL_NAME)
    logger.info("  Query encoder ready.")
    return model, processor, device


def encode_query(
    question: str,
    model,
    processor,
    device: torch.device,
) -> np.ndarray:
    """Encode a single text query into ColPali token embeddings.

    Returns:
        float32 numpy array of shape (N_tokens, dim)
    """
    batch = processor.process_queries(queries=[question]).to(device)
    with torch.no_grad():
        emb = model(**batch)               # (1, N_tokens, dim)
    return emb[0].to(dtype=torch.float32).cpu().numpy()  # (N_tokens, dim)


# ---------------------------------------------------------------------------
# MaxSim retrieval
# ---------------------------------------------------------------------------

def maxsim_scores(
    query_emb: np.ndarray,
    slide_embeddings: np.ndarray,
) -> np.ndarray:
    """Compute ColBERT-style MaxSim scores between a query and all slides.

    Args:
        query_emb:       (N_tokens, dim) — L2-normalised query token embeddings
        slide_embeddings:(N_slides, N_patches, dim) — L2-normalised patch embeddings

    Returns:
        scores: (N_slides,) float32 — MaxSim score per slide
    """
    # Dot products: (N_slides, N_patches, N_tokens)
    # = einsum("sd, td -> st", slide_patches, query) for each slide
    # Efficient: (N_slides, N_patches, dim) x (dim, N_tokens) -> (N_slides, N_patches, N_tokens)
    sims = np.einsum("spd,td->spt", slide_embeddings, query_emb)  # (S, P, T)
    # MaxSim: for each query token, max over patches; then sum over tokens
    scores = sims.max(axis=1).sum(axis=1)                          # (S,)
    return scores


def retrieve_top_k(
    question: str,
    slide_embeddings: np.ndarray,
    slide_ids: list[str],
    model,
    processor,
    device: torch.device,
    top_k: int = 5,
) -> list[str]:
    """Retrieve the top-k slide IDs for a question using MaxSim scoring."""
    query_emb = encode_query(question, model, processor, device)
    scores = maxsim_scores(query_emb, slide_embeddings)
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [slide_ids[i] for i in top_indices]


# ---------------------------------------------------------------------------
# VLM answer generation (same as zero_shot_vlm.py)
# ---------------------------------------------------------------------------

def encode_image_b64(image_path: Path) -> str:
    return base64.b64encode(image_path.read_bytes()).decode("utf-8")


def answer_with_vlm(
    question: str,
    image_path: Path,
    client,
    model: str = "openai/gpt-4o",
    max_retries: int = 3,
) -> str:
    """Send slide image + question to GPT-4o, return answer string."""
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


# ---------------------------------------------------------------------------
# Main baseline runner
# ---------------------------------------------------------------------------

def run_colpali_rag_baseline(
    qa_pairs: list[dict],
    course: str,
    model: str = "openai/gpt-4o",
    rate_limit: float = 1.5,
    top_k: int = 5,
) -> list[dict]:
    """Run ColPali RAG baseline on all QA pairs for a course.

    Returns list of prediction dicts with keys:
      question_id, predicted_answer, retrieved_slides, retrieval_score, baseline
    """
    from openai import OpenAI

    # Load pre-built index
    slide_embeddings, slide_ids = load_index(course)

    # Load ColPali query encoder (once)
    col_model, processor, device = load_query_encoder()

    # Load GPT-4o client
    gpt_client = OpenAI(
        base_url=OPENROUTER_BASE,
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    slides_dir = DATA_DIR / "slides" / course
    predictions = []

    for i, qa in enumerate(qa_pairs):
        qid = qa["question_id"]
        question = qa["question"]

        # Retrieve top-k slides via MaxSim
        top_slides = retrieve_top_k(
            question, slide_embeddings, slide_ids, col_model, processor, device, top_k=top_k
        )

        # Answer with top-1 retrieved slide
        top_slide_id = top_slides[0]
        img_path = slides_dir / top_slide_id

        if not img_path.exists():
            logger.warning(f"Retrieved slide not found: {img_path}")
            predictions.append({
                "question_id": qid,
                "predicted_answer": "",
                "retrieved_slides": top_slides,
                "retrieval_score": 0.0,
                "baseline": "colpali_rag",
            })
            continue

        predicted_answer = answer_with_vlm(question, img_path, gpt_client, model=model)

        predictions.append({
            "question_id": qid,
            "predicted_answer": predicted_answer,
            "retrieved_slides": top_slides,
            "baseline": "colpali_rag",
        })

        if (i + 1) % 10 == 0 or (i + 1) == len(qa_pairs):
            logger.info(f"  [{i + 1}/{len(qa_pairs)}] answered")

        time.sleep(rate_limit)

    # Log Recall@k
    log_recall(qa_pairs, predictions, top_k)

    return predictions


def log_recall(qa_pairs: list[dict], predictions: list[dict], top_k: int) -> None:
    """Compute and log Recall@k: fraction where gold slide is in top-k retrieved."""
    pred_by_id = {p["question_id"]: p for p in predictions}
    hits = 0
    total = 0
    for qa in qa_pairs:
        gold_slides = set(qa.get("evidence_slides", []))
        if not gold_slides:
            continue
        pred = pred_by_id.get(qa["question_id"], {})
        retrieved = set(pred.get("retrieved_slides", []))
        if gold_slides & retrieved:
            hits += 1
        total += 1
    recall = hits / total if total > 0 else 0.0
    logger.info(f"  Recall@{top_k}: {recall:.3f}  ({hits}/{total} questions)")

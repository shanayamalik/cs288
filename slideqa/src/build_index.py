#!/usr/bin/env python3
"""Build ColPali embedding index for slide retrieval.

Embeds all slide images in a course with ColPali (vidore/colpali-v1.2) and
saves per-slide patch embeddings to disk. The index is used at retrieval time
by colpali_rag.py to perform MaxSim scoring (ColBERT-style late interaction).

Outputs per course (in slideqa/data/colpali_index/{course}/):
  embeddings.npy        — float32 array of shape (N_slides, N_patches, dim)
  slide_ids.json        — list of N_slides slide IDs ("lecture_04/slide_012.png")

Why not FAISS?
  MaxSim requires grouping patches back by slide before summing, which FAISS
  IndexFlatIP doesn't support natively. A numpy matmul approach is simpler,
  exact, and fast enough for ~1300 slides at query time (~50 ms on CPU).

Memory estimate: ~700 MB per course on disk, ~700 MB RAM during scoring.

Usage:
    # Index all 3 courses (sequential, ~30-60 min total on MPS):
    python slideqa/src/build_index.py

    # Index one course only:
    python slideqa/src/build_index.py --course cs288

    # Force re-index even if index already exists:
    python slideqa/src/build_index.py --course cs288 --force

    # Use smaller batch size if running out of memory:
    python slideqa/src/build_index.py --batch-size 2
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SLIDES_DIR = DATA_DIR / "slides"
INDEX_DIR = DATA_DIR / "colpali_index"

COURSES = ["cs288", "cs601", "cs224n"]
MODEL_NAME = "vidore/colpali-v1.2"


def get_device() -> torch.device:
    """Pick the best available device: MPS (Apple Silicon) > CUDA > CPU."""
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def load_model(device: torch.device):
    """Load ColPali model and processor onto device."""
    from colpali_engine.models import ColPali, ColPaliProcessor

    logger.info(f"Loading ColPali model '{MODEL_NAME}' onto {device} ...")
    model = ColPali.from_pretrained(
        MODEL_NAME,
        dtype=torch.float32,
        device_map=None,
    ).to(device).eval()

    processor = ColPaliProcessor.from_pretrained(MODEL_NAME)
    logger.info("Model loaded.")
    return model, processor


def collect_slides(course: str) -> list[tuple[str, Path]]:
    """Return sorted list of (slide_id, path) for all PNGs in a course.

    slide_id format matches evidence_slides field in QA JSON:
        "lecture_04/slide_012.png"
    """
    course_dir = SLIDES_DIR / course
    if not course_dir.exists():
        raise FileNotFoundError(f"Slides directory not found: {course_dir}")

    slides = []
    for lecture_dir in sorted(course_dir.iterdir()):
        if not lecture_dir.is_dir():
            continue
        for png in sorted(lecture_dir.glob("*.png")):
            slide_id = f"{lecture_dir.name}/{png.name}"
            slides.append((slide_id, png))

    if not slides:
        raise RuntimeError(f"No PNG slides found under {course_dir}")

    logger.info(f"  Found {len(slides)} slides for {course}")
    return slides


def embed_slides(
    slides: list[tuple[str, Path]],
    model,
    processor,
    device: torch.device,
    batch_size: int = 4,
) -> tuple[np.ndarray, list[str]]:
    """Embed all slides and return (embeddings, slide_ids).

    embeddings: float32 numpy array of shape (N_slides, N_patches, dim)
    slide_ids:  list of N_slides slide ID strings
    """
    slide_ids = [sid for sid, _ in slides]
    paths = [p for _, p in slides]

    all_embeddings = []
    n = len(paths)
    n_batches = (n + batch_size - 1) // batch_size

    with tqdm(total=n, desc="  Embedding slides", unit="slide", dynamic_ncols=True) as pbar:
        for start in range(0, n, batch_size):
            end = min(start + batch_size, n)
            batch_paths = paths[start:end]

            # Load and convert images
            images = [Image.open(p).convert("RGB") for p in batch_paths]

            # Tokenize for ColPali
            batch_inputs = processor.process_images(images).to(device)

            with torch.no_grad():
                embeddings = model(**batch_inputs)  # (B, N_patches, dim)

            # Move to CPU and convert to float32 numpy immediately to free VRAM
            embeddings_np = embeddings.to(dtype=torch.float32).cpu().numpy()
            all_embeddings.append(embeddings_np)
            pbar.update(len(batch_paths))

            # Free MPS cache to prevent memory accumulation across batches
            if device.type == "mps":
                torch.mps.empty_cache()

    # Stack: each batch may have different N_patches if images vary — pad to max
    max_patches = max(e.shape[1] for e in all_embeddings)
    dim = all_embeddings[0].shape[2]

    padded = []
    for batch_emb in all_embeddings:
        b, p, d = batch_emb.shape
        if p < max_patches:
            pad = np.zeros((b, max_patches - p, d), dtype=np.float32)
            batch_emb = np.concatenate([batch_emb, pad], axis=1)
        padded.append(batch_emb)

    full_embeddings = np.concatenate(padded, axis=0)  # (N_slides, max_patches, dim)
    logger.info(f"    Embedding matrix shape: {full_embeddings.shape}")
    return full_embeddings, slide_ids


def build_course_index(
    course: str,
    model,
    processor,
    device: torch.device,
    batch_size: int,
    force: bool,
) -> None:
    """Build and save the ColPali index for one course."""
    out_dir = INDEX_DIR / course
    out_dir.mkdir(parents=True, exist_ok=True)

    emb_path = out_dir / "embeddings.npy"
    ids_path = out_dir / "slide_ids.json"

    if emb_path.exists() and ids_path.exists() and not force:
        logger.info(f"  Index already exists for {course} (use --force to rebuild). Skipping.")
        return

    logger.info(f"{'=' * 60}")
    logger.info(f"  Building index for: {course}")
    logger.info(f"{'=' * 60}")

    slides = collect_slides(course)
    embeddings, slide_ids = embed_slides(slides, model, processor, device, batch_size)

    np.save(emb_path, embeddings)
    with open(ids_path, "w") as f:
        json.dump(slide_ids, f, indent=2)

    logger.info(f"  Saved embeddings to {emb_path}  ({embeddings.nbytes / 1e6:.1f} MB)")
    logger.info(f"  Saved slide IDs to  {ids_path}")


def main():
    parser = argparse.ArgumentParser(description="Build ColPali slide embedding index")
    parser.add_argument("--course", choices=COURSES, default=None,
                        help="Build index for one course only (default: all)")
    parser.add_argument("--batch-size", type=int, default=4,
                        help="Images per forward pass (reduce if OOM, default: 4)")
    parser.add_argument("--force", action="store_true",
                        help="Re-build even if index already exists")
    args = parser.parse_args()

    device = get_device()
    logger.info(f"Using device: {device}")

    model, processor = load_model(device)

    courses = [args.course] if args.course else COURSES
    for course in courses:
        build_course_index(course, model, processor, device, args.batch_size, args.force)

    logger.info("All done!")


if __name__ == "__main__":
    main()

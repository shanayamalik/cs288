#!/usr/bin/env python3
"""Step 4A: LLM-assisted QA draft generation.

Sends each slide image to a VLM and asks it to generate candidate QA pairs.
Supports resuming (skips slides that already have drafts).

Usage:
    python generate_qa.py --course cs288 --model gpt-4o
    python generate_qa.py --course cs288 --model gemini-2.0-flash
"""

import argparse
import base64
import json
import logging
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"

# ──────────────────────────────────────────────
# Prompt template
# ──────────────────────────────────────────────
QA_GENERATION_PROMPT = """\
You are helping build a QA benchmark for lecture slides. Given this lecture slide image, generate question-answer pairs for as many of the following categories as applicable. Only generate for categories where the slide has relevant content.

Categories:
1. text_only — question answerable from the text on the slide alone
2. image_diagram — question requiring interpretation of a figure, diagram, or mathematical expression
3. table — question requiring reading/reasoning over a table
4. chart_graph — question requiring interpretation of a chart or data visualization
5. layout_aware — question requiring understanding of spatial layout (e.g., comparing side-by-side content, grouped elements)

For each QA pair, respond in this JSON format:
{
  "question": "...",
  "answer": "...",
  "category": "text_only | image_diagram | table | chart_graph | layout_aware",
  "difficulty": "easy | medium | hard",
  "reasoning": "Brief explanation of why this question fits the category and requires the specified modality"
}

Return a JSON array of QA pairs. If the slide has no meaningful content for QA (e.g., a title slide or section divider), return an empty array [].
"""


# ──────────────────────────────────────────────
# VLM API callers
# ──────────────────────────────────────────────
def encode_image_b64(image_path: Path) -> str:
    """Read an image file and return its base64-encoded string."""
    return base64.b64encode(image_path.read_bytes()).decode("utf-8")


import re

def _safe_json_loads(raw: str) -> list[dict]:
    """Parse JSON from VLM output, handling common issues like bad escapes and trailing commas."""
    # Try as-is first
    for attempt_raw in [raw]:
        try:
            return json.loads(attempt_raw)
        except json.JSONDecodeError:
            pass

    # Fix 1: invalid \escape sequences (e.g. \frac, \theta)
    fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', raw)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # Fix 2: trailing commas before ] or }
    fixed = re.sub(r',\s*([}\]])', r'\1', fixed)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # Fix 3: try extracting just the JSON array from the response
    match = re.search(r'\[.*\]', fixed, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Give up — raise the original error
    return json.loads(raw)


def call_openai(image_path: Path, model: str = "gpt-4o", base_url: str = None) -> list[dict]:
    """Send a slide image to an OpenAI-compatible vision API and return parsed QA pairs."""
    import os
    from openai import OpenAI

    # Support OpenRouter via OPENROUTER_API_KEY + base_url override
    if base_url:
        client = OpenAI(base_url=base_url, api_key=os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY"))
    else:
        client = OpenAI()  # uses OPENAI_API_KEY env var
    b64 = encode_image_b64(image_path)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": QA_GENERATION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"},
                    },
                ],
            }
        ],
        temperature=0.3,
        max_tokens=2048,
    )
    raw = response.choices[0].message.content.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw[: raw.rfind("```")]
    return _safe_json_loads(raw)


def call_gemini(image_path: Path, model: str = "gemini-2.0-flash") -> list[dict]:
    """Send a slide image to Google's Gemini API and return parsed QA pairs."""
    import google.generativeai as genai
    from PIL import Image

    img = Image.open(image_path)
    gm = genai.GenerativeModel(model)
    response = gm.generate_content(
        [QA_GENERATION_PROMPT, img],
        generation_config=genai.GenerationConfig(temperature=0.3, max_output_tokens=2048),
    )
    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw[: raw.rfind("```")]
    return _safe_json_loads(raw)


OPENROUTER_BASE = "https://openrouter.ai/api/v1"

MODEL_CALLERS = {
    # Direct APIs
    "gpt-4o": call_openai,
    "gpt-4.1": lambda p: call_openai(p, model="gpt-4.1"),
    "gemini-2.0-flash": call_gemini,
    "gemini-2.5-pro": lambda p: call_gemini(p, model="gemini-2.5-pro-preview-03-25"),
    # OpenRouter (uses OPENROUTER_API_KEY env var)
    "openrouter/gpt-4o": lambda p: call_openai(p, model="openai/gpt-4o", base_url=OPENROUTER_BASE),
    "openrouter/gpt-4.1": lambda p: call_openai(p, model="openai/gpt-4.1", base_url=OPENROUTER_BASE),
    "openrouter/gemini-2.0-flash": lambda p: call_openai(p, model="google/gemini-2.0-flash-001", base_url=OPENROUTER_BASE),
    "openrouter/gemini-2.5-pro": lambda p: call_openai(p, model="google/gemini-2.5-pro-preview-03-25", base_url=OPENROUTER_BASE),
    "openrouter/qwen2-vl-72b": lambda p: call_openai(p, model="qwen/qwen2-vl-72b-instruct", base_url=OPENROUTER_BASE),
}


# ──────────────────────────────────────────────
# Draft management
# ──────────────────────────────────────────────
def load_existing_drafts(drafts_path: Path) -> dict:
    """Load existing drafts file. Returns dict keyed by slide image path."""
    if drafts_path.exists():
        with open(drafts_path) as f:
            drafts = json.load(f)
        return {d["evidence_slide"]: d for d in drafts}
    return {}


def save_drafts(drafts: dict, drafts_path: Path) -> None:
    """Save all drafts to JSON."""
    drafts_path.parent.mkdir(parents=True, exist_ok=True)
    with open(drafts_path, "w") as f:
        json.dump(list(drafts.values()), f, indent=2)


# ──────────────────────────────────────────────
# Main pipeline
# ──────────────────────────────────────────────
def generate_qa_for_course(
    course: str,
    model: str = "gpt-4o",
    rate_limit_delay: float = 1.0,
    max_retries: int = 3,
    lectures: list = None,
) -> None:
    slides_dir = DATA_DIR / "slides" / course
    if not slides_dir.exists():
        raise FileNotFoundError(f"Slides directory not found: {slides_dir}. Run process_pdfs.py first.")

    # Sanitize model name for filename: openrouter/gpt-4o → openrouter_gpt-4o
    model_slug = model.replace("/", "_")
    drafts_path = DATA_DIR / "annotations" / f"{course}_qa_drafts_{model_slug}.json"
    existing = load_existing_drafts(drafts_path)
    logger.info(f"Loaded {len(existing)} existing drafts from {drafts_path}")

    caller = MODEL_CALLERS.get(model)
    if caller is None:
        raise ValueError(f"Unsupported model: {model}. Choose from: {list(MODEL_CALLERS.keys())}")

    # Collect all slide images sorted by lecture then slide number
    slide_images = sorted(slides_dir.rglob("*.png"))
    if lectures:
        lecture_dirs = {f"lecture_{int(l):02d}" for l in lectures}
        slide_images = [p for p in slide_images if p.parent.name in lecture_dirs]
        logger.info(f"Filtering to lectures: {sorted(lecture_dirs)}")
    logger.info(f"Found {len(slide_images)} slide images")

    q_counter = len(existing)  # for question_id numbering
    skipped = 0
    generated = 0
    empty = 0

    for img_path in slide_images:
        # Relative key: e.g., "lecture_01/slide_003.png"
        rel_key = f"{img_path.parent.name}/{img_path.name}"

        if rel_key in existing:
            skipped += 1
            continue

        logger.info(f"Generating QA for {rel_key} ...")

        for attempt in range(1, max_retries + 1):
            try:
                qa_pairs = caller(img_path)
                break
            except Exception as e:
                logger.warning(f"  Attempt {attempt}/{max_retries} failed: {e}")
                if attempt == max_retries:
                    logger.error(f"  Skipping {rel_key} after {max_retries} failures")
                    qa_pairs = None
                time.sleep(rate_limit_delay * attempt)

        if qa_pairs is None:
            continue

        if len(qa_pairs) == 0:
            empty += 1
            # Still record that we processed this slide (so we don't retry)
            existing[rel_key] = {
                "evidence_slide": rel_key,
                "course": course,
                "qa_pairs": [],
                "status": "empty",
                "annotator": f"llm_{model}",
            }
        else:
            for qa in qa_pairs:
                q_counter += 1
                qa["question_id"] = f"{course}_q{q_counter:04d}"
                qa["status"] = "draft"
                qa["annotator"] = f"llm_{model}"
            existing[rel_key] = {
                "evidence_slide": rel_key,
                "course": course,
                "qa_pairs": qa_pairs,
                "status": "draft",
                "annotator": f"llm_{model}",
            }
            generated += len(qa_pairs)

        # Save after each slide so we can resume
        save_drafts(existing, drafts_path)
        time.sleep(rate_limit_delay)

    logger.info(
        f"Done. Generated {generated} QA pairs, {empty} empty slides, {skipped} skipped (already had drafts)."
    )


def main():
    parser = argparse.ArgumentParser(description="Generate QA drafts from slide images using a VLM")
    parser.add_argument("--course", required=True, help="Course identifier (e.g., cs288)")
    parser.add_argument(
        "--model",
        default="gpt-4o",
        choices=list(MODEL_CALLERS.keys()),
        help="VLM model to use (default: gpt-4o)",
    )
    parser.add_argument("--rate-limit", type=float, default=1.0, help="Seconds between API calls (default: 1.0)")
    parser.add_argument("--max-retries", type=int, default=3, help="Max retries per slide (default: 3)")
    parser.add_argument("--lectures", type=int, nargs="+", help="Lecture numbers to process (e.g., --lectures 1 2 3). Default: all")
    args = parser.parse_args()
    generate_qa_for_course(args.course, model=args.model, rate_limit_delay=args.rate_limit, max_retries=args.max_retries, lectures=args.lectures)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Step 1 & 2: Convert lecture PDFs into individual slide images + extracted text.

Usage:
    python process_pdfs.py --course cs288
    python process_pdfs.py --course cs288 --dpi 300 --ocr-fallback
"""

import argparse
import json
import logging
from pathlib import Path

# pdf2image for rendering, PyMuPDF for text extraction (prefer over OCR)
# Fallback to pytesseract only when PyMuPDF returns empty text
try:
    from pdf2image import convert_from_path
except ImportError:
    raise ImportError("Install pdf2image: pip install pdf2image (requires poppler)")

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from PIL import Image
    import pytesseract
except ImportError:
    pytesseract = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"


def get_pdf_dir(course: str) -> Path:
    return DATA_DIR / "raw_pdfs" / course


def get_slides_dir(course: str) -> Path:
    return DATA_DIR / "slides" / course


def get_text_dir(course: str) -> Path:
    return DATA_DIR / "text" / course


# ──────────────────────────────────────────────
# Step 1: PDF → slide images
# ──────────────────────────────────────────────
def pdf_to_images(pdf_path: Path, output_dir: Path, dpi: int = 300) -> list[Path]:
    """Convert a single PDF into one PNG per page/slide.

    Returns list of paths to generated images.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    images = convert_from_path(str(pdf_path), dpi=dpi)
    saved_paths: list[Path] = []
    for i, img in enumerate(images, start=1):
        out_path = output_dir / f"slide_{i:03d}.png"
        img.save(str(out_path), "PNG")
        saved_paths.append(out_path)
    logger.info(f"  → {len(saved_paths)} slides saved to {output_dir}")
    return saved_paths


# ──────────────────────────────────────────────
# Step 2: Extract text per slide
# ──────────────────────────────────────────────
def extract_text_pymupdf(pdf_path: Path) -> list[str]:
    """Extract text from each page using PyMuPDF (fast, no OCR)."""
    if fitz is None:
        raise ImportError("Install PyMuPDF: pip install pymupdf")
    doc = fitz.open(str(pdf_path))
    texts = [page.get_text() for page in doc]
    doc.close()
    return texts


def extract_text_ocr(image_path: Path) -> str:
    """Fallback: OCR a slide image using pytesseract."""
    if pytesseract is None:
        raise ImportError("Install pytesseract: pip install pytesseract")
    img = Image.open(image_path)
    return pytesseract.image_to_string(img)


def save_slide_texts(texts: list[str], output_dir: Path) -> None:
    """Save extracted text as one .txt file per slide."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for i, text in enumerate(texts, start=1):
        out_path = output_dir / f"slide_{i:03d}.txt"
        out_path.write_text(text, encoding="utf-8")


# ──────────────────────────────────────────────
# Metadata tracking
# ──────────────────────────────────────────────
def build_metadata(course: str, lecture_num: int, pdf_name: str, num_slides: int) -> list[dict]:
    """Return a list of metadata dicts, one per slide."""
    return [
        {
            "course": course,
            "lecture": lecture_num,
            "slide": slide_num,
            "source_pdf": pdf_name,
            "image_path": f"{course}/lecture_{lecture_num:02d}/slide_{slide_num:03d}.png",
            "text_path": f"{course}/lecture_{lecture_num:02d}/slide_{slide_num:03d}.txt",
        }
        for slide_num in range(1, num_slides + 1)
    ]


# ──────────────────────────────────────────────
# Main pipeline
# ──────────────────────────────────────────────
def process_course(course: str, dpi: int = 300, ocr_fallback: bool = False) -> None:
    pdf_dir = get_pdf_dir(course)
    if not pdf_dir.exists():
        raise FileNotFoundError(f"PDF directory not found: {pdf_dir}")

    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {pdf_dir}")

    logger.info(f"Found {len(pdf_files)} PDFs in {pdf_dir}")
    all_metadata: list[dict] = []

    for lecture_num, pdf_path in enumerate(pdf_files, start=1):
        logger.info(f"Processing lecture {lecture_num}: {pdf_path.name}")

        lecture_tag = f"lecture_{lecture_num:02d}"
        slides_out = get_slides_dir(course) / lecture_tag
        text_out = get_text_dir(course) / lecture_tag

        # Step 1: render slide images
        image_paths = pdf_to_images(pdf_path, slides_out, dpi=dpi)

        # Step 2: extract text
        try:
            texts = extract_text_pymupdf(pdf_path)
        except (ImportError, Exception) as e:
            if ocr_fallback:
                logger.warning(f"PyMuPDF failed ({e}), falling back to OCR")
                texts = [extract_text_ocr(p) for p in image_paths]
            else:
                raise

        save_slide_texts(texts, text_out)

        # Metadata
        meta = build_metadata(course, lecture_num, pdf_path.name, len(image_paths))
        all_metadata.extend(meta)

    # Save consolidated metadata
    meta_path = DATA_DIR / "annotations" / f"{course}_slide_metadata.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    with open(meta_path, "w") as f:
        json.dump(all_metadata, f, indent=2)
    logger.info(f"Metadata saved to {meta_path} ({len(all_metadata)} slides total)")


def main():
    parser = argparse.ArgumentParser(description="Process lecture PDFs into slide images + text")
    parser.add_argument("--course", required=True, help="Course identifier (e.g., cs288)")
    parser.add_argument("--dpi", type=int, default=300, help="Render DPI (default: 300)")
    parser.add_argument("--ocr-fallback", action="store_true", help="Use OCR if PyMuPDF text extraction fails")
    args = parser.parse_args()
    process_course(args.course, dpi=args.dpi, ocr_fallback=args.ocr_fallback)


if __name__ == "__main__":
    main()

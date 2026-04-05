#!/usr/bin/env python3
"""SlideQA dataset loader.

Loads approved QA annotations, pairs them with slide images, and provides
filtering, statistics, and split functionality.

Usage:
    from slideqa_dataset import SlideQADataset
    ds = SlideQADataset("cs288")
    ds.print_stats()
    text_only = ds.filter(category="text_only")
"""

import json
from pathlib import Path

CATEGORIES = ["text_only", "image_diagram", "table", "chart_graph", "layout_aware"]
DIFFICULTIES = ["easy", "medium", "hard"]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


class SlideQADataset:
    """Loader for approved SlideQA annotations."""

    def __init__(self, course: str, data_dir: Path | None = None):
        self.course = course
        self.data_dir = data_dir or DATA_DIR
        self.annotations_path = self.data_dir / "annotations" / f"{course}_qa.json"
        self.slides_dir = self.data_dir / "slides" / course

        if not self.annotations_path.exists():
            raise FileNotFoundError(f"Annotations not found: {self.annotations_path}")

        with open(self.annotations_path) as f:
            self.qa_pairs: list[dict] = json.load(f)

    def __len__(self) -> int:
        return len(self.qa_pairs)

    def __getitem__(self, idx: int) -> dict:
        entry = self.qa_pairs[idx].copy()
        # Resolve slide image paths
        entry["slide_image_paths"] = [
            self.slides_dir / slide_ref for slide_ref in entry.get("evidence_slides", [])
        ]
        return entry

    def filter(
        self,
        category: str | None = None,
        difficulty: str | None = None,
        lecture: int | None = None,
    ) -> list[dict]:
        """Filter QA pairs by category, difficulty, or lecture number."""
        results = self.qa_pairs
        if category:
            results = [q for q in results if q.get("category") == category]
        if difficulty:
            results = [q for q in results if q.get("difficulty") == difficulty]
        if lecture is not None:
            lecture_prefix = f"lecture_{lecture:02d}/"
            results = [
                q for q in results if any(lecture_prefix in s for s in q.get("evidence_slides", []))
            ]
        return results

    def get_all_with_images(self) -> list[dict]:
        """Return all QA pairs with resolved slide image paths."""
        return [self[i] for i in range(len(self))]

    def stats(self) -> dict:
        """Compute summary statistics."""
        total = len(self.qa_pairs)
        by_category = {cat: 0 for cat in CATEGORIES}
        by_difficulty = {d: 0 for d in DIFFICULTIES}
        lectures_seen: set[str] = set()

        for q in self.qa_pairs:
            cat = q.get("category", "unknown")
            diff = q.get("difficulty", "unknown")
            by_category[cat] = by_category.get(cat, 0) + 1
            by_difficulty[diff] = by_difficulty.get(diff, 0) + 1
            for slide in q.get("evidence_slides", []):
                parts = slide.split("/")
                if parts:
                    lectures_seen.add(parts[0])

        return {
            "total": total,
            "by_category": by_category,
            "by_difficulty": by_difficulty,
            "num_lectures": len(lectures_seen),
            "lectures": sorted(lectures_seen),
        }

    def print_stats(self) -> None:
        """Pretty-print dataset statistics."""
        s = self.stats()
        print(f"\n{'=' * 50}")
        print(f"SlideQA Dataset — {self.course.upper()}")
        print(f"{'=' * 50}")
        print(f"Total QA pairs: {s['total']}")
        print(f"Lectures covered: {s['num_lectures']}")
        print(f"\nBy category:")
        for cat in CATEGORIES:
            count = s["by_category"].get(cat, 0)
            pct = (count / s["total"] * 100) if s["total"] > 0 else 0
            print(f"  {cat:20s}: {count:4d} ({pct:5.1f}%)")
        print(f"\nBy difficulty:")
        for d in DIFFICULTIES:
            count = s["by_difficulty"].get(d, 0)
            pct = (count / s["total"] * 100) if s["total"] > 0 else 0
            print(f"  {d:20s}: {count:4d} ({pct:5.1f}%)")
        print(f"{'=' * 50}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--course", required=True)
    args = parser.parse_args()
    ds = SlideQADataset(args.course)
    ds.print_stats()

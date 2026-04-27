# SlideQA

A multimodal benchmark and retrieval-augmented VLM pipeline for lecture slide question answering.  
**CS 288 (Advanced NLP) — UC Berkeley, Spring 2026**

## Team

Nathan McNaughton, Nicholas Eliacin, Shanaya Malik

## Overview

SlideQA is a QA benchmark built from lecture slides of three public NLP courses (UC Berkeley CS 288, Stanford CS 224N, JHU CS 601.471). It includes 450 curated questions (150 per course) spanning five categories:

1. **Text-only reasoning** — answerable from slide text alone
2. **Image/diagram interpretation** — figures, diagrams, math expressions
3. **Table comprehension** — reading and reasoning over tables
4. **Chart/graph analysis** — interpreting data visualizations
5. **Layout-aware reasoning** — spatial relationships between slide elements

We pair the benchmark with a ColPali retrieval-augmented multimodal pipeline and evaluate four systems: closed-book GPT-4o, text-only BM25 retrieval, ColPali RAG, and an oracle VLM upper bound (given the gold evidence slide directly).

## Paper

The ICLR 2026 writeup is in [`iclr2026/report.tex`](iclr2026/report.tex). Compile with:
```bash
cd iclr2026
pdflatex report.tex && bibtex report && pdflatex report.tex && pdflatex report.tex
```

## Demo

An interactive demo is available at **https://shanaya-is-a-genius.streamlit.app/**. Browse questions by course, compare model outputs side by side, and view the leaderboard.

## Setup

```bash
git clone https://github.com/shanayamalik/cs288-sp26-slideQA.git
cd cs288-sp26-slideQA

python3 -m venv .venv
source .venv/bin/activate
pip install -r slideqa/requirements.txt

# macOS system deps
brew install poppler
```

### API Keys

```bash
# Edit .env and fill in:
OPENROUTER_API_KEY=sk-or-...
export $(grep -v '^#' .env | xargs)
```

### Running the Pipeline

Replace `cs288` with `cs224n` or `cs601` for other courses.

```bash
# 1. Process PDFs into slide images + text
python slideqa/src/process_pdfs.py --course cs288

# 2. Generate + curate QA pairs
python slideqa/src/generate_qa.py --course cs288 --model openrouter/gpt-4o
python slideqa/src/curate_qa.py --course cs288 --target 150

# 3. Build ColPali index
python slideqa/src/build_index.py --course cs288

# 4. Run ColPali RAG
python slideqa/src/run_colpali_rag.py --course cs288

# 5. Evaluate
python slideqa/src/evaluate.py --course cs288
```

## Results

Scores are LLM-judge ratings on a 1–5 scale, averaged over 150 questions per course. Token-F1 is also reported for exact-match comparison.

### LLM-Judge Score (1–5)

| Course | Closed-Book | Text-Only | ColPali RAG | Oracle VLM |
|---|---|---|---|---|
| CS 288 (Berkeley) | 2.09 | 1.79 | 3.73 | **4.70** |
| CS 601 (JHU) | 2.03 | 2.11 | 3.39 | **4.42** |
| CS 224N (Stanford) | 1.81 | 1.53 | 3.75 | **4.60** |

### Token-F1

| Course | Closed-Book | Text-Only | ColPali RAG | Oracle VLM |
|---|---|---|---|---|
| CS 288 (Berkeley) | 0.088 | 0.143 | 0.292 | **0.377** |
| CS 601 (JHU) | 0.090 | 0.186 | 0.296 | **0.373** |
| CS 224N (Stanford) | 0.077 | 0.100 | 0.316 | **0.394** |

### ColPali Retrieval Recall

| Course | R@1 | R@3 | R@5 |
|---|---|---|---|
| CS 288 | 0.500 | 0.747 | 0.793 |
| CS 601 | 0.373 | 0.600 | 0.707 |
| CS 224N | 0.480 | 0.807 | 0.827 |

Oracle VLM (given the gold evidence slide directly) is the upper bound. ColPali RAG substantially outperforms text-only and closed-book across all courses, with the gap largest on diagram- and chart-heavy questions. Retrieval recall at R@5 exceeds 70% on all courses.
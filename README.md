# SlideQA

A multimodal benchmark and retrieval-augmented VLM agent for lecture slide question answering.  
**CS 288 (Advanced NLP) — UC Berkeley, Spring 2026**

## Team

Nathan McNaughton, Nicholas Eliacin, Shanaya Malik

## Overview

SlideQA is a QA benchmark built from lecture slides of three public NLP courses (UC Berkeley CS 288, Stanford CS 224N, JHU CS 601.471). It includes five question categories:

1. **Text-only reasoning** — answerable from slide text alone
2. **Image/diagram interpretation** — figures, diagrams, math expressions
3. **Table comprehension** — reading and reasoning over tables
4. **Chart/graph analysis** — interpreting data visualizations
5. **Layout-aware reasoning** — spatial relationships between slide elements

We pair the benchmark with a retrieval-augmented multimodal pipeline (ColPali + VLM) and compare against text-only and zero-shot baselines.

## Project Structure

```
slideqa/
├── data/
│   ├── raw_pdfs/{cs288,cs224n,cs601}/   # Lecture PDFs (tracked in git)
│   ├── slides/                           # Extracted slide images (gitignored)
│   ├── text/                             # Extracted slide text (gitignored)
│   └── annotations/                      # QA JSON files
├── src/
│   ├── process_pdfs.py                   # PDF → slide images + text
│   ├── generate_qa.py                    # VLM-assisted QA draft generation
│   ├── curate_qa.py                      # Auto-filter + balanced sampling
│   ├── annotate.py                       # Streamlit review tool
│   ├── evaluate.py                       # Evaluation metrics
│   └── slideqa_dataset.py                # Dataset loader + stats
├── requirements.txt
iclr2026/                                 # Paper (ICLR 2026 format)
```

## Setup

```bash
# Clone the repo (Git LFS required for lecture PDFs)
git lfs install
git clone https://github.com/shanayamalik/cs288-sp26-slideQA.git
cd cs288-sp26-slideQA

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r slideqa/requirements.txt

# Install system dependencies (macOS)
brew install poppler    # required for pdf2image
brew install git-lfs    # if not already installed
```

### API Keys

Copy the `.env` template and paste your key:

```bash
cp .env .env.local   # optional — .env works too
# Edit .env and fill in:
OPENROUTER_API_KEY=sk-or-...
```

Then load it before running scripts:

```bash
export $(grep -v '^#' .env | xargs)
```

The `.env` file is gitignored — never commit API keys.

## Usage

### 1. Process PDFs into slide images + text
```bash
python slideqa/src/process_pdfs.py --course cs288
```

### 2. Generate QA drafts using a VLM
```bash
python slideqa/src/generate_qa.py --course cs288 --model openrouter/gpt-4o
```

### 3. Curate benchmark subset
```bash
python slideqa/src/curate_qa.py --course cs288 --target 75
```

### 4. (Optional) Review QA pairs in Streamlit
```bash
streamlit run slideqa/src/annotate.py -- --course cs288
```

### 5. View dataset statistics
```bash
python slideqa/src/slideqa_dataset.py --course cs288
```

### 6. Evaluate predictions
```bash
python slideqa/src/evaluate.py --course cs288 --predictions path/to/preds.json
```

## Baselines (Checkpoint 2)

Two baselines to measure the value of multimodality:

| Baseline | Input | What it tests |
|---|---|---|
| Zero-shot VLM | slide image + question | Upper bound — full visual context |
| Text-only LLM | extracted text + question (no image) | Does vision actually help? |

Both use GPT-4o via OpenRouter. Run with:
```bash
python slideqa/src/run_baselines.py --course cs288
```

### Results (3-lecture pilot, 75 QA pairs)

| Category | N | Text-Only F1 | Text-Only Judge | VLM F1 | VLM Judge |
|---|---|---|---|---|---|
| text_only | 7 | 0.330 | 4.43 | 0.547 | 5.00 |
| image_diagram | 35 | 0.211 | 2.26 | 0.396 | 4.66 |
| table | 7 | 0.164 | 1.71 | 0.550 | 4.57 |
| chart_graph | 9 | 0.180 | 1.44 | 0.510 | 4.67 |
| layout_aware | 17 | 0.208 | 1.82 | 0.433 | 4.29 |
| **Overall** | **75** | **0.213** | **2.21** | **0.447** | **4.60** |

**Key takeaways:**
- The VLM baseline (with the correct slide image) more than doubles Token-F1 (0.21 → 0.45) and LLM-Judge score (2.2 → 4.6) over text-only, confirming the benchmark requires genuine visual understanding.
- The gap is largest on **chart_graph** (1.44 → 4.67) and **table** (1.71 → 4.57) — categories where the answer lives in a visual element that text extraction misses entirely.
- Exact Match is 0% for both baselines because answers are free-form; LLM-as-Judge (1-5 scale) is the most informative metric.

Detailed per-question results are in `slideqa/data/results/`.

## Progress

- [x] Project scaffolding and paper abstract
- [x] PDF processing pilot (3 lectures, 183 slides)
- [x] QA draft generation (GPT-4o, 706 pairs)
- [x] Auto-curation (75 benchmark pairs across 5 categories)
- [x] Baseline evaluation (zero-shot VLM vs text-only)
- [ ] Scale to full CS 288 (16 lectures)
- [ ] Add Stanford CS 224N and JHU CS 601.471
- [ ] Retrieval pipeline (ColPali + vector DB)
- [ ] Final evaluation and ablations
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

Evaluation uses **Exact Match** and **Token-F1** (SQuAD-style). Answers are short-form (≤10 words) for reliable automated scoring.

| Category | N | Text-Only EM | Text-Only F1 | VLM EM | VLM F1 |
|---|---|---|---|---|---|
| text_only | 7 | 0.143 | 0.272 | 0.000 | 0.535 |
| image_diagram | 43 | 0.000 | 0.115 | 0.023 | 0.294 |
| table | 11 | 0.000 | 0.063 | 0.000 | 0.368 |
| chart_graph | 7 | 0.000 | 0.138 | 0.000 | 0.519 |
| layout_aware | 7 | 0.000 | 0.175 | 0.000 | 0.392 |
| **Overall** | **75** | **0.013** | **0.130** | **0.013** | **0.358** |

**Key takeaways:**
- The VLM baseline (with the correct slide image) nearly triples Token-F1 over text-only (0.36 vs 0.13), confirming the benchmark requires genuine visual understanding.
- The gap is largest on **chart_graph** (0.14 → 0.52) and **table** (0.06 → 0.37) — categories where the answer lives in a visual element that text extraction misses.
- EM is low for both baselines (~1%) because even short answers get paraphrased. Token-F1 is our primary metric.

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
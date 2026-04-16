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

# To generate for specific lectures only (e.g., first 3):
python slideqa/src/generate_qa.py --course cs601 --model openrouter/gpt-4o --lectures 1 2 3
```

### 3. Curate benchmark subset
```bash
python slideqa/src/curate_qa.py --course cs288 --target 150
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

### Results (3-lecture pilot per course, 75 QA pairs each — re-running on scaled data)

| Course | Text-Only F1 | VLM F1 | VLM Advantage |
|---|---|---|---|
| CS 288 (Berkeley) | 0.130 | 0.358 | 2.75x |
| CS 601 (JHU) | 0.376 | 0.558 | 1.48x |
| CS 224N (Stanford) | 0.106 | 0.372 | 3.51x |

VLM consistently outperforms text-only across all three courses. The advantage is largest on CS 224N (diagram-heavy) and smallest on CS 601 (text-heavy PPT slides). See [RESULTS.md](RESULTS.md) for detailed per-category breakdowns and reproduction steps.

## Progress

- [x] Project scaffolding and paper abstract
- [x] PDF processing — CS 288 (17 lectures, 1301 slides)
- [x] PDF processing — CS 601 (19 lectures, 1264 slides)
- [x] PDF processing — CS 224N (19 lectures, 1207 slides)
- [x] QA generation — CS 288 (5518 drafts → 150 curated, balanced across lectures + categories)
- [x] Baseline evaluation — CS 288, CS 601, CS 224N (pilot, 75 Qs each)
- [ ] QA generation — CS 601 (scale to all 19 lectures, 150 curated)
- [ ] QA generation — CS 224N (scale to all 19 lectures, 150 curated)
- [ ] Re-run baselines on scaled 150-question sets
- [ ] Multimodal RAG baseline (ColPali embeddings → retrieval → VLM generation)
- [ ] Final evaluation and ablations
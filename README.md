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

### Results

Evaluation uses **Exact Match** and **Token-F1** (SQuAD-style). Answers are short-form (≤10 words) for reliable automated scoring.

#### UC Berkeley CS 288 (3 lectures, 75 QA pairs)

| Category | N | Text-Only EM | Text-Only F1 | VLM EM | VLM F1 |
|---|---|---|---|---|---|
| text_only | 7 | 0.143 | 0.272 | 0.000 | 0.535 |
| image_diagram | 43 | 0.000 | 0.115 | 0.023 | 0.294 |
| table | 11 | 0.000 | 0.063 | 0.000 | 0.368 |
| chart_graph | 7 | 0.000 | 0.138 | 0.000 | 0.519 |
| layout_aware | 7 | 0.000 | 0.175 | 0.000 | 0.392 |
| **Overall** | **75** | **0.013** | **0.130** | **0.013** | **0.358** |

#### JHU CS 601.471 (3 lectures, 75 QA pairs)

| Category | N | Text-Only EM | Text-Only F1 | VLM EM | VLM F1 |
|---|---|---|---|---|---|
| text_only | 53 | 0.132 | 0.383 | 0.151 | 0.554 |
| image_diagram | 16 | 0.000 | 0.218 | 0.063 | 0.427 |
| table | 4 | 0.500 | 0.854 | 0.250 | 0.917 |
| layout_aware | 2 | 0.000 | 0.519 | 1.000 | 1.000 |
| **Overall** | **75** | **0.120** | **0.376** | **0.160** | **0.558** |

#### Cross-course comparison

| Course | Text-Only F1 | VLM F1 | VLM Advantage |
|---|---|---|---|
| CS 288 (Berkeley) | 0.130 | 0.358 | 2.75x |
| CS 601 (JHU) | 0.376 | 0.558 | 1.48x |

**Key takeaways:**
- VLM consistently outperforms text-only across both courses, confirming the benchmark requires visual understanding.
- The VLM advantage is larger on CS 288 (2.75x) which has more diagram/chart-heavy slides, vs CS 601 (1.48x) which has older, more text-heavy PPT slides.
- CS 601's higher text_only category share (53/75 vs 7/75) explains why text-only BM25+LLM performs better there.
- EM is low for both baselines because even short answers get paraphrased. Token-F1 is our primary metric.

Detailed per-question results are in `slideqa/data/results/`.

### Reproducing CS 601 results

The JHU CS 601.471 slides were originally `.ppt`/`.pptx` files. They were converted to PDF using LibreOffice headless:
```bash
# Install LibreOffice (macOS, one-time)
brew install --cask libreoffice

# Convert PPT/PPTX to PDF (already done — PDFs are in the repo)
soffice --headless --convert-to pdf *.ppt *.pptx
```

Then run the standard pipeline:
```bash
# 1. Process all lectures (extracts slide images + text)
python slideqa/src/process_pdfs.py --course cs601

# 2. Generate QA for first 3 lectures only
python slideqa/src/generate_qa.py --course cs601 --model openrouter/gpt-4o --rate-limit 1.5 --lectures 1 2 3

# 3. Curate 75 short-answer QA pairs
python slideqa/src/curate_qa.py --course cs601 --target 75

# 4. Run baselines
python slideqa/src/run_baselines.py --course cs601 --rate-limit 1.0
```

## Progress

- [x] Project scaffolding and paper abstract
- [x] PDF processing pilot — CS 288 (3 lectures, 183 slides)
- [x] QA draft generation — CS 288 (GPT-4o, 706 pairs → 75 curated)
- [x] Baseline evaluation — CS 288 (zero-shot VLM vs text-only)
- [x] JHU CS 601.471 added (19 lectures, 1264 slides; 3-lecture pilot: 231 pairs → 75 curated)
- [x] Baseline evaluation — CS 601 (zero-shot VLM vs text-only)
- [ ] Add Stanford CS 224N (3-lecture pilot)
- [ ] Scale to full CS 288 (16 lectures)
- [ ] Scale to full CS 601 and CS 224N
- [ ] Retrieval pipeline (ColPali + vector DB)
- [ ] Final evaluation and ablations
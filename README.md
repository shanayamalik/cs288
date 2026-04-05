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
│   ├── annotate.py                       # Streamlit review tool
│   ├── evaluate.py                       # Evaluation metrics
│   └── slideqa_dataset.py                # Dataset loader + stats
├── requirements.txt
iclr2026/                                 # Paper (ICLR 2026 format)
```

## Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r slideqa/requirements.txt

# Install poppler (macOS — required for pdf2image)
brew install poppler
```

## Usage

### 1. Process PDFs into slide images + text
```bash
python slideqa/src/process_pdfs.py --course cs288
```

### 2. Generate QA drafts using a VLM
```bash
# Requires OPENAI_API_KEY in environment
python slideqa/src/generate_qa.py --course cs288 --model gpt-4o
```

### 3. Review and annotate QA pairs
```bash
streamlit run slideqa/src/annotate.py -- --course cs288
```

### 4. View dataset statistics
```bash
python slideqa/src/slideqa_dataset.py --course cs288
```

### 5. Evaluate predictions
```bash
python slideqa/src/evaluate.py --course cs288 --predictions path/to/preds.json
```

## Progress

- [x] Project scaffolding and paper abstract
- [ ] Dataset creation (CS 288 pilot — 3 lectures)
- [ ] Baseline VLM evaluation
- [ ] Scale to full CS 288 (16 lectures)
- [ ] Add Stanford CS 224N and JHU CS 601.471
- [ ] Retrieval pipeline (ColPali + vector DB)
- [ ] Final evaluation and ablations
# Nathan's Guide — ColPali RAG Pipeline

Hi Nathan! This doc covers everything you need to get set up and build the retrieval pipeline from scratch. 

Shanaya is working in parallel on: per-category breakdown, LM-as-judge, and the closed-book baseline. Your work and hers are independent — no ordering dependencies. The one coordination note is at the bottom.

---

## 1. Prerequisites

You need **Git LFS** installed before cloning, so the lecture PDFs download correctly.

```bash
brew install git-lfs
git lfs install
```

---

## 2. Clone and Set Up

```bash
git clone https://github.com/shanayamalik/cs288-sp26-slideQA.git
cd cs288-sp26-slideQA

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install existing dependencies
pip install -r slideqa/requirements.txt

# Install system dependency for PDF rendering
brew install poppler
```

---

## 3. API Key

Ask Shanaya for the OpenRouter API key. Create a `.env` file in the project root:

```bash
echo "OPENROUTER_API_KEY=sk-or-YOUR_KEY_HERE" > .env
```

Then load it into your shell before running any script:

```bash
export $(grep -v '^#' .env | xargs)
```

You'll need to run this every time you open a new terminal. Put it in a shell alias if you prefer.

---

## 4. Install ColPali and FAISS

These are new dependencies not yet in `requirements.txt` — install them manually:

```bash
pip install colpali-engine faiss-cpu torch torchvision pillow
```

> Note: `colpali-engine` downloads the `vidore/colpali-v1.2` model from HuggingFace (~5GB) the first time it runs. Make sure you have space and a decent connection.

Also add these to `slideqa/requirements.txt` so they're tracked:
```
colpali-engine>=0.3.0
faiss-cpu>=1.8.0
torch>=2.2.0
torchvision>=0.17.0
```

---

## 5. Regenerate Slide Images

Slide images (PNGs) are `.gitignore`'d since they're large and regenerable from the PDFs (which are tracked via Git LFS). You need to generate them locally before building the index.

```bash
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)

python slideqa/src/process_pdfs.py --course cs288
python slideqa/src/process_pdfs.py --course cs601
python slideqa/src/process_pdfs.py --course cs224n
```

This takes ~10–15 minutes per course. Slides are saved to `slideqa/data/slides/{course}/`.

---

## 6. Project Structure (what already exists)

```
slideqa/
├── data/
│   ├── raw_pdfs/{cs288,cs601,cs224n}/   # Lecture PDFs (in git via LFS)
│   ├── slides/                           # Slide PNGs — you generate these (step 5)
│   ├── annotations/
│   │   ├── cs288_qa.json                 # 150 curated QA pairs
│   │   ├── cs601_qa.json                 # 150 curated QA pairs
│   │   └── cs224n_qa.json               # 150 curated QA pairs
│   └── results/                          # Existing baseline results
├── src/
│   ├── process_pdfs.py                   # Step 5 above
│   ├── run_baselines.py                  # Baseline runner — you'll add colpali_rag here
│   ├── evaluate.py                       # EM + Token-F1 metrics (already implemented)
│   └── baselines/
│       ├── text_only.py                  # BM25 + LLM (reference implementation)
│       └── zero_shot_vlm.py              # Oracle image + VLM (reference implementation)
```

**Read `baselines/zero_shot_vlm.py` carefully** — your ColPali RAG baseline follows the same structure. It loads QA pairs, calls an answer function per question, and returns a list of `{"question_id": ..., "predicted_answer": ..., "retrieved_slides": [...], "baseline": "colpali_rag"}` dicts.

---

## 7. What to Build

You need two new files:

### File 1: `slideqa/src/build_index.py`

Offline preprocessing — embeds all slide images with ColPali and saves a FAISS index. Run once per course.

**What it does:**
1. Finds all slide PNG paths for the course under `slideqa/data/slides/{course}/`
2. Loads the ColPali model (`vidore/colpali-v1.2`)
3. Encodes each slide image → a single embedding vector (ColPali produces patch-level embeddings; average-pool them to get a single vector per slide)
4. Builds a FAISS flat L2 index over all slide vectors
5. Saves the index to `slideqa/data/indexes/{course}_colpali.index`
6. Saves a companion JSON `slideqa/data/indexes/{course}_colpali_index_map.json` mapping FAISS row integer → slide metadata (at minimum: `slide_path`, `slide_id` matching the format in `cs288_qa.json`)

**Run as:**
```bash
python slideqa/src/build_index.py --course cs288
python slideqa/src/build_index.py --course cs601
python slideqa/src/build_index.py --course cs224n
```

**Slide ID format to match:** Open `slideqa/data/annotations/cs288_qa.json` and look at the `evidence_slides` field — it looks like `"cs288/lecture_04/slide_012.png"`. Your index map should use this same relative path format so the RAG baseline can load the correct image.

---

### File 2: `slideqa/src/baselines/colpali_rag.py`

The actual RAG baseline. Mirrors `zero_shot_vlm.py` in structure.

**What it does per question:**
1. Loads the FAISS index + index map for the course
2. Encodes the question text with ColPali's query encoder → query vector
3. Searches FAISS for top-k=5 nearest slides
4. Takes the top-1 retrieved slide image
5. Sends slide image + question to GPT-4o via OpenRouter (same `answer_with_vlm` call as in `zero_shot_vlm.py` — you can import it directly)
6. Returns prediction with `retrieved_slides` list (all top-k, not just top-1) so we can compute Recall@k later

**Key function signature to match:**
```python
def run_colpali_rag_baseline(
    qa_pairs: list[dict],
    course: str,
    model: str = "openai/gpt-4o",
    rate_limit: float = 1.5,
    top_k: int = 5,
) -> list[dict]:
```

---

### File 3: Update `slideqa/src/run_baselines.py`

Add `colpali_rag` as a third option. Look at how `zero_shot_vlm` is wired in — add the same pattern for `colpali_rag`. Cache file should be `{course}_colpali_rag_preds.json`.

The `--only` argument already accepts specific baselines, so just add `"colpali_rag"` to the choices list and add the corresponding block.

Run as:
```bash
python slideqa/src/run_baselines.py --course cs288 --only colpali_rag
python slideqa/src/run_baselines.py --course cs601 --only colpali_rag
python slideqa/src/run_baselines.py --course cs224n --only colpali_rag
```

---

## 8. Coordination with Shanaya (LM-as-Judge)

Shanaya is adding LM-as-judge scoring to `evaluate.py`. Once her branch is merged, you can re-evaluate your cached ColPali predictions with the judge by just changing one argument in the `evaluate()` call — no other changes needed. So don't worry about it now; build the pipeline with EM/F1 first.

---

## 9. Commit Order

1. After building indexes: commit `build_index.py` + the index files. **Check first whether the `.index` files are large** (likely 50–200MB each). If so, add them to `.gitignore` (like slide images) and note in the README that they need to be regenerated locally. The `index_map.json` files are small and should always be committed.
2. After running and verifying: commit `colpali_rag.py` + updated `run_baselines.py` + all result files (`cs288_colpali_rag_preds.json`, `cs288_colpali_rag_details.json`, etc.) together.

Push to a branch (`git checkout -b nathan`) and open a PR to main.

---

## 10. Expected Results

For reference, the two existing baselines score:

| Course | Text-Only F1 | Oracle VLM F1 |
|--------|-------------|---------------|
| CS 288 | 0.143 | 0.377 |
| CS 601 | 0.186 | 0.373 |
| CS 224N | 0.100 | 0.394 |

The ColPali RAG pipeline should land **between** these two. Text-only is the lower bound (no vision), Oracle VLM is the upper bound (perfect retrieval). If ColPali RAG is close to or above Oracle VLM, something is wrong. If it's at or below Text-Only, the retrieval isn't working.

A healthy result might look like F1 ≈ 0.25–0.35 — better than text-only because we're feeding visual slides, but below oracle because retrieval isn't perfect.

---

Questions? Ask Shanaya or check the code — `zero_shot_vlm.py` is the closest reference for almost everything you need.

# SlideQA — Copilot Prompt: Dataset Creation Pipeline

## Full Project Context

I'm building **SlideQA**, a multimodal QA benchmark and retrieval-augmented VLM agent for lecture slide question-answering, as my final project for CS 288 (Advanced NLP) at UC Berkeley.

### What the project involves (full scope)
1. **A QA benchmark** built from lecture slides of three public NLP courses (UC Berkeley CS 288, Stanford CS 224N, JHU CS 601.471). The benchmark has five question categories:
   - **(1) Text-only reasoning** — answerable from slide text alone
   - **(2) Image/diagram interpretation** — requires understanding figures, diagrams, or mathematical expressions rendered as images
   - **(3) Table comprehension** — requires reading and reasoning over tables
   - **(4) Chart/graph analysis** — requires interpreting data visualizations
   - **(5) Layout-aware reasoning** — requires understanding spatial relationships between slide elements (e.g., comparing items in side-by-side columns, interpreting grouped content blocks)

2. **A retrieval-augmented VLM-based agent** that:
   - Embeds slide images using a vision-language model (e.g., ColPali)
   - Stores embeddings in a vector database
   - At inference, retrieves the most relevant slides for a given question
   - Generates an answer conditioned on the retrieved slide(s) using a VLM

3. **Baselines** for comparison:
   - Text-only baseline (OCR/pdf-to-text → text retrieval → LLM)
   - Zero-shot VLM baseline (feed slide image + question directly to a VLM, no retrieval)

4. **Ablation studies** comparing design choices (e.g., text-only vs. multimodal retrieval, different VLMs, different numbers of retrieved slides)

### What I need RIGHT NOW (this session)
I'm working on **Checkpoint 2** (midpoint report, due 04/09). The first task is to build a **modest-sized dataset from one course (CS 288)** that I can evaluate baselines against. I'll scale to Stanford and JHU courses later for the final report.

I have **16 lecture PDFs** (one per lecture), stored locally. Each PDF contains the full slide deck for that lecture.

---

## Task: Build the SlideQA Dataset Creation Pipeline

### Step 1: Process lecture PDFs into individual slide images

- Input: 16 lecture PDF files (one per lecture)
- Output: Individual slide images (one PNG per slide), organized by lecture
- Naming convention: `lecture_{NN}/slide_{MMM}.png` (e.g., `lecture_01/slide_003.png`)
- Use a PDF-to-image library (e.g., `pdf2image` / `poppler` in Python, or equivalent)
- Render at high resolution (at least 300 DPI) so text and diagrams remain legible for VLMs
- Track metadata: for each slide image, store lecture number, slide number, and source filename

### Step 2: Extract text from each slide (for text-only baseline later)

- Use OCR (e.g., `pytesseract`) or a PDF text extraction library (e.g., `pdfplumber`, `PyMuPDF/fitz`) to extract the raw text from each slide
- Store the extracted text alongside each slide image in a structured format
- This text extraction doesn't need to be perfect — it's primarily for the text-only baseline

### Step 3: Design the QA annotation schema

Create a JSON schema for each QA pair that captures:

```json
{
  "question_id": "cs288_q001",
  "question": "What is the difference between precision and recall as shown in the diagram?",
  "answer": "Precision measures the fraction of retrieved items that are relevant, while recall measures the fraction of relevant items that are retrieved.",
  "category": "image_diagram",
  "evidence_slides": ["lecture_03/slide_015.png"],
  "course": "cs288",
  "difficulty": "medium",
  "requires_multi_slide": false,
  "metadata": {
    "lecture_topic": "Evaluation Metrics",
    "question_type": "comparison",
    "annotator": "human_verified"
  }
}
```

The `annotator` field should track provenance:
- `"human"` — written from scratch by a human annotator
- `"llm_gpt4o"` (or the model used) — LLM-generated draft, not yet reviewed
- `"human_verified"` — LLM-generated, then reviewed and approved/edited by a human
```

The five valid values for `category` are:
- `"text_only"` — category 1
- `"image_diagram"` — category 2 (includes math expressions)
- `"table"` — category 3
- `"chart_graph"` — category 4
- `"layout_aware"` — category 5

### Step 4: LLM-assisted QA generation + human review tool

This step has two parts: (A) automated draft generation using a VLM, and (B) a review interface for human verification.

#### Part A: LLM-assisted QA draft generation (`generate_qa.py`)

Write a script that sends each slide image to a VLM API (e.g., OpenAI's GPT-4o or Google's Gemini) and asks it to generate candidate QA pairs. The script should:

- Iterate through processed slide images (from Step 1)
- For each slide, send the image to the VLM with a prompt like:

```
You are helping build a QA benchmark for lecture slides. Given this lecture slide image, generate question-answer pairs for as many of the following categories as applicable. Not every category will apply to every slide — only generate for categories where the slide has relevant content.

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
```

- Save the raw LLM-generated drafts to a separate file (`cs288_qa_drafts.json`) with a `"status": "draft"` field and `"annotator": "llm_gpt4o"` (or whichever model was used)
- Include rate limiting and error handling (retry on API failures)
- Support resuming from where it left off (skip slides that already have drafts)
- Log which slides produced QA pairs and which were skipped (empty arrays)

#### Part B: Human review and annotation tool (`annotate.py`)

Build a Streamlit or Gradio app that lets human annotators review, edit, and approve/reject the LLM-generated drafts. The tool should:

- Load the LLM-generated drafts from `cs288_qa_drafts.json`
- Display the slide image prominently alongside the draft QA pair(s) for that slide
- For each draft QA pair, let the reviewer:
  - **Approve** it as-is
  - **Edit** the question, answer, category, or difficulty and then approve
  - **Reject** it (with an optional reason)
  - **Add a new QA pair** manually if the LLM missed a good question for that slide
- Let the annotator browse by lecture and filter by review status (draft / approved / rejected)
- Auto-populate metadata (lecture number, slide number, course)
- Save approved annotations to the final `cs288_qa.json` file, appending as we go (so we don't lose work if it crashes)
- Track review progress: show how many drafts have been reviewed vs. remaining

### Step 5: Create a dataset loader

Write a Python module (`slideqa_dataset.py` or similar) that:
- Loads the JSON annotations file
- Provides easy access to QA pairs, filtered by category, difficulty, or lecture
- Pairs each QA entry with its corresponding slide image(s)
- Provides train/test split functionality (or just a single evaluation split for now, since this is a benchmark)
- Prints summary statistics (total QA pairs, breakdown by category, coverage across lectures)

---

## Technical Preferences

- **Language**: Python 3.10+
- **Key libraries**: `pdf2image`, `Pillow`, `pdfplumber` or `PyMuPDF`, `pytesseract` (if OCR needed), `openai` or `google-generativeai` (for VLM-based QA generation), `json`, `pathlib`
- **For the annotation tool**: Prefer Streamlit or Gradio for quick iteration; Jupyter notebook is acceptable as a fallback
- **Code style**: Clear docstrings, type hints, modular functions
- **File organization**: This is just an IDEA/SUGGESTION, not necessarily how you might want to organize it
  ```
  slideqa/
  ├── data/
  │   ├── raw_pdfs/
  │   │   ├── cs288/              # UC Berkeley CS 288 (current focus)
  │   │   ├── cs224n/             # Stanford CS 224N (to be added after Checkpoint 2)
  │   │   └── cs601/              # JHU CS 601.471 (to be added after Checkpoint 2)
  │   ├── slides/                 # Extracted slide images
  │   │   ├── cs288/
  │   │   │   ├── lecture_01/
  │   │   │   │   ├── slide_001.png
  │   │   │   │   └── ...
  │   │   │   └── ...
  │   │   ├── cs224n/             # Empty for now
  │   │   └── cs601/              # Empty for now
  │   ├── text/                   # Extracted text per slide
  │   │   ├── cs288/
  │   │   │   ├── lecture_01/
  │   │   │   │   ├── slide_001.txt
  │   │   │   │   └── ...
  │   │   │   └── ...
  │   │   ├── cs224n/             # Empty for now
  │   │   └── cs601/              # Empty for now
  │   └── annotations/
  │       ├── cs288_qa_drafts.json   # LLM-generated drafts (for review)
  │       ├── cs288_qa.json          # Approved QA pairs (final)
  │       ├── cs224n_qa.json         # To be created after Checkpoint 2
  │       └── cs601_qa.json          # To be created after Checkpoint 2
  ├── scripts/
  │   ├── process_pdfs.py         # Step 1 & 2: PDF → slide images + text
  │   ├── generate_qa.py          # Step 4A: LLM-assisted QA draft generation
  │   └── annotate.py             # Step 4B: Human review tool (Streamlit/Gradio)
  ├── slideqa_dataset.py          # Step 5: Dataset loader
  └── requirements.txt
  ```

  **Important:** All scripts should accept a `--course` argument (e.g., `--course cs288`) so the same pipeline works for any course. The folder structure is designed so that adding Stanford and JHU later just means dropping PDFs into `raw_pdfs/cs224n/` and `raw_pdfs/cs601/` and re-running the same scripts with a different `--course` flag.

---

## What NOT to do in this session

- Don't build the retrieval pipeline or vector database yet (that's Session 3)
- Don't implement baselines yet (that's Session 2)
- Don't process Stanford or JHU slides yet — just create the empty folder structure for them so it's ready later
- Don't skip the human review step — LLM-generated QA pairs must be verified before they're considered final

---

## Success criteria for this session

By the end, I should have:
1. A working script that converts my 16 CS 288 lecture PDFs into organized slide images + extracted text (with empty folders ready for `cs224n` and `cs601`)
2. A QA generation script that produces LLM-drafted QA pairs for each slide
3. A review tool (Streamlit/Gradio) that lets me and my teammates approve, edit, or reject the LLM drafts
4. A dataset loader that can ingest the approved annotations and provide useful statistics
5. A clear, well-organized codebase that's ready for Session 2 (baselines)
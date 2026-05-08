# SlideQA — 4-Minute Presentation Outline

---

## Slide 1 — Title (~10 sec)

**SlideQA: A Multimodal Benchmark for Lecture Slide Question Answering**

Nathan McNaughton, Nicholas Eliacin & Shanaya Malik
UC Berkeley CS 288 — Spring 2026

---

## Slide 2 — The Problem (~40 sec)

**Headline:** Lecture slides are multimodal — but QA systems treat them as plain text.

**Content:**
- Slides contain: formulas, diagrams, charts, tables, spatial layout
- OCR / PDF text extraction **loses all of that structure**
- Example: a formula rendered as an image → extracted text = nothing

**Visual suggestion:** Side-by-side of a slide image (e.g., `slide_length_norm.png`) vs. the empty/garbled OCR output below it. Makes the problem immediately concrete.

---

## Slide 3 — The Gap (~30 sec)

**Headline:** No benchmark exists for this setting.

**Content:**
- Existing benchmarks: SlideVQA (business decks), ChartQA (isolated charts), InfographicVQA (infographics)
- None target **university-level technical lecture slides**
- None combine text, formulas, diagrams, tables, and layout in one benchmark

**Visual suggestion:** Simple 2-column table or icon grid:

| Benchmark | Domain | Visual? | Layout? |
|---|---|---|---|
| SlideVQA | Business | ✓ | ✗ |
| ChartQA | Charts only | ✓ | ✗ |
| InfographicVQA | Infographics | ✓ | ✗ |
| **SlideQA (ours)** | **NLP Lectures** | **✓** | **✓** |

---

## Slide 4 — SlideQA Benchmark (~30 sec)

**Headline:** 450 curated QA pairs across 3 courses, 5 categories.

**Content:**
- 3 courses: UC Berkeley CS 288, Stanford CS 224N, JHU CS 601.471
- 150 questions per course, 5 question categories:
  - Text-only · Image/Diagram · Table · Chart/Graph · Layout-Aware
- GPT-4o generated, manually reviewed via Streamlit annotation tool

**Visual suggestion:** Grouped bar chart or stacked bar showing category breakdown per course:

```
         CS 288   CS 601   CS 224N
Text       15       15       15
Image/Diag 60       59       57
Table      28       27       27
Chart/Graph 21      16       28
Layout     26       33       23
```

---

## Slide 5 — Key Idea: Retrieve Images, Not Text (~35 sec)

**Headline:** Skip text extraction entirely — embed and retrieve slide images directly.

**Content:**
- Standard RAG: PDF → OCR text → BM25 → LLM  ← throws away visuals
- **Our approach (ColPali RAG):** PDF → images → ColPali embeddings → top-k retrieval → GPT-4o with image context

**Visual suggestion:** Two-row pipeline diagram:

```
Standard RAG:
  PDF → [OCR] → text chunks → [BM25] → text → [LLM] → answer
                    ↑ visual info lost here

ColPali RAG (ours):
  PDF → slide images → [ColPali embed] → image index → [cosine search] → images → [GPT-4o] → answer
```

---

## Slide 6 — Systems We Compare (~20 sec)

**Headline:** We evaluate a spectrum from zero context to perfect context.

**Visual suggestion:** 4-box horizontal spectrum (no text beyond labels):

```
[Closed-Book]  →  [Text-Only BM25]  →  [ColPali RAG ⭐]  →  [Oracle VLM]
  no context       OCR text only       image retrieval      gold slide given
  (lower bound)                         (our method)        (upper bound)
```

---

## Slide 7 — Main Results (~40 sec)

**Headline:** ColPali RAG is 2× better than text-only. Gap to oracle = retrieval failures.

**Visual suggestion:** Grouped bar chart of average LLM-Judge scores (1–5 scale):

```
                Closed-Book   Text-Only   ColPali RAG   Oracle VLM
LLM-Judge avg:     1.98          1.81        3.62           4.57
```

Bar chart with ColPali RAG bar highlighted. Add annotation: "2× vs. text-only" and "22% of questions: retrieval miss → drives gap to oracle."

**Key numbers to call out verbally:**
- 1.81 (text-only) → **3.62** (ColPali RAG) → 4.57 (oracle)
- R@5 = 0.776: retrieval finds the right slide 78% of the time

---

## Slide 8 — Qualitative Example (~25 sec)

**Headline:** Text-only can't see the formula. ColPali can.

**Content:** Show the length normalization example side-by-side:

| | Answer |
|---|---|
| **Question** | What expression is used for length normalization? |
| **Text-only** | *"The context does not include information about a mathematical expression..."* |
| **ColPali RAG** | $p(\bar{x}) \propto \frac{1}{|\bar{x}|^\alpha} \sum \log p(x_i \mid x_1,\ldots,x_{i-1})$ ✓ |
| **Oracle VLM** | $p(\bar{x}) \propto \frac{1}{|\bar{x}|^\alpha} \sum \log p(x_i \mid x_1,\ldots,x_{i-1})$ ✓ |

**Visual:** Show `figures/slide_length_norm.png` alongside the table. The formula is only visible in the image — OCR gives nothing.

---

## Slide 9 — Takeaway (~10 sec)

**Headline:** Visual retrieval is essential for lecture slide QA.

**Content (minimal — just 3 lines):**
- Text-only is insufficient for slides with formulas, charts, and diagrams
- ColPali image retrieval closes most of the gap to perfect slide access
- Code & data: https://github.com/shanayamalik/cs288-sp26-slideQA

---

## Timing Guide

| Slide | Content | Time |
|---|---|---|
| 1 | Title | ~10 sec |
| 2 | Problem | ~40 sec |
| 3 | Gap / related work | ~30 sec |
| 4 | SlideQA benchmark | ~30 sec |
| 5 | Key idea (pipeline) | ~35 sec |
| 6 | Systems compared | ~20 sec |
| 7 | Main results | ~40 sec |
| 8 | Qualitative example | ~25 sec |
| 9 | Takeaway | ~10 sec |
| **Total** | | **~4:00** |

---

## Speaker Notes

- **Do not read the results table** — just call out the 3 numbers: 1.81 / 3.62 / 4.57.
- **Slide 8 is your strongest moment** — let the audience look at the slide image and the text-only failure response. Pause briefly.
- **Slides 3 and 4 can be cut** if you're running long — jump straight from problem to pipeline.
- The 30-sec QnA is ungraded; likely questions: "Why GPT-4o as judge?", "What's the hardest category?", "Did you try other VLMs?"

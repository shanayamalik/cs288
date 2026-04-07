# SlideQA Baseline Results

Evaluation uses **Exact Match** and **Token-F1** (SQuAD-style). Answers are short-form (≤10 words) for reliable automated scoring. Both baselines use GPT-4o via OpenRouter.

## Cross-Course Summary

| Course | N | Text-Only F1 | VLM F1 | VLM Advantage |
|---|---|---|---|---|
| CS 288 (Berkeley) | 75 | 0.130 | 0.358 | 2.75x |
| CS 601 (JHU) | 75 | 0.376 | 0.558 | 1.48x |
| CS 224N (Stanford) | 75 | 0.106 | 0.372 | 3.51x |

## UC Berkeley CS 288 (3 lectures, 75 QA pairs)

| Category | N | Text-Only EM | Text-Only F1 | VLM EM | VLM F1 |
|---|---|---|---|---|---|
| text_only | 7 | 0.143 | 0.272 | 0.000 | 0.535 |
| image_diagram | 43 | 0.000 | 0.115 | 0.023 | 0.294 |
| table | 11 | 0.000 | 0.063 | 0.000 | 0.368 |
| chart_graph | 7 | 0.000 | 0.138 | 0.000 | 0.519 |
| layout_aware | 7 | 0.000 | 0.175 | 0.000 | 0.392 |
| **Overall** | **75** | **0.013** | **0.130** | **0.013** | **0.358** |

## JHU CS 601.471 (3 lectures, 75 QA pairs)

| Category | N | Text-Only EM | Text-Only F1 | VLM EM | VLM F1 |
|---|---|---|---|---|---|
| text_only | 53 | 0.132 | 0.383 | 0.151 | 0.554 |
| image_diagram | 16 | 0.000 | 0.218 | 0.063 | 0.427 |
| table | 4 | 0.500 | 0.854 | 0.250 | 0.917 |
| layout_aware | 2 | 0.000 | 0.519 | 1.000 | 1.000 |
| **Overall** | **75** | **0.120** | **0.376** | **0.160** | **0.558** |

## Stanford CS 224N (3 lectures, 75 QA pairs)

| Category | N | Text-Only EM | Text-Only F1 | VLM EM | VLM F1 |
|---|---|---|---|---|---|
| text_only | 7 | 0.000 | 0.274 | 0.000 | 0.352 |
| image_diagram | 40 | 0.000 | 0.088 | 0.025 | 0.300 |
| table | 13 | 0.000 | 0.040 | 0.000 | 0.485 |
| chart_graph | 7 | 0.000 | 0.183 | 0.000 | 0.464 |
| layout_aware | 8 | 0.000 | 0.088 | 0.125 | 0.484 |
| **Overall** | **75** | **0.000** | **0.106** | **0.027** | **0.372** |

## Key Takeaways

- VLM consistently outperforms text-only across all three courses, confirming the benchmark requires genuine visual understanding.
- The VLM advantage is largest on CS 224N (3.51x) which has the most diagram/chart-heavy slides (40/75 image_diagram), and smallest on CS 601 (1.48x) which has older, more text-heavy PPT slides.
- CS 601's higher text_only category share (53/75 vs 7/75) explains why text-only BM25+LLM performs best there.
- The table and chart_graph categories show the largest per-category VLM improvement — these are where answers live in visual elements that text extraction misses.
- EM is low for both baselines because even short answers get paraphrased. Token-F1 is our primary metric.

## Reproducing Results

### CS 288
```bash
python slideqa/src/process_pdfs.py --course cs288
python slideqa/src/generate_qa.py --course cs288 --model openrouter/gpt-4o --rate-limit 1.5
python slideqa/src/curate_qa.py --course cs288 --target 75
python slideqa/src/run_baselines.py --course cs288 --rate-limit 1.0
```

### CS 601
The JHU slides were originally `.ppt`/`.pptx` and converted to PDF using LibreOffice:
```bash
brew install --cask libreoffice   # one-time
cd slideqa/data/raw_pdfs/cs601 && soffice --headless --convert-to pdf *.ppt *.pptx
```
Then:
```bash
python slideqa/src/process_pdfs.py --course cs601
python slideqa/src/generate_qa.py --course cs601 --model openrouter/gpt-4o --rate-limit 1.5 --lectures 1 2 3
python slideqa/src/curate_qa.py --course cs601 --target 75
python slideqa/src/run_baselines.py --course cs601 --rate-limit 1.0
```

### CS 224N
```bash
python slideqa/src/process_pdfs.py --course cs224n
python slideqa/src/generate_qa.py --course cs224n --model openrouter/gpt-4o --rate-limit 1.5 --lectures 1 2 3 4
python slideqa/src/curate_qa.py --course cs224n --target 75
python slideqa/src/run_baselines.py --course cs224n --rate-limit 1.0
```

Detailed per-question results are in `slideqa/data/results/`.

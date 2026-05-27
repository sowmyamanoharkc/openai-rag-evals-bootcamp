# Syllabus — OpenAI APIs · RAG · Evals (1 week)

A self-paced curriculum for Python developers. Each assignment is an independent, gradable artifact. All assignments in this repo are provided with starter code, reference solutions, design notes, and (for assignments 3, 4) walkthrough notebooks.

---



### 1. Setup & orientation
- Read this syllabus + `01-reading-list.md`.
- Set up the repo, install dependencies, smoke-test the API key.
- Complete **Assignment 1** (`assignment_01_hello_openai/`) — a 100-line summarizer CLI that prints token usage and cost. ~1–2 hours.
- Optional but recommended: complete **Assignment 2** (`assignment_02_structured_tools/`) — meeting-notes extractor with Pydantic + tool calling. ~3–4 hours.
- Skim `assignment_03_rag/ASSIGNMENT.md` so you know what's coming.

###  2. Assignment 3 part 1 — ingest + retrieve
- Implement `ingest.py` (chunking + embedding + storing in Chroma).
- Implement `retrieve.py` (top-k similarity search, returns chunks + metadata).
- Run a few manual queries; sanity-check that retrieved chunks look relevant.

### 3. Assignment 3 part 2 — generate + guardrails
- Implement `generate.py` (prompt template, citation format, "I don't know" guardrail).
- Wire up `main.py` end-to-end CLI.
- Try ~10 questions of your own; note where it fails. (You'll need these failures in Assignment 4.)

### 4. Assignment 4 part 1 — gold dataset
- Read `assignment_04_evals/ASSIGNMENT.md`.
- Curate or augment the gold Q&A set (`data/eval/gold_qa.jsonl`). Aim for ~20 cases including:
  - Easy (single-chunk answer)
  - Multi-hop (answer requires combining 2 chunks)
  - "Out of scope" (the answer is *not* in the docs — model should say "I don't know")
  - Adversarial (paraphrased, indirect, or contains a false premise)

### 5. Assignment 4 part 2 — metrics
- Implement `metrics_retrieval.py` (Recall@k, MRR).
- Implement `metrics_judge.py` (faithfulness + answer relevancy via LLM-as-judge with rubric).
- Implement `run_eval.py` to produce a results table.

### 6, Assignment 4 part 3 — comparison + CI
- Run the eval suite under **two configurations** (e.g., chunk size 256 vs. 1024, or top-k=3 vs. top-k=8).
- Wire the suite into `pytest` so a regression fails the build.
- Write `reports/comparison.md` with a 1-page conclusion.
- Re-read your own report. What's the most surprising result? Why?
- Look at `solution/` and `SOLUTION.md` for both assignments — diff them against your own.

---

## Assignment summaries

### Assignment 1 — Hello, OpenAI (`assignment_01_hello_openai/`)
CLI tool `summarize.py` that takes a `.txt` and a `--style` flag (`formal`/`casual`/`eli5`). Prints summary + token usage (local `tiktoken` count vs. `usage` ground truth) + estimated cost.

**Learning outcomes:** API auth, message roles, system prompts, `tiktoken`, basic cost reasoning.

### Assignment 2 — Structured Output + Tool Calling (`assignment_02_structured_tools/`)
Meeting-notes extractor: input transcript → JSON `{title, attendees, decisions, action_items}` validated by Pydantic. Adds one tool (`lookup_employee`) the model can call to enrich attendee fields. Implements a bounded tool-call loop and a single retry on validation failure.

**Learning outcomes:** Structured Outputs, function/tool calling, schema-driven design, retry/repair patterns.

### Assignment 3 — Mini RAG over your own docs (`assignment_03_rag/`)
Pure `openai` SDK + `chromadb`. Chunk → embed → retrieve → generate, with citations and a refusal guardrail. No frameworks.

**Learning outcomes:** chunking trade-offs, embeddings, top-k similarity, prompt design for groundedness.

### Assignment 4 — Evaluate your RAG (`assignment_04_evals/`)
Retrieval metrics (Recall@k, MRR), LLM-as-judge metrics (faithfulness, answer relevancy), and the same metrics expressed as `pytest` regression assertions. Compare two configurations side by side.

**Learning outcomes:** deterministic vs. judge-based metrics, gold dataset design, CI as the contract.

---

A practical, hands-on curriculum for Python developers. You will learn:

1. The **OpenAI API surface** that matters in production (Chat Completions, Structured Outputs, function/tool calling, embeddings).
2. How to build a **Retrieval-Augmented Generation (RAG)** system from scratch with the pure `openai` SDK — no LangChain or LlamaIndex magic.
3. How to **evaluate** an LLM application properly: deterministic retrieval metrics, LLM-as-judge metrics, and turning evals into regression tests in CI.

## Assignments included:

1. **Hello, OpenAI** — Chat Completions, system prompts, tokens & cost.
2. **Structured Output + Tool Calling** — Pydantic, `parse()`, bounded tool-call loop with one retry.
3. **Mini RAG** — chunk → embed → retrieve → generate, hand-rolled.
4. **Evals** — retrieval metrics + LLM-as-judge + `pytest` regression gates.

## Repository layout

```text
openai-rag-evals-bootcamp/
├── README.md                  # you are here
├── requirements.txt
├── Makefile                   # `make summarize`, `make extract`, `make ingest`, `make eval`, ...
├── .env.example               # OPENAI_API_KEY=...
├── .github/workflows/ci.yml   # CI: builds index, runs evals, runs pytest gates
├── docs/
│   ├── 00-syllabus.md         # full assignment curriculum
│   └── 01-reading-list.md     # curated study material
├── data/
│   ├── docs/                  # Acme Corp knowledge base (~12 markdown files)
│   ├── samples/
│   │   ├── article.txt        # input for Assignment 1 (summarizer)
│   │   └── transcript.txt     # input for Assignment 2 (notes extractor)
│   └── eval/
│       ├── gold_qa.jsonl       # 21 items — Assignments 3 & 4
├── assignment_01_hello_openai/
│   ├── ASSIGNMENT.md
│   ├── SOLUTION.md
│   ├── starter/summarize.py
│   └── solution/summarize.py
├── assignment_02_structured_tools/
│   ├── ASSIGNMENT.md
│   ├── SOLUTION.md
│   ├── starter/               # schema.py, tools.py, extract.py
│   └── solution/
├── assignment_03_rag/
│   ├── ASSIGNMENT.md          # learner-facing handout
│   ├── SOLUTION.md            # design notes, pitfalls, grading rubric
│   ├── starter/               # skeleton code with `TODO:` markers
│   └── solution/              # working reference implementation
├── assignment_04_evals/
│   ├── ASSIGNMENT.md
│   ├── SOLUTION.md
│   ├── example_deliverable/   # what a passing comparison.md looks like
│   ├── starter/
│   └── solution/
│       └── tests/             # pytest-based regression evals
└── notebooks/
    ├── 03-rag-walkthrough.ipynb
    ├── 04-evals-walkthrough.ipynb
```

---

## Getting started

**Read syllabus** and then set up env (as below) 

```bash
git clone <this-repo> openai-rag-evals-bootcamp
cd openai-rag-evals-bootcamp

python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and add your OPENAI_API_KEY
```

Smoke test:

```bash
python -c "from openai import OpenAI; print(OpenAI().models.list().data[0].id)"
```

---

## How to use this repo

For each assignment:

1. Read `ASSIGNMENT.md` end to end.
2. Work in `starter/` — fill in every `TODO:` marker.
3. Run your code against the sample data in `data/`.
4. Once finished, compare against `solution/` and read `SOLUTION.md` for the *why* behind each choice.
5. Optionally walk through `notebooks/0X-*.ipynb` for a guided commentary version.

---
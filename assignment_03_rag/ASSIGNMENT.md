# Assignment 3 — Mini RAG over your own docs

**Stack:** Pure `openai` SDK + `chromadb` (no LangChain or LlamaIndex).
**Prerequisites:** Python 3.10+, comfort with the OpenAI Chat Completions API.

---

## What you will build

A command-line Q&A assistant over Acme Corp's internal policy documents (`data/docs/`). Given a question, it should:

1. Retrieve the most relevant document chunks using vector similarity.
2. Generate a grounded answer that cites its sources.
3. Politely refuse (return *"I don't know based on the provided docs."*) when no chunk is relevant enough.

By the end you will have built every piece of a RAG pipeline yourself, with no framework hiding the moving parts.

---

## Learning outcomes

After completing this assignment you will be able to:

- Explain why naive prompt-stuffing of the entire KB into the model is a bad idea.
- Choose a chunking strategy (and articulate the trade-offs).
- Use OpenAI's `text-embedding-3-small` to embed text and store/query embeddings in a vector DB.
- Implement top-k similarity retrieval with metadata.
- Design a RAG prompt that **forces** grounded answers and citations.
- Implement a confidence-based "I don't know" guardrail.

---

## What's provided

```text
assignment_03_rag/
├── ASSIGNMENT.md          # this file
├── SOLUTION.md            # design notes — read AFTER attempting yourself
├── starter/
│   ├── ingest.py          # skeleton with TODOs
│   ├── retrieve.py
│   ├── generate.py
│   └── main.py
└── solution/              # reference implementation (peek only when stuck)
data/
├── docs/                  # 12 Acme Corp markdown policy files
└── eval/gold_qa.jsonl     # used in Assignment 4 — ignore for now
```

A walkthrough notebook (`notebooks/03-rag-walkthrough.ipynb`) is provided for guided commentary.

---

## Tasks

### Task 1 — Ingest (`starter/ingest.py`)

Load every `.md` file in `data/docs/`, split it into chunks, embed each chunk, and store the chunks in a local Chroma collection.

Requirements:

1. Implement `load_documents(docs_dir: str) -> list[Document]` where `Document` is a small dataclass with `path`, `content`, and any other metadata you want.
2. Implement `chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]`. **Use a recursive character splitter** that prefers paragraph breaks → line breaks → sentences → words. *Do not* simply split on a fixed character count — that breaks tables and headings.
3. Implement `embed_chunks(chunks: list[str]) -> list[list[float]]` using `text-embedding-3-small`. Batch your requests (the embeddings endpoint accepts a list of strings).
4. Persist to a Chroma collection at `./chroma_db`. Each document chunk's metadata must include at least `source_path` and `chunk_index`.
5. The script should be **idempotent** — running it twice should not duplicate data. Either delete-and-rebuild, or use deterministic chunk IDs.

Run it:

```bash
python -m assignment_03_rag.starter.ingest --chunk-size 500 --chunk-overlap 50
```

You should see ~50–100 chunks created.

### Task 2 — Retrieve (`starter/retrieve.py`)

Implement a `retrieve(query: str, k: int = 5) -> list[RetrievedChunk]` function that returns the top-k chunks by cosine similarity, including each chunk's text, similarity score, and metadata.

Sanity check: print the top 3 chunks for the question *"How much PTO do I get?"*. The top hit must come from `02-leave-policy.md`.

### Task 3 — Generate (`starter/generate.py`)

Implement `answer(question: str, retrieved: list[RetrievedChunk]) -> Answer` where `Answer` is a dataclass with `text`, `citations` (list of `source_path` strings), and `is_grounded` (bool).

Requirements:

1. Build a prompt with a clear system message instructing the model to:
   - Only use the provided context.
   - Cite each fact with the source filename in the format `[source: <filename>]`.
   - Respond with exactly *"I don't know based on the provided docs."* when the context is insufficient.
2. Pass the retrieved chunks as numbered context (`[1] ...`, `[2] ...`).
3. Use `gpt-4o-mini` with `temperature=0`.
4. Implement a **guardrail**: if the *maximum* similarity score across retrieved chunks is below a threshold (start at `0.3`), short-circuit and return the "I don't know" response without calling the model.

### Task 4 — End-to-end CLI (`starter/main.py`)

Wire it together as a CLI:

```bash
python -m assignment_03_rag.starter.main "How much PTO do I get?"
python -m assignment_03_rag.starter.main "What is Acme's stock ticker?"   # should refuse
```

Output format:

```text
Q: How much PTO do I get?

A: Full-time employees accrue 22 working days of PTO per calendar year, accrued at 1.83 days per month [source: 02-leave-policy.md].

Sources:
  - 02-leave-policy.md (chunk 0, score 0.84)
  - 02-leave-policy.md (chunk 1, score 0.71)
```

### Task 5 — Manual smoke test

Run **at least 10 questions of your own** against your system. For each, write down:

- Did it answer correctly?
- Were the citations correct?
- If it failed, was the failure in **retrieval** (wrong chunks) or **generation** (right chunks, wrong answer)?

You will use this list of failures as inspiration for your gold dataset in Assignment 4. Save your notes in `assignment_03_rag/manual_smoke_test.md`.

---

## Stretch goals (optional, distinction-grade)

- **Hybrid search:** add BM25 (`rank-bm25`) and combine with the dense scores via reciprocal rank fusion.
- **Query rewriting:** before retrieval, ask the model to expand the user's question into 2–3 paraphrases; retrieve with all and merge.
- **Re-ranking:** retrieve top-20 with vectors, then re-rank to top-5 using a cross-encoder or an LLM-as-judge call.
- **HyDE:** instead of embedding the question, ask the model to draft a hypothetical answer and embed *that* — often improves retrieval on short queries.

---

## Constraints and rules

- **Do not** use LangChain, LlamaIndex, Haystack, or any RAG framework. The point of this assignment is to understand the primitives.
- **Do** use the official `openai` Python SDK and `chromadb`.
- **Do not** load the full document set into the model context. The whole point is retrieval.
- **Do** keep secrets out of source — use `.env`.

---

## Deliverables

When done, your `starter/` directory should contain a working implementation. Submit:

1. Your code (all four files filled in).
2. `manual_smoke_test.md` with your 10+ test questions and observations.
3. A short note (5–10 lines) at the top of `manual_smoke_test.md` describing the chunking parameters you settled on and why.

A grader will run your code against `data/docs/` and a held-out question set.

---

## Hints (read only when stuck)

<details>
<summary>Hint 1 — Chunking</summary>

A reasonable starting point is `chunk_size=500` characters with `chunk_overlap=50`. Try recursive splitting on `["\n\n", "\n", ". ", " "]` in that order. **Don't worry about token-perfect splits;** character-based is fine and avoids tokenizer round-trips.
</details>

<details>
<summary>Hint 2 — Chroma quickstart</summary>

```python
import chromadb
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="acme_docs")
collection.add(ids=[...], documents=[...], embeddings=[...], metadatas=[...])
results = collection.query(query_embeddings=[...], n_results=5)
```

`results["distances"]` are *cosine distances* (lower = closer). Convert to similarity with `similarity = 1 - distance`.
</details>

<details>
<summary>Hint 3 — Why the guardrail threshold matters</summary>

Without a threshold, the model will *always* try to answer — even on out-of-scope questions — by stretching whatever chunks it received. Your "out of scope" eval cases in Assignment 4 will fail until you add this. Start at 0.3 and tune later.
</details>

# Assignment 3 — Solution Notes

This is the *why* behind the code in `solution/`. Read this **after** you've attempted the assignment yourself — otherwise you'll cheat yourself out of the most valuable lessons.

---

## Architecture at a glance

```text
                    ingest.py
docs/*.md ──► load ──► chunk ──► embed ──► Chroma persistent collection
                                            │
                                            ▼
                       retrieve.py: query embedding → top-k chunks
                                            │
                                            ▼
                generate.py: chunks → prompt → gpt-4o-mini → grounded answer
```

Three modules, three concerns. Keep it that way — when something breaks, you want to know whether it's an ingest bug, a retrieval bug, or a generation bug. Mixing them makes debugging miserable.

---

## Design decisions and the reasoning

### 1. Recursive character chunking, not token-based

We split on `["\n\n", "\n", ". ", " "]` in order. **Why character-based and not token-based?**

- Character-based is dependency-light (no `tiktoken` round-trip per chunk) and fast.
- Token-aware splitting matters at the *edges* of the model's context window (e.g., for long-context summarization). For our 500-character chunks, the difference between 100 and 130 tokens is irrelevant.

**Why recursive?** A flat character split breaks tables, headings, and bullet lists at arbitrary points, which destroys retrieval quality. Trying paragraph → line → sentence → word respects natural boundaries first.

### 2. Chunk size 500 / overlap 50 is a starting point, not a fact of nature

Chunk size is a **trade-off**:

| Smaller chunks (~200 chars) | Larger chunks (~1500 chars) |
|---|---|
| More precise retrieval (the chunk is "about" one thing). | More context per hit (multi-paragraph reasoning is easier). |
| Higher chance of fragmenting a fact across chunks. | Higher chance the right answer is buried in noise. |
| More chunks → higher embedding cost, more index storage. | Fewer chunks → cheaper, but each chunk is "fuzzier" semantically. |

Start at 500/50 because the docs are short and well-structured. **Assignment 4 will have you compare two configurations empirically** — that's where you'll discover that "best chunk size" is dataset-dependent.

### 3. Embedding model: `text-embedding-3-small`

- 1536 dims, $0.02 per 1M tokens. The whole knowledge base costs **fractions of a cent** to index.
- `-large` is 3072 dims and ~6× more expensive. Use it only if you've shown `-small` is the bottleneck via evals (Assignment 4).

### 4. Cosine similarity, not Euclidean

We pass `metadata={"hnsw:space": "cosine"}` when creating the collection. OpenAI embeddings are normalized for cosine similarity; using Euclidean works *most* of the time but is theoretically wrong here.

**Important:** Chroma returns *cosine distance*, not similarity. The conversion is `similarity = 1 - distance`. (For normalized vectors, `cosine_distance ∈ [0, 2]`, so similarity is roughly `[-1, 1]` but usually in `[0, 1]` for related text.)

### 5. Idempotent ingest

`build_index` deletes-and-recreates the collection. The alternative is deterministic IDs + upsert, which is friendlier for incremental ingests but more code. For a learning exercise, delete-and-rebuild is honest about what's happening.

### 6. Retrieval: top-k similarity, no re-ranking

Top-5 is the default. We sort the returned chunks by similarity descending — Chroma already does this, but we don't rely on it (defensive coding).

**Why not re-rank?** Adding a re-ranker (e.g., Cohere Rerank or an LLM-as-judge call) almost always improves retrieval quality but adds latency and cost. The cost-benefit only makes sense once you've measured a problem with vanilla top-k. *Measure first* — that's the point of Assignment 4.

### 7. Prompt design: explicit, not clever

The system prompt is deliberately **bossy**:

- "Every factual claim must include an inline citation."
- "If the context does not contain the answer, respond with EXACTLY ..."
- "Do NOT use prior knowledge."

Vague prompts ("answer using the context") let models drift into using parametric knowledge when retrieval misses. The explicit refusal string lets us programmatically detect grounding (`text == REFUSAL_TEXT`) instead of trying to parse "I'm not sure but..." answers.

### 8. The similarity threshold is a *cheap* guardrail

Before calling the model at all, if `max(similarity) < 0.30`, we return the refusal text. This:

- Saves a model call on questions with no relevant context.
- Forces "I don't know" behavior on out-of-scope questions, which the model alone is bad at (it will try to be helpful).

The threshold value is empirical. **Tune it using the eval suite from Assignment 4** — too high and you reject answerable questions; too low and the model hallucinates from irrelevant chunks.

### 9. `temperature=0`

For RAG over a fixed knowledge base, randomness in the answer is a bug, not a feature. `temperature=0` gives near-deterministic outputs — important for evals (you want a metric on stable behavior).

---

## Common pitfalls (and how to recognize them)

| Symptom | Likely cause |
|---|---|
| Top-1 chunk is correct but the answer is wrong | Generation prompt isn't strict enough; model is paraphrasing wrong, or you're not passing the chunk text in cleanly. |
| Top-1 chunk is wrong | Retrieval problem. Inspect the embedding of your query vs. the embedding of the gold chunk. Often a chunking issue (the answer was split across chunks). |
| Citations missing or hallucinated | Prompt isn't enforcing the format strongly enough, or `temperature > 0`. |
| "I don't know" on answerable questions | Threshold too high, or chunk size too small for the question's scope. |
| "I don't know" never fires | No threshold guardrail, or threshold too low. The model will *always* try to answer if asked. |
| Same question gives different answers | `temperature > 0`, or two duplicate chunks were inserted (check ingest idempotency). |

---

## Stretch goals — when each pays off

- **Hybrid search (BM25 + dense):** wins on queries with rare terms or specific identifiers (filenames, employee IDs, error codes). Dense embeddings under-weight rare tokens.
- **Query rewriting:** wins on short / vague queries ("PTO?"). Less helpful when queries are already specific.
- **Re-ranking with a cross-encoder:** wins when top-20 reliably contains the answer but top-3 doesn't. Add this when retrieval recall is high but precision is low.
- **HyDE:** wins on very short queries or when the query language differs from the document language (e.g., users ask in their words, docs use jargon).

**Don't add these until evals tell you the base system is the bottleneck.** Adding everything blindly often makes things worse and always makes things slower.

---

## Grading rubric (out of 100)

| Category | Points | What we look for |
|---|---|---|
| Ingest correctness | 15 | Recursive chunking, batched embeddings, idempotent. |
| Retrieve correctness | 15 | Top-k by similarity, metadata returned, similarity (not distance). |
| Generate correctness | 20 | Strict system prompt, citation format, refusal handling, temp=0. |
| Guardrail | 10 | Threshold short-circuits the model call. |
| Code quality | 15 | Clean modules, type hints, no dead code. |
| Smoke test report | 10 | 10+ thoughtful questions, retrieval-vs-generation failure analysis. |
| Reasoning notes | 15 | Brief but specific justification for chunk size / threshold / model choice. |

Distinction (90+) requires at least one stretch goal implemented and a written explanation of *which problem* it solved on which queries.

---

## What to read after

Once your RAG works:

1. *Lost in the Middle* (Liu et al., 2023) — read the abstract and Figure 2. Then look at how *you* ordered chunks in the prompt.
2. Pinecone's *Chunking strategies* article — compare to your decisions.
3. Hamel Husain, *Your AI Product Needs Evals* — the perfect bridge to Assignment 4.

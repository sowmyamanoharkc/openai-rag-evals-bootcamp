# Reading List

Tight, opinionated reading list for Python developers. Skip anything you've already seen — the goal is to fill *gaps*, not collect bookmarks.

---

## Core (read these first)

### OpenAI APIs
1. **OpenAI Platform Docs** — https://platform.openai.com/docs
   - *Quickstart* (skim if familiar)
   - *Text generation* — message roles, parameters
   - *Structured Outputs* — JSON schema enforcement
   - *Function calling* — tool use end-to-end
   - *Embeddings* — `text-embedding-3-small` vs `-large`
2. **OpenAI Cookbook** — https://github.com/openai/openai-cookbook
   - `examples/How_to_call_functions_with_chat_models.ipynb`
   - `examples/Question_answering_using_embeddings.ipynb`
   - `examples/How_to_count_tokens_with_tiktoken.ipynb`

### RAG
3. Lewis et al. (2020), *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks* — https://arxiv.org/abs/2005.11401
   *Read sections 1–3. Skim the rest.*
4. Liu et al. (2023), *Lost in the Middle: How Language Models Use Long Contexts* — https://arxiv.org/abs/2307.03172
   *Critical for understanding why ordering and chunk count matter.*
5. Pinecone Learning Center — https://www.pinecone.io/learn/
   - *Chunking strategies for LLM applications*
   - *Hybrid search*

### Evals
6. Hamel Husain, *Your AI Product Needs Evals* — https://hamel.dev/blog/posts/evals/
   *The single most important blog post on this list.*
7. Liu et al. (2023), *G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment* — https://arxiv.org/abs/2303.16634
   *The justification for LLM-as-judge done well: rubrics, chain-of-thought, calibration.*
8. **Ragas docs** — https://docs.ragas.io
   - Read the *faithfulness*, *answer relevancy*, *context precision*, *context recall* metric pages.
9. **OpenAI Evals framework** — https://github.com/openai/evals — README + `examples/`.

---

## Deeper / supplementary

### RAG techniques
- **HyDE** (Gao et al., 2022) — *Hypothetical Document Embeddings*. https://arxiv.org/abs/2212.10496
- **Multi-query retrieval** — generating query variants before retrieval.
- **Re-ranking with cross-encoders** — Cohere Rerank, BGE reranker.
- DeepLearning.AI — *Building and Evaluating Advanced RAG* (free short course).

### Eval techniques
- Eugene Yan, *Evaluation & Hallucination Detection for Abstractive Summaries* — https://eugeneyan.com/writing/abstractive/
- Eugene Yan, *Patterns for Building LLM-based Systems & Products* (the "Evals" section) — https://eugeneyan.com/writing/llm-patterns/
- **TruLens**, **DeepEval** — alternatives to Ragas; scan READMEs for comparison.

### Tooling
- `tiktoken` — tokenization. (You will use this.)
- `pydantic` v2 — Structured Outputs ergonomics.
- `chromadb` — local vector DB used in Assignment 3.
- `rank-bm25` — sparse retrieval, used in the hybrid-search stretch goal.

---

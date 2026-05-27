# RAG Configuration Comparison — Acme Policy Assistant

**Author:** *(your name)*
**Date:** *(YYYY-MM-DD)*
**Eval set:** `data/eval/gold_qa.jsonl` @ commit `e1f3a8c` (21 items: 10 easy / 5 multihop / 3 adversarial / 3 out-of-scope)

> Note: this file is an **example deliverable**, not real run output. The numbers below are illustrative — yours will differ. Use this as a template for the depth and structure expected, not as a target.

---

## 1. Configurations under test

| | Config A — *baseline* | Config B — *large chunks* |
|---|---|---|
| chunk size (chars) | 500 | 1000 |
| chunk overlap | 50 | 100 |
| retriever top-k | 3 | 8 |
| similarity threshold | 0.30 | 0.30 |
| chat model | `gpt-4o-mini` | `gpt-4o-mini` |
| embedding model | `text-embedding-3-small` | `text-embedding-3-small` |
| judge model | `gpt-4o-mini` | `gpt-4o-mini` |
| temperature | 0 | 0 |

Both runs use the same gold dataset, prompt template, and eval harness. Re-ingest is performed before each run because chunk size requires re-embedding.

Reports: `reports/eval_20260503T091200Z_baseline.json`, `reports/eval_20260503T093400Z_large_chunks.json`.

---

## 2. Headline results

| Metric | Config A | Config B | Δ (B − A) | Verdict |
|---|---:|---:|---:|---|
| Recall@1 | 0.78 | 0.83 | +0.05 | B better |
| Recall@3 | 0.94 | 0.94 | 0.00 | tie |
| Recall@k *(at the run's top-k)* | 0.94 (k=3) | 0.94 (k=8) | 0.00 | tie |
| MRR@k | 0.86 | 0.84 | −0.02 | A better |
| Mean faithfulness (1–5) | 4.71 | 4.43 | −0.28 | **A better** |
| Mean answer relevancy (1–5) | 4.62 | 4.52 | −0.10 | A better |

**Winner overall: Config A (baseline).**
Config B nudged Recall@1 upward but lost ground on faithfulness — and faithfulness is the metric that maps most directly to user-trust failures in production.

---

## 3. Per-category breakdown

| Category | n | A — Recall@k | B — Recall@k | A — Faithfulness | B — Faithfulness | A — Relevancy | B — Relevancy |
|---|---:|---:|---:|---:|---:|---:|---:|
| easy | 10 | 1.00 | 1.00 | 4.90 | 4.80 | 4.90 | 4.80 |
| multihop | 5 | 0.80 | 0.80 | 4.60 | 4.20 | 4.40 | 4.40 |
| adversarial | 3 | 1.00 | 1.00 | 4.33 | 3.67 | 4.00 | 4.00 |
| out_of_scope | 3 | n/a | n/a | 5.00 | 5.00 | 5.00 | 5.00 |

**Where they differ most:** the **adversarial** category. Faithfulness drops 0.66 between A and B (4.33 → 3.67). Inspecting the per-item judge reasoning, the failure pattern is:

> *adversarial-01* — "Acme rotates passwords every 90 days, right?"
>
> Config A's answer (top-3 chunks): correctly contradicts the false premise — *"No, Acme does NOT mandate fixed-schedule rotation. The 90-day rule applies only to service accounts."*
>
> Config B's answer (top-8 chunks): includes the same correct contradiction **plus** an extra paragraph paraphrasing breadth-of-policy rules from `08-data-classification.md`, which the judge flagged as drifting beyond the question. Faithful to the chunks, but a stretch on the question — and the relevancy score moved similarly.

---

## 4. Hypothesis explaining the gap

Bigger top-k provides more context but also more *opportunity* for the model to weave in tangential material. Larger chunks compound this: each chunk now contains rules from multiple sub-sections, so the model occasionally pulls in adjacent rules that share keywords with the question but don't actually apply.

In short: **on this dataset, retrieval was already saturated at top-3 with chunk size 500.** Adding more context and more chunks brought no recall benefit and a measurable cost in faithfulness. This matches the *Lost in the Middle* finding that more context isn't free.

---

## 5. Other observations

- **Out-of-scope behavior:** identical across configs (all 3 items refused correctly). The threshold guardrail does its job; the chunk-size change didn't shift it past the threshold for either OOS query (top-similarity was ≤ 0.20 in both runs).
- **Cost:** Config B used ~3× the input tokens at generation time and ~2× at embedding (re-ingest). API spend per run: A ≈ \$0.07, B ≈ \$0.18.
- **Latency:** end-to-end p50 per query: A 1.4s, B 2.6s — driven mostly by the 2× generation context size.
- **Judge noise:** I ran Config A twice. Mean faithfulness moved from 4.71 → 4.65 across runs (Δ 0.06). My Δ between A and B (0.28) is meaningfully larger than the noise floor, so the comparison is real.

---

## 6. Recommendation

**Stay on Config A.** The Recall@1 gain on B does not pay for the faithfulness loss on adversarial cases, the 2× latency, or the 2.5× cost.

---

## 7. Next experiment

Try a *third* configuration: **chunk size 500 (A) + retriever top-3 + cross-encoder re-ranker on top-10 → top-3**. Hypothesis: the re-ranker preserves A's faithfulness while lifting Recall@1 by reordering the same dense-retrieval candidates. Budget: 2 hours, ~\$0.20 in API spend. Success criterion: Recall@1 ≥ 0.85 with no regression on faithfulness.

If that fails, the next thing I'd try is **query rewriting (HyDE-style)** on the multihop category specifically — that's the only category where Recall@k is < 1.0 for either config, so it's the obvious next bottleneck.

---

## 8. Pytest output

```text
$ pytest assignment_04_evals/solution/tests/ -v
============================= test session starts ==============================
collected 5 items

assignment_04_evals/solution/tests/test_regression.py::test_overall_recall_at_5      PASSED
assignment_04_evals/solution/tests/test_regression.py::test_easy_category_recall_perfect PASSED
assignment_04_evals/solution/tests/test_regression.py::test_overall_faithfulness     PASSED
assignment_04_evals/solution/tests/test_regression.py::test_overall_answer_relevancy PASSED
assignment_04_evals/solution/tests/test_regression.py::test_out_of_scope_refuses     PASSED

============================== 5 passed in 0.09s ===============================
```

# Assignment 4 — Solution Notes

This is the *why* behind the eval harness in `solution/`. Read it after attempting the assignment.

---

## What "evaluation" actually means here

LLM apps differ from classical software in one key way: there is **no single ground-truth output** for most inputs. So "evaluation" is fundamentally about **measuring distributions of behavior** over a curated dataset, not about asserting a single expected return value.

Three distinct levels of evaluation, each with different cost / fidelity trade-offs:

| Level | What it measures | Cost | Fidelity |
|---|---|---|---|
| **Retrieval metrics** | Did the right chunks come back? | Free, deterministic. | High — direct measurement. |
| **Reference-based generation metrics** (e.g., exact match, F1) | Does the answer match a reference? | Free. | Brittle — paraphrases break it. |
| **LLM-as-judge** | Does the answer satisfy human-written rubric criteria? | A model call per item per metric. | Medium — noisy but flexible. |

We use **retrieval metrics + LLM-as-judge** in this assignment. We skip reference-based generation metrics deliberately because they're misleading on free-form responses.

---

## Architecture

```text
gold_qa.jsonl ──► run_eval.py ──► (calls into Assignment 3 RAG)
                       │
                       ├─► metrics_retrieval.py   # Recall@k, MRR
                       │
                       ├─► metrics_judge.py        # faithfulness, answer relevancy
                       │
                       └─► reports/eval_<ts>_<config>.json
                                  │
                                  └─► tests/test_regression.py (pytest)
```

`run_eval.py` is the *only* file that knows about both the RAG pipeline and the metrics. The metrics modules know nothing about how the answers were produced — they just take items as dicts and return scores. This separation matters for two reasons:

1. **You can swap the RAG implementation** (e.g. a LangChain version) without changing the metrics.
2. **You can re-score from saved JSON reports** without re-running the RAG pipeline. Iterating on a judge prompt no longer costs new RAG calls.

---

## Design decisions

### 1. Why `recall@k` and not `precision@k`?

For a Q&A system, what matters is: **did the answer-bearing chunk make it into the context window?** That's recall. Precision (how many of the top-k were relevant) is a secondary concern — extra noise hurts but isn't fatal.

We track Recall@1, Recall@3, and Recall@k in the report so you can see how rapidly recall climbs. If Recall@1 is far below Recall@5, your retriever is *almost* right but ordering is bad — a re-ranker is the obvious fix.

### 2. Why exclude `out_of_scope` items from retrieval metrics?

They have no expected sources; "correct retrieval" is undefined. The behavior we *do* care about — *did the system refuse?* — is captured by:

- The `answer_relevancy_score` rubric explicitly rewards a refusal on OOS questions.
- A direct pytest assertion (`test_out_of_scope_refuses`) on the answer text.

Trying to mash this into recall@k makes the metric harder to interpret.

### 3. Why LLM-as-judge for faithfulness and relevancy?

You *cannot* reliably measure these with string matching. A correct answer can be phrased a hundred ways, and a faithful summary can use words that aren't in the source chunks. LLM-as-judge handles this — at the cost of being **noisy** and **biased**.

We mitigate the bias and noise with three techniques from the G-Eval paper:

1. **Rubric in the system prompt.** A 1–5 scale with explicit anchors at each level. Vague rubrics produce vague scores.
2. **Reasoning before score, enforced by schema.** Putting reasoning first makes the model think before committing to a number — measurably improves agreement with humans.
3. **`temperature=0`.** Deterministic-ish scoring. We still recommend rerunning the suite ≥2× to estimate variance (stretch goal).

### 4. Structured Outputs, not regex parsing

The judge returns `JudgeOutput(reasoning, score)` enforced by Pydantic. Without Structured Outputs, you'd hand-write a regex like `r"Score:\s*(\d)"` and pray. This is fragile and silently wrong — when parsing fails, you get random fallback scores polluting your metric.

Structured Outputs **fail loudly**. If the model can't satisfy the schema, you find out immediately.

### 5. Special-cases in the judges, not in the rubric

Both judge functions have early returns:

```python
if answer_text == REFUSAL_TEXT:
    return JudgeResult(score=5, reasoning="Refusal — vacuously faithful.")
```

Why not let the rubric handle it? Because:

1. Calling the LLM to score "did it say *exactly* this string?" is wasteful.
2. The model occasionally drifts and scores refusals as 3 or 4 ("could have tried harder"). That bias propagates to your aggregate.

Hard-coding the deterministic case keeps the metric honest and saves money.

### 6. Same model for answering and judging — known limitation

We use `gpt-4o-mini` for both the RAG generation and the judging (configurable via `OPENAI_JUDGE_MODEL`). This is **the most common LLM-as-judge bias** — same-family models systematically over-rate each other. We document it in the assignment, and the recommended remediation is to use a *stronger* judge (e.g., `gpt-4o`) or a *different family* (Claude, Gemini) for high-stakes evals.

For learning purposes, same-model is fine: it teaches the methodology without quadrupling cost.

### 7. Why pytest for the regression layer?

LLM evals are unfamiliar to most developers. **Pytest is familiar to all of them.** Wiring evals into pytest means:

- They run in your existing CI pipeline with no new tooling.
- A failure shows up in the same dashboard as unit-test failures.
- You can express *behavior* assertions (the OOS refusal test) right next to the *metric* assertions.

The thresholds (0.85 recall, 4.0 mean faithfulness, 4.0 mean relevancy) are starting points. Tune them per-app based on the cost of false negatives in your domain.

### 8. Per-category metrics matter more than overall

The aggregate metric can hide regressions. If you ship a change that:

- Improves `easy` from 95% → 100% (+5%),
- Degrades `multihop` from 60% → 40% (-20%),

The overall metric barely moves but you've shipped a regression. Always inspect category breakdowns.

The pytest suite enforces `recall_at_k == 1.0` on the `easy` subset specifically *because* it's the canary — if you can't get easy questions right, nothing else matters.

---

## Common pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| Running judge with non-zero temperature | Same items score differently across runs | `temperature=0` everywhere |
| Asking judge for a score before reasoning | Scores cluster around 4 | Schema must put `reasoning` first |
| Using the same model as judge and answerer (silently) | Inflated scores; weak correlation with reality | Use a stronger model for judging, OR document and accept |
| Eval set < 20 items | Metrics swing wildly run-to-run | Aim for ≥30; we ship 21 to keep this assignment cheap |
| Out-of-scope items not in eval set | Refusal behavior never measured; will silently break | We provide 3 OOS items; add more to your domain set |
| Eval items written *after* seeing model output | Massive overfit; the test set is no longer "held out" | Write items first, run model second |
| Not re-ingesting between configs | Comparison meaningless | The harness's chunk size / threshold are runtime params; **chunk size requires a re-ingest** |

---

## What a good comparison report looks like

A passing comparison (`reports/comparison.md`) should be tight — about a page — and include:

1. **Configurations:** exact parameters for A and B (chunk size, top-k, threshold, model versions, dataset commit hash).
2. **Metrics table:** all four primary metrics, side by side, plus per-category for whichever metric moved most.
3. **Winner & why:** one paragraph. Don't bury the lede.
4. **Surprise:** the *interesting* finding — usually a metric that moved opposite to your expectation.
5. **Next experiment:** one concrete change with a hypothesis.

Bad comparison reports just dump numbers. Good ones make a *recommendation*.

---

## Stretch goal commentary

- **Citation correctness** is high-value because it directly measures hallucinated sources, which cause real user-trust failures. Implementing it as a third judge metric is well worth ~30 minutes.
- **Confidence intervals via 3× repeats:** the punchline is usually that mean scores have ±0.2 noise on a 1–5 scale, so changes < 0.2 should not be considered real.
- **Cost & latency tracking:** a simple decorator around the OpenAI client. Once you measure it you'll discover that the judges cost 2–3× more than the RAG itself — useful when justifying a cheaper judge model later.
- **Ragas integration:** a useful sanity check. If your hand-rolled judge agrees with Ragas, both are probably reasonable; if they disagree consistently, you've found a calibration issue worth investigating.

---

## Grading rubric (out of 100)

| Category | Points | What we look for |
|---|---|---|
| Retrieval metrics | 15 | Correct Recall@k and MRR, OOS handling. |
| Faithfulness judge | 20 | Rubric clarity, reasoning-before-score, refusal handling. |
| Relevancy judge | 15 | Same, including OOS-refusal scoring. |
| Eval harness | 15 | Reproducible reports with timestamp, full per-item data. |
| Two-config comparison | 15 | Both runs reproducible, metrics differ as expected. |
| Comparison write-up | 10 | Specific, recommends next action, identifies a surprise. |
| Pytest regression suite | 10 | All thresholds asserted; OOS behavior asserted directly. |

Distinction (90+) requires **at least one** stretch goal **and** a comparison report with at least one non-obvious finding (e.g., "smaller chunks improved recall but degraded faithfulness — likely because each chunk no longer contained the qualifying clauses for the rules").

---

## What to read after

- *G-Eval* paper, in depth — you've seen it applied; now read the methodology.
- Ragas docs — compare its metric definitions to yours.
- Eugene Yan, *Evaluation & Hallucination Detection* — for production-scale techniques.


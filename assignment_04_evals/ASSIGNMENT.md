# Assignment 4 — Evaluate your RAG

**Stack:** Pure `openai` SDK + `pytest`.
**Prerequisites:** A working solution for Assignment 3.

> "Without evals, every decision you make about your LLM app is vibes."
> — Hamel Husain, paraphrased.

---

## What you will build

A reproducible evaluation harness for the RAG system you built in Assignment 3, with three layers:

1. **Deterministic retrieval metrics** — Recall@k, MRR — to measure whether the right chunks come back at all.
2. **LLM-as-judge metrics** — *faithfulness* and *answer relevancy* — to measure whether the generated answer is actually any good.
3. **Regression tests** — `pytest` cases that fail the build if metrics drop below thresholds.

You will then **run the suite under two RAG configurations** and produce a 1-page comparison report.

---

## Why this matters

A RAG system that "looks good in demos" can be silently broken in 30% of cases. The only way to know is to measure. This assignment teaches the *muscle memory* of:

- Curating a small but pointed gold dataset.
- Using deterministic metrics where you can.
- Using LLM-as-judge metrics where you must — and being honest about their limits.
- Wiring metrics into CI so a regression *actually fails the build*, not just shows up as a number in a slack message no one reads.

---

## What's provided

```text
data/eval/gold_qa.jsonl       # 20 graded Q&A pairs (you may extend this)
assignment_04_evals/
├── ASSIGNMENT.md             # this file
├── SOLUTION.md               # design notes
├── starter/
│   ├── metrics_retrieval.py
│   ├── metrics_judge.py
│   ├── run_eval.py
│   └── tests/
│       └── test_regression.py
└── solution/                 # reference implementation
```

A walkthrough notebook (`notebooks/04-evals-walkthrough.ipynb`) is provided.

---

## The gold dataset format

`data/eval/gold_qa.jsonl` is a JSON-Lines file. One example per line:

```json
{
  "id": "easy-01",
  "question": "How many days of PTO do full-time employees accrue per year?",
  "expected_answer": "22 working days per calendar year, accrued at 1.83 days per month.",
  "expected_sources": ["02-leave-policy.md"],
  "category": "easy",
  "answerable": true
}
```

Categories included:

| Category | Count | Purpose |
|---|---:|---|
| `easy` | 10 | Single-chunk, factual; should be near-100%. |
| `multihop` | 5 | Answer requires combining 2+ chunks or reasoning. |
| `adversarial` | 3 | Contains a false premise; correct answer is to *correct* the premise. |
| `out_of_scope` | 3 | Answer is NOT in the docs; correct answer is the refusal string. |

For `out_of_scope` items, `answerable` is `false` and `expected_sources` is `[]`. Your metrics must handle these cases correctly.

---

## Tasks

### Task 1 — Retrieval metrics (`starter/metrics_retrieval.py`)

For an answerable question, retrieval is "correct" if **at least one expected source** appears in the retrieved chunks.

Implement two metrics over a list of evaluation items:

- **`recall_at_k(items, k)`** — fraction of items whose retrieved top-k contains *any* expected source.
  Skip `out_of_scope` items (they have no expected sources).
- **`mean_reciprocal_rank(items, k)`** — average of `1/rank` of the first expected source in the top-k (0 if not found).

Each item is a dict with the gold fields plus a `retrieved_sources: list[str]` populated by your evaluation harness (Task 3).

### Task 2 — LLM-as-judge metrics (`starter/metrics_judge.py`)

Implement two LLM-as-judge metrics. **Both must use a structured rubric** (1–5 scale) and **chain-of-thought** reasoning — the judge writes its rationale before its score, à la G-Eval.

#### `faithfulness_score(item) -> JudgeResult`

Does the generated answer *only* state things supported by the retrieved chunks?

- **5:** Every claim is directly supported by the chunks.
- **3:** Mostly grounded; one minor unsupported detail.
- **1:** Substantial fabrication or contradicts the chunks.

Special handling:

- If the model's answer is the refusal string and the question is `out_of_scope`, score 5.
- If the model's answer is the refusal string and the question is *answerable*, that's a *retrieval / threshold* failure; score 5 for faithfulness anyway (refusing is faithful — Task 1's recall metric will catch this separately).

#### `answer_relevancy_score(item) -> JudgeResult`

Does the answer actually address the user's question?

- **5:** Direct, complete answer.
- **3:** Partially answers; misses a sub-question or a key qualifier.
- **1:** Does not address the question.

Special handling:

- For `out_of_scope` questions, the refusal string scores 5 (it's the *correct* response).
- A confident hallucinated answer to an `out_of_scope` question scores 1.

The judge model should return JSON with `{"reasoning": "...", "score": 1..5}`. Use **Structured Outputs** (Pydantic schema enforcement) so parsing is reliable.

### Task 3 — The eval harness (`starter/run_eval.py`)

Wire it together:

1. Load `data/eval/gold_qa.jsonl`.
2. For each item, call your RAG pipeline (`assignment_03_rag/solution/`) to produce:
   - the retrieved chunk list,
   - the generated answer text.
3. Compute all four metrics.
4. Print a results table with per-category averages and an overall average.
5. Write a JSON report to `reports/eval_<timestamp>.json` so runs are diffable.

CLI:

```bash
python -m assignment_04_evals.starter.run_eval \
  --config-name "default" \
  --top-k 5 \
  --threshold 0.30
```

### Task 4 — Compare two configurations

Run the eval suite **twice** with meaningfully different parameters, e.g.:

| Config A | Config B |
|---|---|
| chunk_size=500, top_k=3 | chunk_size=1000, top_k=8 |

Re-ingest with each chunk size before its run. Save both reports.

Write `reports/comparison.md` (max 1 page) covering:

1. The exact configurations tested.
2. A table of metrics side-by-side.
3. **Which config wins overall and why.**
4. **Where they differ most** (which category? which metric?). Form a hypothesis explaining why.
5. **What you would try next** if you had another day.

### Task 5 — Wire into pytest (`starter/tests/test_regression.py`)

Convert the eval suite into pytest cases that:

- Run the *latest* JSON report (or run a quick eval if none exists — your choice).
- Assert `recall_at_5 >= 0.85`, `mean_faithfulness >= 4.0`, `mean_answer_relevancy >= 4.0` *overall*.
- Assert `recall_at_5 == 1.0` on the `easy` subset.
- Assert that all `out_of_scope` items produce the refusal string (faithfulness 5 alone is not enough — assert the *behavior* directly).

`pytest` should fail the build if any of these regress.

---

## Stretch goals

- **Citation correctness as a third judge metric.** Score whether each `[source: <name>]` citation actually appears in the retrieved chunks.
- **Integrate with `ragas`.** Compare its `faithfulness` and `answer_relevancy` to your hand-rolled judge. Where do they disagree, and which do you trust more?
- **Confidence intervals.** Run each LLM-as-judge metric 3 times and report mean + std. LLM judges are noisy; quantify the noise.
- **Cost & latency** as additional reported metrics. Cheap evals matter more than you think.

---

## Constraints

- **Use Structured Outputs** for the LLM judge — no regex parsing.
- **Use the same judge model for both metrics** in the base assignment. Use `gpt-4o-mini` to keep costs sane (~$0.10 per full eval run).
- **Do not use the same model as the answer-generator for judging unless you note it as a known limitation** in your report. Same-model self-evaluation is the most common LLM-as-judge bias; acknowledge it.

---

## Deliverables

1. Filled-in `starter/` code.
2. Two JSON reports under `reports/`.
3. `reports/comparison.md`.
4. Passing `pytest` run — paste the output into your comparison doc.

---

## Hints

<details>
<summary>Hint 1 — Recall@k on out-of-scope items</summary>

Don't include them in the recall denominator. They have no expected sources, so 'correct retrieval' is undefined for them. The *behavior* you care about for OOS items is whether the *generation* refuses — which is captured by faithfulness/relevancy and by the explicit pytest assertion.
</details>

<details>
<summary>Hint 2 — Why chain-of-thought before score?</summary>

If you ask the judge for a number first, it tends to anchor on a 4 and rationalize. Asking for reasoning first measurably improves agreement with human judgment (this is the core finding of G-Eval). Force the JSON schema to put `reasoning` BEFORE `score`.
</details>

<details>
<summary>Hint 3 — Don't compare apples and oranges</summary>

When comparing two configs, **fix the random seed** by using `temperature=0` everywhere (you already are) and **use the exact same gold dataset**. Sounds obvious; people get it wrong constantly.
</details>

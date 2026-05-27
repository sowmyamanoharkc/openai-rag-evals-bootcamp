# Assignment 1 — Solution Notes

This is the *why* behind `solution/summarize.py`. Read this **after** you've attempted the assignment yourself — otherwise you'll cheat yourself out of the most useful lessons.

---

## What this assignment is really for

The shipped artifact is a 100-line CLI that summarizes a text file. That is not the point. The point is to:

1. Make sure your `OPENAI_API_KEY` works and your environment is set up *before* you hit the harder assignments.
2. See, in the smallest possible context, the four primitives every later assignment is built on:
   - **Authentication** (one env var).
   - **Messages** (system + user roles).
   - **Token accounting** (local prediction vs. API ground truth).
   - **Per-token billing** (everything has a price; you should know it).
3. Build the muscle of *attaching dollar signs to API calls*. Engineers who don't do this in week one tend to ship $400 surprise bills in week ten.

---

## Design decisions

### 1. Three explicit system prompts, not one parameterised prompt

We define three distinct system prompts (`formal`, `casual`, `eli5`) rather than one with `{style}` substitution. Why?

- Pedagogically, you should *write* three voices and feel the difference. Variable substitution lets you fool yourself into thinking you're "controlling style" when you're not — the model is just adding a word.
- In production, you'd absolutely template — but you'd have eval data confirming the templating preserves the intended behaviour. We have no eval data yet, so we hard-code.

### 2. `temperature=0`

Two reasons:

- Reproducibility: running the tool twice on the same input gives the same output. That makes debugging trivial.
- Pedagogy: when you tweak a prompt, any change in output is from the prompt, not from sampling noise.

`temperature=0` is **not** a production default for everything — for creative tasks it makes the output flat and repetitive — but for a deterministic summarizer it's right.

### 3. Hard-coded pricing with a "last verified" date

Pricing changes. We hard-code constants at the top of the module *with a comment* citing the source page and the date someone last looked. Two reasons:

- It's honest about staleness. A learner copy-pasting six months later sees "verified 2026-04" and knows to double-check.
- It puts the dollar amount on the same screen as the code that bills it. You won't update what you can't see.

For unknown models (e.g. user passes `--model gpt-5-future`), we return `estimated_cost_usd = None` and print `"estimated cost: unknown"` rather than guessing. Guessing on cost is worse than admitting ignorance.

### 4. Local token count *and* API token count

We count tokens twice:

- Locally with `tiktoken` *before* the API call — so we can refuse if the prompt is over a budget cap.
- From `usage.prompt_tokens` *after* the API call — the source of truth for billing.

We print both. They should be close (the API count is slightly higher because of role/turn overhead). Showing the disagreement teaches you that local prediction is for budgeting, never for invoicing.

### 5. `tiktoken.encoding_for_model` with a fallback

```python
try:
    enc = tiktoken.encoding_for_model(model)
except KeyError:
    enc = tiktoken.get_encoding("cl100k_base")
```

`tiktoken` is regularly behind the API by a few weeks for new models. The cl100k_base fallback is correct for all GPT-4-family models and "close enough" for everything else. Worst case, you over- or under-count by a few percent — which doesn't matter for a budget check.

### 6. The 50,000-token cap

The hard cap in `summarize` (`MAX_INPUT_TOKENS = 50_000`) is **not** about model context limits — `gpt-4o-mini` happily eats 128k. It's about cost: an unbounded `summarize` is a $5-per-call surprise waiting to happen if a user pipes in a giant log file. The cap forces you to think about that case at design time.

---

## Common pitfalls

| Symptom | Likely cause |
|---|---|
| `Error: OPENAI_API_KEY not set` | You didn't `cp .env.example .env` and edit it, or you didn't `load_dotenv()` before instantiating `OpenAI()`. |
| Local count is *much* higher than `usage.prompt_tokens` | You're counting tokens of the raw text twice — once standalone, once as part of the messages list. Count the messages list once. |
| Cost is `$0.000000` | You're rounding too aggressively. Use `:.6f` formatting, not `:.2f`. At this scale fractions of a cent are normal. |
| Output is identical across all three styles | You're not actually swapping the system prompt. Print `messages[0]["content"]` to verify. |
| The model ignores `--style eli5` and writes a paragraph | Your eli5 prompt is too vague. Be aggressive: *"Write 5 short sentences. Use one analogy. Use only common words."* |

---

## Grading rubric (out of 100)

| Category | Points | What we look for |
|---|---|---|
| API call works | 20 | The CLI runs end to end on the sample article. |
| Style differentiation | 20 | All three styles produce visibly different outputs; eli5 has short sentences and an analogy. |
| Token counting | 15 | Local count is computed; API count is reported; the discrepancy is acknowledged in `runs.md`. |
| Cost reporting | 15 | Constants commented with date; cost printed to 6 decimals; unknown models handled gracefully. |
| Input validation | 10 | Empty file, missing file, unknown style — all raise clear errors. Not silent fallbacks. |
| Code quality | 10 | Type hints, dataclass for the result, clean module shape. |
| `runs.md` | 10 | Three style outputs included; the 3-line reflection answers the question. |

A passing grade is 70+. A 90+ requires a stretch goal (e.g. streaming, JSON output, or token-aware truncation).

---

## What to read after

1. OpenAI Chat Completions reference — read the entire request schema once. Notice how few fields you actually need.
2. Andrej Karpathy's *Let's build the GPT tokenizer* (1 hour video) — to make tokenization concrete. After this, `usage.prompt_tokens` will stop being a magic number.
3. The `tiktoken` README — three minutes, but it's worth knowing what `cl100k_base` is and which models share it.

Then go to Assignment 2.

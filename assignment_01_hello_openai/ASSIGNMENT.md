# Assignment 1 — Hello, OpenAI

**Stack:** Pure `openai` SDK + `tiktoken`. No frameworks.
**Prerequisites:** Python 3.10+, an `OPENAI_API_KEY`, comfort reading the OpenAI Chat Completions docs.

---

## What you will build

A small CLI tool, `summarize.py`, that reads a `.txt` file and prints a summary in one of three styles:

```bash
python -m assignment_01_hello_openai.starter.summarize data/samples/article.txt --style formal
python -m assignment_01_hello_openai.starter.summarize data/samples/article.txt --style casual
python -m assignment_01_hello_openai.starter.summarize data/samples/article.txt --style eli5
```

The tool prints:

1. The summary itself.
2. The token usage (input, output, total) — measured *both* via `tiktoken` (locally) and via the API response (`usage.*_tokens`). They should agree(+/- 10 tokens can be considered a match).
3. An estimated USD cost using current `gpt-4o-mini` pricing.

This is a deliberately tiny exercise. The point is to **internalize what an OpenAI API call actually is** — a JSON request with messages, a JSON response with content and usage, and a per-token bill — before any framework hides those primitives.

---

## Learning outcomes

After completing this assignment you will be able to:

- Authenticate to the OpenAI API from Python and pick a model deliberately.
- Compose a request out of `system` and `user` messages, and explain what each role does to the model.
- Use `tiktoken` to count tokens *before* sending a request (so you can budget and cap input length).
- Read the `usage` field on a Chat Completions response and convert it to a dollar cost.
- Vary model behaviour purely by changing the system prompt — same task, three different "voices".

---

## What's provided

```text
assignment_01_hello_openai/
├── ASSIGNMENT.md          # this file
├── SOLUTION.md            # design notes — read AFTER attempting yourself
├── starter/
│   └── summarize.py       # skeleton with TODOs
└── solution/              # reference implementation (peek only when stuck)

data/samples/article.txt   # ~500-word sample article you can summarize
```

---

## Tasks

### Task 1 — Read the input (`starter/summarize.py`)

Implement `read_text(path: str) -> str`. Read the file as UTF-8. Strip trailing whitespace. If the file is empty, raise a clear error.

### Task 2 — Pick a system prompt per style

Implement `system_prompt_for(style: str) -> str`. Three styles:

| `--style` | Voice |
|---|---|
| `formal` | Concise, neutral, suitable for a research brief. ~3 short paragraphs. No first person. |
| `casual` | Conversational, friendly. Contractions are fine. ~3 short paragraphs. |
| `eli5` | Explain-like-I'm-five: short sentences, simple words, one analogy. ~5 sentences. |

If the style isn't one of these, raise `ValueError` with a helpful message. **Do not** silently fall back to a default — the user asked for something specific.

### Task 3 — Count input tokens locally

Implement `count_tokens(text: str, model: str) -> int` using `tiktoken`. Use `tiktoken.encoding_for_model(model)` and fall back to `tiktoken.get_encoding("cl100k_base")` if the model isn't recognised yet (newer models sometimes lag the package). Count tokens for the full prompt **including** the system message — not just the user content.

You'll use this in two places:
- Before the API call, to refuse if the prompt is over a sane budget (say, 50,000 tokens).
- After the API call, to cross-check that your local count agrees with `usage.prompt_tokens`.

### Task 4 — Call the API

Implement `summarize(text: str, style: str, model: str = "gpt-4o-mini") -> SummaryResult` where `SummaryResult` is a dataclass with:

```python
@dataclass
class SummaryResult:
    summary: str
    style: str
    model: str
    input_tokens: int        # from API usage.prompt_tokens
    output_tokens: int       # from API usage.completion_tokens
    estimated_cost_usd: float
    local_token_count: int   # from your tiktoken count
```

Requirements:

- `temperature=0` for deterministic warm-up runs.
- Build the messages list: `[{"role": "system", ...}, {"role": "user", ...}]`.
- Use `client.chat.completions.create(...)`.
- Compute `estimated_cost_usd` from the pricing constants in `summarize.py` (you'll define them).

### Task 5 — CLI

Wire it up with `argparse`:

```bash
python -m assignment_01_hello_openai.starter.summarize <path> --style {formal,casual,eli5} [--model MODEL]
```

The output should be roughly:

```text
=== Summary (eli5) ===
<the summary>

=== Usage ===
input tokens   : 612
output tokens  : 184
total tokens   : 796
local count    : 612  (matches: yes)
model          : gpt-4o-mini
estimated cost : $0.000202
```

---

## Constraints and rules

- **Do not** use LangChain, LlamaIndex, or any wrapper. Pure `openai` SDK only.
- **Do not** stream — keep the call simple. (Streaming is in a later assignment.)
- **Do** load `OPENAI_API_KEY` from `.env` via `python-dotenv`.
- **Do** `temperature=0` so that two runs of the same input give the same summary (helpful for verifying your work).

---

## Stretch goals

- **`--max-input-tokens` flag** that truncates the input (with a warning) when it would exceed the budget. Use `tiktoken` to truncate at a token boundary, not a character boundary.
- **`--json` flag** that emits the result as JSON instead of human-readable text. Useful for piping into a script.
- **Streaming mode** (`--stream`) that prints tokens as they arrive. Note how `usage` is *only* populated at the end of a streaming response (and in some SDK versions you must opt in via `stream_options={"include_usage": True}`).

---

## Deliverables

1. `starter/summarize.py` filled in (no TODOs left).
2. A run of the tool against `data/samples/article.txt` for each of the three styles. Save the three outputs as `assignment_01_hello_openai/runs.md` (just paste them).
3. A 3-line note at the top of `runs.md` answering: *Which style cost the most output tokens, and why?*

---

## Hints (read only when stuck)

<details>
<summary>Hint 1 — The minimum viable Chat Completions call</summary>

```python
from openai import OpenAI
client = OpenAI()  # picks up OPENAI_API_KEY from env
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    temperature=0,
    messages=[
        {"role": "system", "content": "You are concise."},
        {"role": "user", "content": "Summarize: ..."},
    ],
)
print(resp.choices[0].message.content)
print(resp.usage.prompt_tokens, resp.usage.completion_tokens)
```
</details>

<details>
<summary>Hint 2 — tiktoken for prompts (not just strings)</summary>

`usage.prompt_tokens` includes per-message overhead (a handful of tokens for role markers and separators). If your local count is *exactly* the sum of `len(encoding.encode(msg["content"]))` for every message, you'll be a little under. For a warm-up assignment, "within ~10 tokens" is fine — note the discrepancy and move on. *Don't* try to perfectly reverse-engineer the API's tokenization.
</details>

<details>
<summary>Hint 3 — Cost calculation</summary>

```python
COST_PER_INPUT_TOKEN = 0.15 / 1_000_000   # $0.15 per 1M input tokens, needs updation with model/pricing change
COST_PER_OUTPUT_TOKEN = 0.60 / 1_000_000

cost = usage.prompt_tokens * COST_PER_INPUT_TOKEN + usage.completion_tokens * COST_PER_OUTPUT_TOKEN
print(f"${cost:.6f}")
```

Six decimal places — at this scale a single call costs fractions of a cent and you want to *see* that, not see "0.00".
</details>

<details>
<summary>Hint 4 — Why three system prompts, not one prompt with three branches?</summary>

You could have one system prompt and inject the style as a variable. You'd see the same outputs. Doing three explicit prompts is a teaching choice: it forces you to *write* three different voices and notice how much the model leans on the system prompt to set tone. In the next assignment we'll switch to schema-driven design where the prompt is mostly boilerplate.
</details>

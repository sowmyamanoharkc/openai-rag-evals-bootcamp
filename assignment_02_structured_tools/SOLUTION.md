# Assignment 2 — Solution Notes

This is the *why* behind `solution/`. Read this **after** you've attempted the assignment yourself.

---

## What this assignment is really for

In Assignment 1 you saw a chat completion as a string-in, string-out box. In production, almost no one uses LLMs that way. The two patterns you'll use constantly are:

1. **Structured outputs** — the model returns JSON conforming to a schema you control. The model is now an *extractor* or a *router*, not a chatter.
2. **Tool calling** — the model can decide to invoke a Python function with arguments it generates. The model is now an *agent that can act*.

This assignment combines both in the smallest realistic example. By the end you will have implemented a tiny agent loop by hand, with bounded iterations, a single repair retry, and Pydantic validation. RAG (Assignment 3), evals (Assignment 4)are more elaborate versions of what you'll write here.

---

## Architecture at a glance

```text
                           transcript.txt
                                │
                                ▼
           ┌────────── extract.extract_notes ──────────┐
           │                                           │
           │  build messages (system + user transcript)│
           │                                           │
           │  ┌─────────── tool-call loop ──────────┐  │
           │  │  call API w/ tools=[lookup_employee] │  │
           │  │  if tool_calls: dispatch + append    │  │
           │  │  else: break                         │  │
           │  └─────────── (max 4 iter) ────────────┘  │
           │                                           │
           │  final call w/ response_format=MeetingNotes
           │                                           │
           │  Pydantic validate → cross-field validator│
           │     │                                     │
           │     │  fail?  ──► append corrective msg   │
           │     │           re-call once              │
           │     └──── still fail → raise              │
           └───────────────────────────────────────────┘
                                │
                                ▼
                        MeetingNotes (validated)
```

Three concerns, three places to debug: schema (`schema.py`), tool plumbing (`tools.py`), control flow (`extract.py`).

---

## Design decisions

### 1. `pydantic.BaseModel` *is* the spec

We do not write a JSON schema by hand. We let Pydantic generate it from `MeetingNotes` and feed that to the API via `client.chat.completions.parse(response_format=MeetingNotes)`. Why?

- One source of truth. The Python type and the wire schema can never drift.
- The `parse()` helper handles the small differences between Pydantic-generated schema and what Structured Outputs accepts (no unconstrained types, `additionalProperties: false` everywhere, `$ref` flattening, etc.).

If you find yourself writing a JSON schema literal, stop — you're recreating Pydantic.

### 2. `extra="forbid"` everywhere

```python
model_config = ConfigDict(extra="forbid")
```

This translates to `additionalProperties: false` in the generated JSON schema, which Structured Outputs **requires**. Forgetting this on even one nested model causes the API to reject the schema with an unhelpful error.

### 3. Strings, not `datetime.date`, for `due`

Tempting: type `due: date | None`. Don't. The JSON-schema generator emits `format: "date"` which Structured Outputs accepts, but downstream tooling (e.g. logging, equality checks) gets messier. For a 4-hour assignment, a string in `YYYY-MM-DD` (or `None`) is the pragmatic choice. We document the format in the field description so the model gets it right.

### 4. Cross-field validation lives in Pydantic, not in the prompt

The rule "every action item owner is also an attendee" is enforced via a `@model_validator(mode="after")`. Why not in the prompt?

- The model **will** sometimes write `"Sofia"` when the attendee is `"Sofia Andrade"`. Putting the rule in the prompt only makes it less likely; it doesn't make it impossible.
- A validator is a *guarantee*. A prompt is a *suggestion*. We want guarantees on the contract; suggestions are for tone.
- The retry loop turns a Pydantic `ValidationError` into a corrective message. The validator is therefore the integration point for the entire repair pattern.

### 5. Tool-call dispatch via a dict, not `getattr`

```python
TOOL_DISPATCH = {"lookup_employee": lookup_employee}
def dispatch_tool(name, args): return TOOL_DISPATCH[name](**args)
```

Two reasons:

- Security: an attacker who can influence tool-call output can't escalate to "call any function in this module".
- Maintenance: when you add a tool, the registration is one explicit line, not a side effect of a method existing.

You'll see exactly the same pattern, scaled up, in Assignment 5's LangChain agent (where the framework hides the dispatch table).

### 6. The retry budget is **one**

If the first call passes the cross-field validator, you're done in one round trip. If it fails, we send back the validation error verbatim and ask for a fix; almost always that succeeds. If the *second* attempt fails, we raise.

We deliberately do **not** loop "until it works":

- Most failures past the first retry are *systemic* (e.g. an attendee really wasn't named in the transcript). More retries don't fix systemic bugs; they just spend money.
- An unbounded retry loop interacts catastrophically with paid APIs. Forty retries at 1k tokens each = ~$0.012 per failed extraction; one bug, ten thousand calls, $120 evaporates while you're at lunch.

In production you'd add observability (count `validation_failures_total`, alert on a spike) rather than more retries.

### 7. Tool calls are bounded too

`MAX_TOOL_ITERATIONS = 4`. The transcript has a handful of attendees; the model needs at most one tool call per attendee whose email it doesn't know. Four iterations is generous. We log a warning if we hit the cap — it usually means the model is stuck looping on the same lookup.

### 8. Why `response_format` only on the *final* call

Two design choices the OpenAI API forces on you:

- When you pass `response_format={"type": "json_schema", ...}`, the model **cannot** call tools in that response — it must produce the structured output.
- Tools and structured output are therefore on a sequence, not in parallel.

So our loop runs tool calls *first* (no `response_format`), and then makes one final call *with* `response_format` to get the validated JSON. The system prompt makes this expectation clear so the model doesn't try to call a tool on the final pass.

### 9. `temperature=0`

Same reason as Assignment 1, plus: structured extraction with sampling noise is a debugging nightmare. If two runs produce subtly different JSON for the same transcript, you can't tell whether your prompt change had any effect.

---

## Common pitfalls

| Symptom | Likely cause |
|---|---|
| API rejects the response_format with `additionalProperties` error | A nested model is missing `model_config = ConfigDict(extra="forbid")`. |
| `parse()` returns `None` for `parsed` | The model refused or hit a stop reason like `length`. Inspect `resp.choices[0].finish_reason`. |
| Retry loop never terminates | You forgot to break when `tool_calls` is empty. The condition is `if not msg.tool_calls: break`. |
| Tool message format error | The tool result message must include `tool_call_id` matching the tool call ID, and `content` must be a string (e.g. `json.dumps(result)`), not a dict. |
| Cross-field validator never fires | You're calling `MeetingNotes(**data)` instead of `MeetingNotes.model_validate(data)`. They're nearly equivalent, but `model_validate` is the canonical entry point. |
| Validator fires on a real attendee | Your name normalization differs between attendee and action_item.owner — strip whitespace and use exact comparison. Don't case-fold; "Aisha" and "AISHA" really *are* different identifiers in this contract. |
| Model invents a tool that doesn't exist | Your tool description is too vague. Be aggressive: *"This is the only tool available. Do not call any other tool."* |
| Cost per run is wildly higher than expected | You're not capping tool iterations. Print the iteration count after each run. |

---

## Grading rubric (out of 100)

| Category | Points | What we look for |
|---|---|---|
| Schema correctness | 20 | Pydantic models, `extra="forbid"`, cross-field validator working. |
| Structured output | 15 | Uses `parse()` or raw `json_schema` with `strict=True`. |
| Tool-call loop | 25 | Bounded iterations, dispatch dict, correct tool message format. |
| Retry/repair | 15 | Single retry on validation error, hard fail after that. |
| CLI & deliverable | 10 | Human and `--json` modes, meta footer with iteration / token counts. |
| Code quality | 15 | Type hints, dataclass / model usage, no copy-pasted JSON schema. |

A passing grade is 70+. A 90+ requires at least one stretch goal (a second tool, streaming, or a tiny eval set).

---

## What to read after

1. **OpenAI Structured Outputs guide** — read it once end to end. Note the constraints (`additionalProperties: false`, no unconstrained types, no recursion).
2. **Pydantic v2 docs → Validators** — `model_validator(mode="after")` is the workhorse. Skim `field_validator` for completeness.
3. **OpenAI Function Calling guide** — even though we used the modern `tools` interface, the older Function Calling page has good examples of how to write *crisp* tool descriptions, which is the art form here.

Then go to Assignment 3, where you'll build a RAG pipeline that uses none of these primitives — and feel how different a retrieval problem is from an extraction problem.

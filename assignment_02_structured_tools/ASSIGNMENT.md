# Assignment 2 — Structured Output + Tool Calling

**Stack:** Pure `openai` SDK + `pydantic`. No frameworks.
**Prerequisites:** Assignment 1, basic familiarity with Pydantic models.

---

## What you will build

A meeting-notes extractor that turns a free-form transcript into a strictly-validated JSON object:

```json
{
  "title": "Acme Corp — Platform sync — May 6, 2026",
  "attendees": [
    {"name": "Priya Raman", "email": "priya.raman@acme.com", "team": "Platform"},
    {"name": "Marcus Liu",  "email": "marcus.liu@acme.com",  "team": "SRE"},
    {"name": "Sofia Andrade", "email": "sofia.andrade@acme.com", "team": "Platform"}
  ],
  "decisions": [
    "Cutover Postgres 14 → 16 on Saturday May 9 at 02:00 PT.",
    "Embedding-cost de-duplication fix shipped as a separate release."
  ],
  "action_items": [
    {"owner": "Sofia Andrade", "task": "Post Postgres cutover runbook", "due": "2026-05-07"},
    {"owner": "Marcus Liu",   "task": "Open de-duplication PR", "due": "2026-05-07"},
    {"owner": "Priya Raman",  "task": "Update June PagerDuty schedule", "due": null}
  ]
}
```

The extractor must:

1. Use **OpenAI Structured Outputs** so the model returns JSON that conforms to a Pydantic schema (no `json.loads` on a free-form string and praying).
2. Expose **one tool** — `lookup_employee(name) -> {email, team, manager}` — that the model can call to enrich attendees with email/team data it doesn't know from the transcript.
3. Implement **a single retry loop**: if the parsed result fails an additional Pydantic validation rule (e.g. an unknown owner in `action_items`), send the validation error back to the model and let it correct itself once. After one retry, hard-fail with a clear error.

```bash
python -m assignment_02_structured_tools.starter.extract data/samples/transcript.txt
```

---

## Learning outcomes

After completing this assignment you will be able to:

- Use **Structured Outputs** (`response_format={"type": "json_schema", ...}` or the SDK's `client.chat.completions.parse(...)` helper) to get type-safe JSON back from a model.
- Design a **schema-first** prompt: the schema is the spec; the system prompt is just glue.
- Implement **function/tool calling**: declare a tool, run a tool-call loop (`assistant → tool_calls → execute → tool message → assistant`), and stop when the model emits a final answer.
- Write a **single retry / repair loop** when validation fails — and *resist* the temptation to retry forever (that's how you ship a $400 bill).
- Articulate the difference between "the model returned JSON" and "the JSON is correct". Structured Outputs guarantees the *shape*; semantic validation is still your job.

---

## What's provided

```text
assignment_02_structured_tools/
├── ASSIGNMENT.md          # this file
├── SOLUTION.md            # design notes — read AFTER attempting yourself
├── starter/
│   ├── schema.py          # Pydantic models with TODOs
│   ├── tools.py           # mock employee directory + tool dispatcher
│   └── extract.py         # the main extraction loop
└── solution/              # reference implementation

data/samples/transcript.txt   # ~80-line meeting transcript
```

---

## Tasks

### Task 1 — Schema (`starter/schema.py`)

Define four Pydantic models:

```python
class Attendee(BaseModel):
    name: str
    email: str | None = None
    team: str | None = None

class ActionItem(BaseModel):
    owner: str             # must match one of the attendee names
    task: str
    due: str | None = None # ISO date YYYY-MM-DD or None

class Decision(BaseModel):
    text: str

class MeetingNotes(BaseModel):
    title: str
    attendees: list[Attendee]
    decisions: list[Decision]
    action_items: list[ActionItem]
```

**Important schema choices:**

- Use `str | None` (not `Optional[str]`) for nullable fields. The OpenAI Structured Outputs JSON-schema generator handles both, but `str | None` reads cleanly.
- Set `model_config = ConfigDict(extra="forbid")` on every model. Structured Outputs requires `additionalProperties: false` and Pydantic's `extra="forbid"` produces exactly that.
- For `due`, accept either a YYYY-MM-DD string or null. Don't try to use `datetime.date` — the JSON schema for it is finicky in Structured Outputs. Strings are fine.

### Task 2 — Cross-field validation

In `MeetingNotes`, add a `model_validator(mode="after")` that enforces:

> Every `action_item.owner` must match exactly one `attendee.name`.

If it doesn't, raise `ValueError` with the offending owner. **This is the rule the retry loop will exercise** — the model will sometimes invent owners (e.g. `"Sofia"` when the attendee is `"Sofia Andrade"`), and you want to catch it.

### Task 3 — Tool: `lookup_employee` (`starter/tools.py`)

Implement an in-memory employee directory and a tool function:

```python
EMPLOYEE_DIRECTORY: dict[str, dict] = {
    "Priya Raman":   {"email": "priya.raman@acme.com",   "team": "Platform", "manager": "Devon Park"},
    "Marcus Liu":    {"email": "marcus.liu@acme.com",    "team": "SRE",      "manager": "Devon Park"},
    "Sofia Andrade": {"email": "sofia.andrade@acme.com", "team": "Platform", "manager": "Priya Raman"},
    "Aisha Khan":    {"email": "aisha.khan@acme.com",    "team": "Platform", "manager": "Priya Raman"},
    "Hiroshi Tanaka": {"email": "hiroshi.tanaka@acme.com", "team": "SRE",     "manager": "Marcus Liu"},
}

def lookup_employee(name: str) -> dict:
    """Return {email, team, manager} for an exact name match, or {error: not_found}."""
```

Provide an OpenAI tool spec:

```python
LOOKUP_EMPLOYEE_TOOL = {
    "type": "function",
    "function": {
        "name": "lookup_employee",
        "description": "Look up an Acme Corp employee's email, team, and manager by exact full name. Use this to fill in missing email/team fields for attendees mentioned in a transcript.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The employee's full name."},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
    },
}
```

Also export a `dispatch_tool(name, args)` function that maps the tool name to its Python implementation. Future tools = future dispatch entries; **don't `eval`** the function name.

### Task 4 — Extraction loop (`starter/extract.py`)

This is the heart of the assignment. Implement `extract_notes(transcript: str, model: str = "gpt-4o-mini") -> MeetingNotes`.

The loop:

1. Build initial messages: a system prompt + a user message containing the transcript.
2. Call `client.chat.completions.create(... tools=[LOOKUP_EMPLOYEE_TOOL], ...)`. **Do not pass `response_format` on this first call** — the model needs to be free to choose between calling a tool or producing a final answer.
3. If the response has `tool_calls`:
   - For each tool call, dispatch it, append a `{"role": "tool", "tool_call_id": ..., "content": json.dumps(result)}` message.
   - Loop back to step 2. Cap iterations at **4** (anything more is a bug).
4. When the model finally answers without tool calls, run a *final* call with `response_format={"type": "json_schema", "json_schema": ..., "strict": True}` (or use `client.chat.completions.parse(response_format=MeetingNotes)`) so the output is shape-validated.
5. Pass the result through `MeetingNotes.model_validate(...)` to trigger the cross-field validator.
6. **On `ValidationError`**, send a corrective user message back containing the error and ask the model to fix it. Re-validate. If it still fails, raise.

The loop is finite: at most **4 tool-call iterations** + **1 final structured call** +  **1 retry** = 6 model calls total. That's the upper bound; print a warning if you hit it.

### Task 5 — CLI

```bash
python -m assignment_02_structured_tools.starter.extract data/samples/transcript.txt
python -m assignment_02_structured_tools.starter.extract data/samples/transcript.txt --json   # raw JSON
```

Default output should be human-readable: title, attendees one per line, then decisions, then action items. `--json` dumps `meeting_notes.model_dump_json(indent=2)`.

Also print a small footer:

```text
=== Meta ===
tool calls   : 2 (lookup_employee, lookup_employee)
retries      : 0
total tokens : 1842 in, 312 out
```

---

## Constraints and rules

- **Do** use `pydantic >= 2.7`. The v1 API is gone; don't reach for `BaseModel.parse_obj`.
- **Do** cap tool-call iterations and retries explicitly. An unbounded loop on a paid API is a footgun.
- **Don't** `eval` or `getattr` the tool name. Use a dispatch dict.
- **Don't** write your own JSON schema by hand — let Pydantic generate it from the model.
- **Don't** use Function Calling's old `function_call` field. Use `tool_calls` (the modern interface).
- **Do** `temperature=0`. Variability is a bug here.

---

## Stretch goals

- **Add a second tool**: `list_team_members(team) -> list[name]`. Useful for "everyone on Platform agreed to..." cases.
- **Streaming + structured output**: try `client.chat.completions.stream(...)` and assemble the parsed object incrementally.
- **A second validation rule**: assert every action item's `due` date (if present) is in the future relative to a reference date you parse from the title. Force a retry by deliberately weakening the system prompt.
- **An eval set**: write 5 tiny transcripts with known-correct extractions and a script that scores precision/recall on attendees/decisions/action items. (This is a soft on-ramp to Assignment 4.)

---

## Deliverables

1. Filled-in `starter/` (no TODOs left).
2. The extraction output for `data/samples/transcript.txt`, saved as `assignment_02_structured_tools/run_output.json`.
3. A 5-line note `assignment_02_structured_tools/notes.md` answering: *Did the model call `lookup_employee`? If not, why not? If yes, on which attendees and why those?*

---

## Hints (read only when stuck)

<details>
<summary>Hint 1 — The two ways to do Structured Outputs</summary>

Both work; pick one and stick with it.

**Option A: `parse()` helper (recommended).**

```python
from pydantic import BaseModel

class Out(BaseModel):
    answer: str

resp = client.chat.completions.parse(
    model="gpt-4o-mini",
    temperature=0,
    messages=[...],
    response_format=Out,
)
parsed: Out = resp.choices[0].message.parsed
```

**Option B: raw `response_format` with a JSON schema.**

```python
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    temperature=0,
    messages=[...],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "MeetingNotes",
            "schema": MeetingNotes.model_json_schema(),
            "strict": True,
        },
    },
)
data = json.loads(resp.choices[0].message.content)
notes = MeetingNotes.model_validate(data)
```

Note: Pydantic's auto-generated JSON schema may need light massaging (`additionalProperties: false` everywhere, no `$defs` references the API rejects). The `parse()` helper does this for you — that's why it's the recommended path.
</details>

<details>
<summary>Hint 2 — Tool-calling control flow</summary>

```
[user transcript] ──► model ──► tool_calls? ──yes──► run tools ──► [tool result messages] ──► model ──► (loop)
                                  │
                                  no
                                  ▼
                                final assistant message (the JSON)
```

The model decides when it's done — it stops emitting `tool_calls` and gives you a content message. Your loop terminates the moment `response.choices[0].message.tool_calls` is `None` or empty.
</details>

<details>
<summary>Hint 3 — Why a retry loop, not a retry tower</summary>

A naive "keep retrying until it parses" loop is how you accidentally ship a $200-per-meeting feature. **One** retry is enough to recover from transient model confusion. If a *second* retry would help, the prompt or schema is wrong — fix that, don't paper over it with more retries.
</details>

<details>
<summary>Hint 4 — The cross-field validator is the point</summary>

The interesting failure mode of structured outputs isn't "the model returned malformed JSON" — Structured Outputs essentially eliminates that. The interesting failure is **semantically wrong but structurally valid** JSON: an action item assigned to "Sofia" when the attendee is "Sofia Andrade", or a decision lifted from a side-comment that wasn't actually decided.

You can't catch the second case from a schema — that needs an LLM-as-judge eval (Assignment 4). But you *can* catch the first with `model_validator`. That's why we exercise it here.
</details>

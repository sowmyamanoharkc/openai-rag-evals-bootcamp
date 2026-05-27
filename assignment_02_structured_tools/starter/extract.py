"""Meeting-notes extractor with structured output, tool calls, and a single retry.

Run:
    python -m assignment_02_structured_tools.starter.extract data/samples/transcript.txt
    python -m assignment_02_structured_tools.starter.extract data/samples/transcript.txt --json

You must complete every TODO. Do not change the public function signatures.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError

from .schema import MeetingNotes
from .tools import ALL_TOOLS, dispatch_tool

load_dotenv()

DEFAULT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
MAX_TOOL_ITERATIONS = 4
MAX_RETRIES = 1

SYSTEM_PROMPT = """You extract structured meeting notes from a free-form transcript.

You will be given a transcript. Produce a MeetingNotes JSON object with:
- title: a short string identifying the meeting (use the transcript header if present).
- attendees: every distinct person who spoke OR was named as agreeing to a decision.
- decisions: every concrete decision made. Skip side-comments and questions.
- action_items: every committed task. owner MUST match an attendee.name EXACTLY.

You may call lookup_employee(name) to fill in missing email/team for an attendee.
Call it at most once per attendee. Do not invent emails. If lookup_employee returns
"not_found", leave email and team as null.

When you have all the data you need, return the final JSON. Do not call tools on
the final response.
"""


@dataclass
class ExtractionMeta:
    tool_calls: list[str] = field(default_factory=list)
    retries: int = 0
    input_tokens: int = 0
    output_tokens: int = 0


def read_transcript(path: str | Path) -> str:
    """Read a transcript file as UTF-8.

    TODO:
      - Read `path`. Strip trailing whitespace.
      - Raise ValueError on empty input.
    """
    raise NotImplementedError("TODO: implement read_transcript")


def _run_tool_loop(
    client: OpenAI,
    messages: list[dict],
    model: str,
    meta: ExtractionMeta,
) -> list[dict]:
    """Run the tool-call loop until the model produces a non-tool-call message.

    TODO:
      - Loop up to MAX_TOOL_ITERATIONS times:
          - Call client.chat.completions.create(model=model, messages=messages,
                tools=ALL_TOOLS, temperature=0).
          - Track usage: meta.input_tokens += resp.usage.prompt_tokens, etc.
          - msg = resp.choices[0].message
          - If not msg.tool_calls: append msg.model_dump(exclude_none=True) and return messages.
          - Otherwise:
              - Append the assistant message (with tool_calls) to messages.
              - For each tc in msg.tool_calls:
                  - args = json.loads(tc.function.arguments or "{}")
                  - result = dispatch_tool(tc.function.name, args)
                  - meta.tool_calls.append(tc.function.name)
                  - Append a {"role": "tool", "tool_call_id": tc.id,
                              "content": json.dumps(result)} message.
      - If you exit the loop without a non-tool-call message, print a warning
        and return messages anyway.
    """
    raise NotImplementedError("TODO: implement _run_tool_loop")


def _final_structured_call(
    client: OpenAI,
    messages: list[dict],
    model: str,
    meta: ExtractionMeta,
) -> MeetingNotes:
    """Make the final call with response_format=MeetingNotes and return the parsed model.

    TODO:
      - Use client.chat.completions.parse(model=model, messages=messages,
            response_format=MeetingNotes, temperature=0).
      - Track usage on `meta`.
      - Return resp.choices[0].message.parsed (which is a MeetingNotes instance).
        If it's None, raise RuntimeError(f"Model refused to produce structured output: "
        f"{resp.choices[0].finish_reason}")
    """
    raise NotImplementedError("TODO: implement _final_structured_call")


def extract_notes(
    transcript: str, model: str = DEFAULT_MODEL
) -> tuple[MeetingNotes, ExtractionMeta]:
    """Extract MeetingNotes from a transcript. Returns (notes, meta)."""
    client = OpenAI()
    meta = ExtractionMeta()

    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Transcript:\n\n{transcript}"},
    ]

    # 1. Tool-call loop (no response_format yet — model must be free to call tools).
    messages = _run_tool_loop(client, messages, model, meta)

    # 2. Final structured call.
    notes = _final_structured_call(client, messages, model, meta)

    # 3. Cross-field validation. If it fails, run ONE retry with the error fed back.
    try:
        MeetingNotes.model_validate(notes.model_dump())
        return notes, meta
    except ValidationError as e:
        # TODO:
        #   - Append a corrective user message explaining the validation error.
        #   - Re-run _final_structured_call.
        #   - Re-validate. If it still fails, raise.
        #   - Increment meta.retries.
        raise NotImplementedError("TODO: implement the retry/repair branch") from e


def render_human(notes: MeetingNotes, meta: ExtractionMeta) -> str:
    lines: list[str] = []
    lines.append(f"=== {notes.title} ===\n")
    lines.append("Attendees:")
    for a in notes.attendees:
        suffix_parts = [p for p in [a.email, a.team] if p]
        suffix = f"  ({' / '.join(suffix_parts)})" if suffix_parts else ""
        lines.append(f"  - {a.name}{suffix}")
    lines.append("\nDecisions:")
    for d in notes.decisions:
        lines.append(f"  - {d.text}")
    lines.append("\nAction items:")
    for it in notes.action_items:
        due = f" [due {it.due}]" if it.due else ""
        lines.append(f"  - {it.owner}: {it.task}{due}")
    lines.append("")
    lines.append("=== Meta ===")
    tc_summary = ", ".join(meta.tool_calls) if meta.tool_calls else "(none)"
    lines.append(f"tool calls   : {len(meta.tool_calls)} ({tc_summary})")
    lines.append(f"retries      : {meta.retries}")
    lines.append(f"total tokens : {meta.input_tokens} in, {meta.output_tokens} out")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract meeting notes from a transcript.")
    parser.add_argument("path", type=Path, help="Transcript .txt file.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--json", action="store_true", help="Emit raw JSON instead of human text.")
    args = parser.parse_args()

    transcript = read_transcript(args.path)
    notes, meta = extract_notes(transcript, model=args.model)

    if args.json:
        print(notes.model_dump_json(indent=2))
    else:
        print(render_human(notes, meta))


if __name__ == "__main__":
    main()

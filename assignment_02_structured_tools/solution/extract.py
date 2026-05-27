"""Reference solution: meeting-notes extractor with tools + structured output + 1 retry."""

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
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No such file: {p}")
    text = p.read_text(encoding="utf-8").rstrip()
    if not text.strip():
        raise ValueError(f"Transcript is empty: {p}")
    return text


def _accumulate_usage(meta: ExtractionMeta, usage) -> None:
    if usage is None:
        return
    meta.input_tokens += getattr(usage, "prompt_tokens", 0) or 0
    meta.output_tokens += getattr(usage, "completion_tokens", 0) or 0


def _serialize_assistant_message(msg) -> dict:
    """Turn an OpenAI SDK message object back into a dict suitable for the next call."""
    out: dict = {"role": "assistant", "content": msg.content}
    if msg.tool_calls:
        out["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in msg.tool_calls
        ]
    return out


def _run_tool_loop(
    client: OpenAI,
    messages: list[dict],
    model: str,
    meta: ExtractionMeta,
) -> list[dict]:
    for _ in range(MAX_TOOL_ITERATIONS):
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=ALL_TOOLS,
            temperature=0,
        )
        _accumulate_usage(meta, resp.usage)
        msg = resp.choices[0].message

        if not msg.tool_calls:
            # Model produced a non-tool-calling response.
            # We don't append it because the next phase makes a fresh structured call;
            # but adding it as context doesn't hurt either. Keep the loop simple.
            return messages

        messages.append(_serialize_assistant_message(msg))
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            result = dispatch_tool(tc.function.name, args)
            meta.tool_calls.append(tc.function.name)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                }
            )

    print(
        f"warning: hit MAX_TOOL_ITERATIONS={MAX_TOOL_ITERATIONS}; "
        "the model is likely looping on tool calls."
    )
    return messages


def _final_structured_call(
    client: OpenAI,
    messages: list[dict],
    model: str,
    meta: ExtractionMeta,
) -> MeetingNotes:
    resp = client.chat.completions.parse(
        model=model,
        messages=messages,
        response_format=MeetingNotes,
        temperature=0,
    )
    _accumulate_usage(meta, resp.usage)
    parsed = resp.choices[0].message.parsed
    if parsed is None:
        raise RuntimeError(
            f"Model refused to produce structured output. "
            f"finish_reason={resp.choices[0].finish_reason}"
        )
    return parsed


def extract_notes(
    transcript: str, model: str = DEFAULT_MODEL
) -> tuple[MeetingNotes, ExtractionMeta]:
    client = OpenAI()
    meta = ExtractionMeta()

    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Transcript:\n\n{transcript}"},
    ]

    messages = _run_tool_loop(client, messages, model, meta)
    notes = _final_structured_call(client, messages, model, meta)

    try:
        MeetingNotes.model_validate(notes.model_dump())
        return notes, meta
    except ValidationError as e:
        if meta.retries >= MAX_RETRIES:
            raise
        meta.retries += 1
        # Feed the validator's complaint back to the model so it can self-correct.
        messages.append(
            {
                "role": "user",
                "content": (
                    "Your previous output failed validation with this error:\n"
                    f"{e}\n\n"
                    "Correct ONLY the offending fields. Do not change anything else. "
                    "Re-emit the full MeetingNotes JSON."
                ),
            }
        )
        notes = _final_structured_call(client, messages, model, meta)
        # Re-validate; if it still fails, surface the error.
        MeetingNotes.model_validate(notes.model_dump())
        return notes, meta


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
    parser.add_argument("path", type=Path)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    transcript = read_transcript(args.path)
    notes, meta = extract_notes(transcript, model=args.model)

    if args.json:
        print(notes.model_dump_json(indent=2))
    else:
        print(render_human(notes, meta))


if __name__ == "__main__":
    main()

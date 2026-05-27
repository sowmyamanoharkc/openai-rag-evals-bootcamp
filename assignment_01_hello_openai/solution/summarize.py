"""Reference solution: a tiny OpenAI summarizer with token + cost reporting."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

import tiktoken
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
MAX_INPUT_TOKENS = 50_000

# Pricing per 1M tokens.
# Source: https://openai.com/api/pricing/   (last verified: 2026-05-04)
PRICING_PER_1M_TOKENS: dict[str, dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
}

VALID_STYLES = ("formal", "casual", "eli5")

SYSTEM_PROMPTS: dict[str, str] = {
    "formal": (
        "You are a precise technical writer. Summarize the user's text in roughly "
        "three short paragraphs. Use a neutral, third-person register. No first person. "
        "No filler. Preserve any concrete numbers, names, and dates from the source. "
        "Do not add facts that are not in the source."
    ),
    "casual": (
        "You are a friendly editor explaining an article to a colleague over coffee. "
        "Summarize the user's text in roughly three short paragraphs. Conversational tone, "
        "contractions are fine. Keep it warm but accurate — do not invent details."
    ),
    "eli5": (
        "Explain the user's text the way you'd explain it to a smart 10-year-old. "
        "Use exactly five short sentences. Use simple, everyday words. Include exactly one "
        "analogy. Do not use jargon. Do not invent facts. If the source mentions a number "
        "or a name and it's important, keep it."
    ),
}


@dataclass
class SummaryResult:
    summary: str
    style: str
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float | None
    local_token_count: int


def read_text(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No such file: {p}")
    text = p.read_text(encoding="utf-8").rstrip()
    if not text.strip():
        raise ValueError(f"Input file is empty: {p}")
    return text


def system_prompt_for(style: str) -> str:
    if style not in VALID_STYLES:
        raise ValueError(
            f"Unknown style {style!r}. Expected one of: {', '.join(VALID_STYLES)}"
        )
    return SYSTEM_PROMPTS[style]


def _encoding_for(model: str) -> tiktoken.Encoding:
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def count_tokens(messages: list[dict], model: str) -> int:
    enc = _encoding_for(model)
    return sum(len(enc.encode(m["content"])) for m in messages)


def cost_for(model: str, input_tokens: int, output_tokens: int) -> float | None:
    pricing = PRICING_PER_1M_TOKENS.get(model)
    if pricing is None:
        return None
    return (
        input_tokens * pricing["input"] + output_tokens * pricing["output"]
    ) / 1_000_000


def summarize(text: str, style: str, model: str = DEFAULT_MODEL) -> SummaryResult:
    messages = [
        {"role": "system", "content": system_prompt_for(style)},
        {"role": "user", "content": text},
    ]

    local_count = count_tokens(messages, model)
    if local_count > MAX_INPUT_TOKENS:
        raise ValueError(
            f"Input is {local_count} tokens, which exceeds the safety cap of "
            f"{MAX_INPUT_TOKENS}. Truncate or split before summarizing."
        )

    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=messages,
    )

    summary = resp.choices[0].message.content or ""
    usage = resp.usage
    input_tokens = usage.prompt_tokens if usage else 0
    output_tokens = usage.completion_tokens if usage else 0

    return SummaryResult(
        summary=summary.strip(),
        style=style,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost_usd=cost_for(model, input_tokens, output_tokens),
        local_token_count=local_count,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize a .txt file using OpenAI.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--style", choices=VALID_STYLES, default="formal")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    text = read_text(args.path)
    result = summarize(text, style=args.style, model=args.model)

    print(f"=== Summary ({result.style}) ===")
    print(result.summary)
    print()
    print("=== Usage ===")
    print(f"input tokens   : {result.input_tokens}")
    print(f"output tokens  : {result.output_tokens}")
    print(f"total tokens   : {result.input_tokens + result.output_tokens}")
    matches = "yes" if abs(result.local_token_count - result.input_tokens) <= 10 else "no"
    print(f"local count    : {result.local_token_count}  (matches: {matches})")
    print(f"model          : {result.model}")
    if result.estimated_cost_usd is None:
        print("estimated cost : unknown (no pricing for this model)")
    else:
        print(f"estimated cost : ${result.estimated_cost_usd:.6f}")


if __name__ == "__main__":
    main()

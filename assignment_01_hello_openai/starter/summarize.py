"""Hello, OpenAI — a tiny CLI that summarizes a .txt file in one of three styles.

Run:
    python -m assignment_01_hello_openai.starter.summarize data/samples/article.txt --style eli5

You must complete every TODO. Do not change the public function signatures.
"""

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
MAX_INPUT_TOKENS = 50_000  # safety cap; not the model's context limit

# Pricing per 1M tokens.
# Source: https://openai.com/api/pricing/   (last verified: 2026-05-04)
# If you change the default model, update or extend this table.
PRICING_PER_1M_TOKENS: dict[str, dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
}

VALID_STYLES = ("formal", "casual", "eli5")


@dataclass
class SummaryResult:
    summary: str
    style: str
    model: str
    input_tokens: int       # from API usage.prompt_tokens
    output_tokens: int      # from API usage.completion_tokens
    estimated_cost_usd: float | None  # None if model has no known pricing
    local_token_count: int  # your tiktoken count of the prompt


def read_text(path: str | Path) -> str:
    """Read a text file as UTF-8 and return its contents (trailing whitespace stripped).

    TODO:
      - Read `path` as UTF-8.
      - Strip trailing whitespace.
      - If the file is empty (or whitespace only), raise ValueError with a clear message.
    """
    raise NotImplementedError("TODO: implement read_text")


def system_prompt_for(style: str) -> str:
    """Return a system prompt for the requested style.

    Styles:
      - formal: concise, neutral, ~3 short paragraphs, no first person.
      - casual: conversational, friendly, ~3 short paragraphs.
      - eli5:   5 short sentences, one analogy, simple words only.

    TODO:
      - Validate `style` against VALID_STYLES; raise ValueError on unknown styles.
      - Return a system prompt string tuned for the requested voice.
    """
    raise NotImplementedError("TODO: implement system_prompt_for")


def count_tokens(messages: list[dict], model: str) -> int:
    """Return a rough local token count of the messages list.

    Uses tiktoken. Falls back to cl100k_base if the model isn't in tiktoken's table.

    TODO:
      - Get the encoding (try `tiktoken.encoding_for_model(model)`, except KeyError fall
        back to `tiktoken.get_encoding("cl100k_base")`).
      - Sum `len(encoding.encode(m["content"]))` over messages.
      - You don't need to perfectly match the API count — within ~10 tokens is fine.
    """
    raise NotImplementedError("TODO: implement count_tokens")


def cost_for(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """Estimate cost in USD for the given model and token counts.

    TODO:
      - If `model` is not in PRICING_PER_1M_TOKENS, return None.
      - Otherwise compute (input_tokens * input_price + output_tokens * output_price) / 1_000_000.
    """
    raise NotImplementedError("TODO: implement cost_for")


def summarize(text: str, style: str, model: str = DEFAULT_MODEL) -> SummaryResult:
    """Summarize `text` in the given `style`.

    TODO:
      - Build messages = [{"role": "system", ...}, {"role": "user", ...}].
      - Local-count tokens; raise ValueError if > MAX_INPUT_TOKENS.
      - Call client.chat.completions.create(model=model, messages=messages, temperature=0).
      - Build and return a SummaryResult.
    """
    client = OpenAI()
    # TODO: implement the rest
    raise NotImplementedError("TODO: implement summarize")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize a .txt file using OpenAI.")
    parser.add_argument("path", type=Path, help="Path to a .txt file.")
    parser.add_argument(
        "--style",
        choices=VALID_STYLES,
        default="formal",
        help="Voice of the summary.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenAI model name. Default: {DEFAULT_MODEL}",
    )
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

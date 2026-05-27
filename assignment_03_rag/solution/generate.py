"""Reference solution: generate a grounded answer."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from .retrieve import RetrievedChunk

load_dotenv()

CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
SIMILARITY_THRESHOLD = 0.30
REFUSAL_TEXT = "I don't know based on the provided docs."

CITATION_RE = re.compile(r"\[source:\s*([^\]]+?)\]")


@dataclass
class Answer:
    text: str
    citations: list[str] = field(default_factory=list)
    is_grounded: bool = True


SYSTEM_PROMPT = """You are an internal-policy assistant for Acme Corp.
You answer ONLY using the provided context chunks.
Rules:
1. Every factual claim must include an inline citation in the format [source: <filename>].
2. If the context does not contain the answer, respond with EXACTLY:
   "I don't know based on the provided docs."
3. Do NOT use prior knowledge. Do NOT speculate.
4. Be concise. Two short paragraphs maximum.
"""


def build_user_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    lines: list[str] = ["Context chunks:", ""]
    for i, c in enumerate(chunks, 1):
        lines.append(f"[{i}] (source: {c.source_path})")
        lines.append(c.text)
        lines.append("")
    lines.append(f"Question: {question}")
    return "\n".join(lines)


def _extract_citations(text: str) -> list[str]:
    seen: list[str] = []
    for match in CITATION_RE.findall(text):
        name = match.strip()
        if name and name not in seen:
            seen.append(name)
    return seen


def answer(
    question: str,
    retrieved: list[RetrievedChunk],
    threshold: float = SIMILARITY_THRESHOLD,
) -> Answer:
    if not retrieved or max(c.similarity for c in retrieved) < threshold:
        return Answer(text=REFUSAL_TEXT, citations=[], is_grounded=False)

    client = OpenAI()
    user_prompt = build_user_prompt(question, retrieved)

    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    text = (resp.choices[0].message.content or "").strip()

    if text.strip() == REFUSAL_TEXT:
        return Answer(text=REFUSAL_TEXT, citations=[], is_grounded=False)

    return Answer(text=text, citations=_extract_citations(text), is_grounded=True)

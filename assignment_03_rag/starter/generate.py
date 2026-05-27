"""Generate a grounded answer from retrieved chunks."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from .retrieve import RetrievedChunk

load_dotenv()

CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
SIMILARITY_THRESHOLD = 0.30
REFUSAL_TEXT = "I don't know based on the provided docs."


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
    """Compose the user message containing the question and numbered context.

    TODO:
      - Format each chunk like:
          [N] (source: <filename>)
          <chunk text>
      - End with the user's question on its own line.
    """
    raise NotImplementedError("TODO: implement build_user_prompt")


def answer(
    question: str,
    retrieved: list[RetrievedChunk],
    threshold: float = SIMILARITY_THRESHOLD,
) -> Answer:
    """Produce a grounded answer with citations.

    TODO:
      1. Guardrail: if `retrieved` is empty OR max similarity < threshold,
         return Answer(text=REFUSAL_TEXT, citations=[], is_grounded=False)
         WITHOUT calling the model.
      2. Otherwise, build the user prompt and call gpt-4o-mini with temperature=0.
      3. Parse the response:
           - text = response.choices[0].message.content.strip()
           - citations = unique source filenames mentioned in the text in [source: <name>] format.
           - is_grounded = (text != REFUSAL_TEXT).
      4. Return an Answer.
    """
    raise NotImplementedError("TODO: implement answer")

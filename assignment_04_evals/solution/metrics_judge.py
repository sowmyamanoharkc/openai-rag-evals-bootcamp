"""Reference solution: LLM-as-judge metrics."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

JUDGE_MODEL = os.getenv("OPENAI_JUDGE_MODEL", "gpt-4o-mini")
REFUSAL_TEXT = "I don't know based on the provided docs."


class JudgeOutput(BaseModel):
    reasoning: str = Field(description="Step-by-step reasoning before the score.")
    score: int = Field(ge=1, le=5, description="Integer score from 1 to 5.")


@dataclass
class JudgeResult:
    score: int
    reasoning: str


FAITHFULNESS_RUBRIC = """You are evaluating the FAITHFULNESS of an AI answer to its retrieved context.
Faithfulness = does the answer ONLY state facts that are supported by the provided context chunks?

Score on a 1-5 integer scale:
- 5 = every claim in the answer is directly supported by the chunks.
- 4 = mostly supported; one trivial unsupported phrasing.
- 3 = mostly supported but one notable unsupported detail.
- 2 = several claims unsupported by the chunks.
- 1 = substantial fabrication, or the answer contradicts the chunks.

If the answer is exactly the refusal string ("I don't know based on the provided docs."),
score 5 — refusing is faithful.

Reason step-by-step BEFORE giving the score.
"""

ANSWER_RELEVANCY_RUBRIC = """You are evaluating whether an AI answer ADDRESSES the user's question.
This is independent of correctness or grounding — only "does it address what was asked?".

Score on a 1-5 integer scale:
- 5 = direct, complete answer to the question.
- 4 = mostly addresses; missing a minor qualifier.
- 3 = partially addresses; misses a sub-question or key qualifier.
- 2 = tangentially relevant; mostly misses the question.
- 1 = does not address the question at all.

Special case: for OUT-OF-SCOPE questions (where the correct behavior is to refuse),
the refusal string IS the correct response — score it 5.
A confident hallucinated answer to an out-of-scope question scores 1.

Reason step-by-step BEFORE giving the score.
"""


def _call_judge(system: str, user: str) -> JudgeOutput:
    client = OpenAI()
    resp = client.beta.chat.completions.parse(
        model=JUDGE_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format=JudgeOutput,
    )
    parsed = resp.choices[0].message.parsed
    if parsed is None:
        return JudgeOutput(reasoning="parse failure", score=1)
    return parsed


def _format_chunks(chunks: list[str]) -> str:
    return "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(chunks))


def faithfulness_score(item: dict) -> JudgeResult:
    answer_text = item.get("answer_text", "")
    if answer_text.strip() == REFUSAL_TEXT:
        return JudgeResult(score=5, reasoning="Refusal — vacuously faithful.")

    chunks = item.get("retrieved_chunks", [])
    user = (
        f"QUESTION:\n{item['question']}\n\n"
        f"RETRIEVED CHUNKS:\n{_format_chunks(chunks)}\n\n"
        f"ANSWER:\n{answer_text}\n"
    )
    out = _call_judge(FAITHFULNESS_RUBRIC, user)
    return JudgeResult(score=out.score, reasoning=out.reasoning)


def answer_relevancy_score(item: dict) -> JudgeResult:
    answer_text = item.get("answer_text", "")
    is_oos = item.get("category") == "out_of_scope"

    if is_oos and answer_text.strip() == REFUSAL_TEXT:
        return JudgeResult(score=5, reasoning="Correct refusal on out-of-scope question.")

    user = (
        f"QUESTION:\n{item['question']}\n\n"
        f"ANSWER:\n{answer_text}\n\n"
        f"NOTE: This question is "
        f"{'OUT-OF-SCOPE (the correct response is to refuse)' if is_oos else 'in-scope'}."
    )
    out = _call_judge(ANSWER_RELEVANCY_RUBRIC, user)
    return JudgeResult(score=out.score, reasoning=out.reasoning)

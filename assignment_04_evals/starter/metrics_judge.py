"""LLM-as-judge metrics: faithfulness and answer relevancy.

Both metrics use Structured Outputs to enforce a JSON schema with chain-of-thought
reasoning preceding the numeric score (per G-Eval).
"""

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
    """Schema enforced by Structured Outputs. Reasoning MUST come before score."""
    reasoning: str = Field(description="Step-by-step reasoning before the score.")
    score: int = Field(ge=1, le=5, description="Integer score from 1 to 5.")


@dataclass
class JudgeResult:
    score: int
    reasoning: str


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Judge calls
# ---------------------------------------------------------------------------

def _call_judge(system: str, user: str) -> JudgeOutput:
    """Call the judge model with Structured Outputs and return a JudgeOutput.

    TODO:
      - Use OpenAI().chat.completions.parse(...) with response_format=JudgeOutput.
      - model=JUDGE_MODEL, temperature=0.
      - messages = [system, user].
      - Return resp.choices[0].message.parsed.
    """
    raise NotImplementedError("TODO: implement _call_judge")


def faithfulness_score(item: dict) -> JudgeResult:
    """Judge whether item['answer_text'] is faithful to item['retrieved_chunks'].

    `item` must contain:
      - question
      - retrieved_chunks: list[str]   # full chunk texts
      - answer_text: str
      - answerable: bool
      - category: str

    TODO:
      - If answer_text == REFUSAL_TEXT, return JudgeResult(score=5, reasoning="refusal").
      - Otherwise build a user message containing:
          QUESTION, CHUNKS (numbered), ANSWER.
        Then call _call_judge(FAITHFULNESS_RUBRIC, user).
      - Wrap the result in a JudgeResult.
    """
    raise NotImplementedError("TODO: implement faithfulness_score")


def answer_relevancy_score(item: dict) -> JudgeResult:
    """Judge whether item['answer_text'] addresses item['question'].

    TODO:
      - If category == 'out_of_scope' AND answer_text == REFUSAL_TEXT,
        return JudgeResult(score=5, reasoning="correct refusal").
      - Otherwise build a user message containing QUESTION and ANSWER.
        Call _call_judge(ANSWER_RELEVANCY_RUBRIC, user).
      - Return a JudgeResult.
    """
    raise NotImplementedError("TODO: implement answer_relevancy_score")

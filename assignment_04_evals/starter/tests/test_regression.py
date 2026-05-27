"""Regression tests for the RAG system.

Run:
    pytest assignment_04_evals/starter/tests/ -v

These tests load the most recent eval report (or run a quick eval if none exists)
and assert that key metrics meet minimum thresholds. A failure here means a
regression and should fail CI.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
REPORTS_DIR = REPO_ROOT / "reports"


def _load_latest_report() -> dict:
    """Load the most recent eval report, or run one inline if none exists.

    TODO:
      - If REPORTS_DIR has any eval_*.json, pick the newest by mtime and load it.
      - Otherwise, call run_eval.run(top_k=5, threshold=0.30, config_name='ci') inline.
      - Return the results dict.
    """
    raise NotImplementedError("TODO: implement _load_latest_report")


@pytest.fixture(scope="session")
def report() -> dict:
    return _load_latest_report()


def test_overall_recall_at_5(report: dict) -> None:
    """Overall recall@5 must be >= 0.85.

    TODO: assert report['metrics']['overall']['recall_at_5'] >= 0.85
    """
    raise NotImplementedError("TODO")


def test_easy_category_recall_at_5(report: dict) -> None:
    """The 'easy' category must have recall@5 == 1.0 — no excuses.

    TODO: assert report['metrics']['by_category']['easy']['recall_at_5'] == 1.0
    """
    raise NotImplementedError("TODO")


def test_overall_faithfulness(report: dict) -> None:
    """Mean faithfulness must be >= 4.0.

    TODO: assert report['metrics']['overall']['mean_faithfulness'] >= 4.0
    """
    raise NotImplementedError("TODO")


def test_overall_answer_relevancy(report: dict) -> None:
    """Mean answer relevancy must be >= 4.0.

    TODO: assert report['metrics']['overall']['mean_answer_relevancy'] >= 4.0
    """
    raise NotImplementedError("TODO")


def test_out_of_scope_refuses(report: dict) -> None:
    """Every out_of_scope item must produce the refusal string.

    TODO:
      - For every item with category == 'out_of_scope':
          assert item['answer_text'] == "I don't know based on the provided docs."
      - Use pytest.fail or asserts with helpful messages.
    """
    raise NotImplementedError("TODO")

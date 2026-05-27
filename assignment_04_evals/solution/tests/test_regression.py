"""Regression tests — wires the eval suite into pytest.

Run:
    pytest assignment_04_evals/solution/tests/ -v
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
REPORTS_DIR = REPO_ROOT / "reports"
REFUSAL_TEXT = "I don't know based on the provided docs."

OVERALL_RECALL_THRESHOLD = 0.85
OVERALL_FAITHFULNESS_THRESHOLD = 4.0
OVERALL_RELEVANCY_THRESHOLD = 4.0


def _latest_report() -> dict:
    if REPORTS_DIR.exists():
        candidates = sorted(REPORTS_DIR.glob("eval_*.json"), key=lambda p: p.stat().st_mtime)
        if candidates:
            return json.loads(candidates[-1].read_text(encoding="utf-8"))

    import importlib
    run_eval = importlib.import_module("assignment_04_evals.solution.run_eval")
    results = run_eval.run(top_k=5, threshold=0.30, config_name="ci")
    run_eval.write_report(results)
    return results


@pytest.fixture(scope="session")
def report() -> dict:
    return _latest_report()


def _recall_at_5_key(report: dict) -> str:
    overall = report["metrics"]["overall"]
    for key in overall:
        if key.startswith("recall_at_") and key != "recall_at_1" and key != "recall_at_3":
            return key
    return "recall_at_5"


def test_overall_recall_at_5(report: dict) -> None:
    key = _recall_at_5_key(report)
    val = report["metrics"]["overall"][key]
    assert val >= OVERALL_RECALL_THRESHOLD, (
        f"Overall {key} = {val:.2f} is below threshold {OVERALL_RECALL_THRESHOLD}"
    )


def test_easy_category_recall_perfect(report: dict) -> None:
    by_cat = report["metrics"]["by_category"]
    assert "easy" in by_cat, "no 'easy' category found in report"
    easy = by_cat["easy"]
    recall_keys = [k for k in easy if k.startswith("recall_at_")]
    assert recall_keys, "no recall metric in easy category"
    val = easy[recall_keys[0]]
    assert val == 1.0, f"easy category {recall_keys[0]} = {val}, must be 1.0"


def test_overall_faithfulness(report: dict) -> None:
    val = report["metrics"]["overall"]["mean_faithfulness"]
    assert val >= OVERALL_FAITHFULNESS_THRESHOLD, (
        f"mean_faithfulness = {val:.2f} below threshold {OVERALL_FAITHFULNESS_THRESHOLD}"
    )


def test_overall_answer_relevancy(report: dict) -> None:
    val = report["metrics"]["overall"]["mean_answer_relevancy"]
    assert val >= OVERALL_RELEVANCY_THRESHOLD, (
        f"mean_answer_relevancy = {val:.2f} below threshold {OVERALL_RELEVANCY_THRESHOLD}"
    )


def test_out_of_scope_refuses(report: dict) -> None:
    failures: list[str] = []
    for item in report["items"]:
        if item.get("category") != "out_of_scope":
            continue
        if item.get("answer_text", "").strip() != REFUSAL_TEXT:
            failures.append(f"{item['id']}: got '{item.get('answer_text', '')[:60]}...'")
    assert not failures, "Out-of-scope items did not refuse:\n  " + "\n  ".join(failures)

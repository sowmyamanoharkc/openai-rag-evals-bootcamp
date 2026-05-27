"""Run the full eval suite over data/eval/gold_qa.jsonl."""

from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLD_PATH = REPO_ROOT / "data" / "eval" / "gold_qa.jsonl"
REPORTS_DIR = REPO_ROOT / "reports"


def load_gold(path: Path) -> list[dict]:
    """Load the JSONL file."""
    raise NotImplementedError("TODO: load gold_qa.jsonl, return list[dict]")


def evaluate_item(item: dict, top_k: int, threshold: float) -> dict:
    """Run the RAG pipeline on a single item and attach runtime fields.

    TODO:
      - Import retrieve and answer from assignment_03_rag.solution.
      - Call retrieve(question, k=top_k) -> list[RetrievedChunk].
      - Call answer(question, retrieved, threshold=threshold) -> Answer.
      - Mutate `item` (or copy) to add:
          retrieved_sources: list[str]   # source_path of each retrieved chunk, in order
          retrieved_chunks: list[str]    # the chunk texts
          retrieved_scores: list[float]  # similarity scores
          answer_text: str
      - Return the updated item.
    """
    raise NotImplementedError("TODO: implement evaluate_item")


def run(top_k: int, threshold: float, config_name: str) -> dict:
    """Run the full eval and return a results dict.

    TODO:
      1. Load gold items.
      2. For each, evaluate_item(...).
      3. Compute metrics:
           - recall_at_1, recall_at_3, recall_at_k (using top_k)
           - mean_reciprocal_rank at top_k
           - faithfulness_score and answer_relevancy_score for every item
      4. Build per-category averages too.
      5. Return {
           "config_name", "top_k", "threshold", "timestamp",
           "items": [...with judge results...],
           "metrics": {...},
         }
    """
    raise NotImplementedError("TODO: implement run")


def write_report(results: dict) -> Path:
    """Persist results to reports/eval_<timestamp>_<config>.json. Return the path."""
    raise NotImplementedError("TODO: implement write_report")


def print_summary(results: dict) -> None:
    """Pretty-print the metrics table.

    TODO:
      - Print overall metrics.
      - Print per-category breakdown.
      - Use the `tabulate` library or manual formatting — your choice.
    """
    raise NotImplementedError("TODO: implement print_summary")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-name", default="default")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--threshold", type=float, default=0.30)
    args = parser.parse_args()

    results = run(top_k=args.top_k, threshold=args.threshold, config_name=args.config_name)
    path = write_report(results)
    print_summary(results)
    print(f"\nReport written to {path}")


if __name__ == "__main__":
    main()

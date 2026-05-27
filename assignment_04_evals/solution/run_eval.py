"""Reference solution: full eval harness."""

from __future__ import annotations

import argparse
import importlib
import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLD_PATH = REPO_ROOT / "data" / "eval" / "gold_qa.jsonl"
REPORTS_DIR = REPO_ROOT / "reports"

_rag_retrieve = importlib.import_module("assignment_03_rag.solution.retrieve")
_rag_generate = importlib.import_module("assignment_03_rag.solution.generate")

from .metrics_judge import answer_relevancy_score, faithfulness_score
from .metrics_retrieval import mean_reciprocal_rank, recall_at_k


def load_gold(path: Path = GOLD_PATH) -> list[dict]:
    items: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def evaluate_item(item: dict, top_k: int, threshold: float) -> dict:
    item = dict(item)
    retrieved = _rag_retrieve.retrieve(item["question"], k=top_k)
    ans = _rag_generate.answer(item["question"], retrieved, threshold=threshold)

    item["retrieved_sources"] = [r.source_path for r in retrieved]
    item["retrieved_chunks"] = [r.text for r in retrieved]
    item["retrieved_scores"] = [r.similarity for r in retrieved]
    item["answer_text"] = ans.text
    item["answer_is_grounded"] = ans.is_grounded
    item["answer_citations"] = ans.citations
    return item


def _per_category(items: list[dict], compute) -> dict[str, float]:
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for it in items:
        by_cat[it.get("category", "uncategorized")].append(it)
    return {cat: compute(its) for cat, its in by_cat.items()}


def run(top_k: int, threshold: float, config_name: str) -> dict:
    print(f"Loading gold dataset from {GOLD_PATH}")
    gold = load_gold()
    print(f"Loaded {len(gold)} items")

    evaluated: list[dict] = []
    for i, item in enumerate(gold, 1):
        print(f"  [{i}/{len(gold)}] {item['id']} — {item['question'][:60]}...")
        evaluated.append(evaluate_item(item, top_k=top_k, threshold=threshold))

    print("\nJudging faithfulness and answer relevancy...")
    for i, it in enumerate(evaluated, 1):
        f = faithfulness_score(it)
        r = answer_relevancy_score(it)
        it["faithfulness_score"] = f.score
        it["faithfulness_reasoning"] = f.reasoning
        it["answer_relevancy_score"] = r.score
        it["answer_relevancy_reasoning"] = r.reasoning
        print(f"  [{i}/{len(evaluated)}] {it['id']}: F={f.score} R={r.score}")

    overall = {
        "recall_at_1": recall_at_k(evaluated, 1),
        "recall_at_3": recall_at_k(evaluated, 3),
        f"recall_at_{top_k}": recall_at_k(evaluated, top_k),
        f"mrr_at_{top_k}": mean_reciprocal_rank(evaluated, top_k),
        "mean_faithfulness": statistics.mean(i["faithfulness_score"] for i in evaluated),
        "mean_answer_relevancy": statistics.mean(i["answer_relevancy_score"] for i in evaluated),
    }

    by_category = _per_category(
        evaluated,
        lambda its: {
            "n": len(its),
            f"recall_at_{top_k}": recall_at_k(its, top_k),
            "mean_faithfulness": statistics.mean(i["faithfulness_score"] for i in its),
            "mean_answer_relevancy": statistics.mean(i["answer_relevancy_score"] for i in its),
        },
    )

    return {
        "config_name": config_name,
        "top_k": top_k,
        "threshold": threshold,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "items": evaluated,
        "metrics": {
            "overall": overall,
            "by_category": by_category,
        },
    }


def write_report(results: dict) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    cfg = results["config_name"].replace(" ", "_")
    path = REPORTS_DIR / f"eval_{ts}_{cfg}.json"
    path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return path


def print_summary(results: dict) -> None:
    print("\n" + "=" * 70)
    print(f" RESULTS — config={results['config_name']} top_k={results['top_k']} threshold={results['threshold']}")
    print("=" * 70)

    print("\nOverall:")
    for k, v in results["metrics"]["overall"].items():
        print(f"  {k:30s} {v:.3f}")

    print("\nBy category:")
    for cat, m in results["metrics"]["by_category"].items():
        print(f"  [{cat}] n={m['n']}")
        for k, v in m.items():
            if k == "n":
                continue
            print(f"    {k:30s} {v:.3f}")


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

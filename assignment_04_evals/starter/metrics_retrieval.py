"""Deterministic retrieval metrics: Recall@k and Mean Reciprocal Rank.

You will receive eval items shaped like:

    {
      "id": "easy-01",
      "question": "...",
      "expected_sources": ["02-leave-policy.md"],
      "category": "easy",
      "answerable": true,
      "retrieved_sources": ["02-leave-policy.md", "11-performance-review-cycle.md", ...]
    }

For out_of_scope items, expected_sources == [] and answerable == false.
"""

from __future__ import annotations


def recall_at_k(items: list[dict], k: int) -> float:
    """Fraction of ANSWERABLE items where any expected source appears in the
    first k retrieved sources.

    TODO:
      - Filter to items where item["answerable"] is True.
      - For each, check whether any expected source is in retrieved_sources[:k].
      - Return the fraction (0..1). Return 0.0 if there are no answerable items.
    """
    raise NotImplementedError("TODO: implement recall_at_k")


def mean_reciprocal_rank(items: list[dict], k: int) -> float:
    """Mean 1/rank of the first expected source within retrieved_sources[:k],
    or 0 if not found. Computed only over ANSWERABLE items.

    TODO:
      - Filter to answerable items.
      - For each item, scan retrieved_sources[:k] and find the smallest 1-based
        position whose value is in expected_sources.
      - rr = 1/position if found, else 0.
      - Return the average across answerable items.
    """
    raise NotImplementedError("TODO: implement mean_reciprocal_rank")

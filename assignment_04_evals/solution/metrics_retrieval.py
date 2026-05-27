"""Reference solution: deterministic retrieval metrics."""

from __future__ import annotations


def _answerable(items: list[dict]) -> list[dict]:
    return [it for it in items if it.get("answerable", True)]


def recall_at_k(items: list[dict], k: int) -> float:
    answerable = _answerable(items)
    if not answerable:
        return 0.0

    hits = 0
    for it in answerable:
        retrieved = it.get("retrieved_sources", [])[:k]
        expected = set(it.get("expected_sources", []))
        if expected.intersection(retrieved):
            hits += 1
    return hits / len(answerable)


def mean_reciprocal_rank(items: list[dict], k: int) -> float:
    answerable = _answerable(items)
    if not answerable:
        return 0.0

    total = 0.0
    for it in answerable:
        retrieved = it.get("retrieved_sources", [])[:k]
        expected = set(it.get("expected_sources", []))
        rr = 0.0
        for rank, src in enumerate(retrieved, start=1):
            if src in expected:
                rr = 1.0 / rank
                break
        total += rr
    return total / len(answerable)

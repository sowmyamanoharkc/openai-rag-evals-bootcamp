"""Reference solution: end-to-end CLI."""

from __future__ import annotations

import argparse

from .generate import answer
from .retrieve import retrieve


def ask(question: str, k: int = 5) -> None:
    retrieved = retrieve(question, k=k)
    result = answer(question, retrieved)

    print(f"Q: {question}\n")
    print(f"A: {result.text}\n")
    print("Sources:")
    if not result.is_grounded:
        print("  (none — refusal)")
        return
    for c in retrieved:
        print(f"  - {c.source_path} (chunk {c.chunk_index}, score {c.similarity:.3f})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("-k", type=int, default=5)
    args = parser.parse_args()
    ask(args.question, k=args.k)


if __name__ == "__main__":
    main()

"""End-to-end CLI: question -> retrieved chunks -> grounded answer.

Usage:
    python -m assignment_03_rag.starter.main "How much PTO do I get?"
"""

from __future__ import annotations

import argparse

from .generate import answer
from .retrieve import retrieve


def ask(question: str, k: int = 5) -> None:
    """TODO:
      - Call retrieve(question, k=k).
      - Call answer(question, retrieved).
      - Print the question, the answer.text, and the source list with scores.
    """
    raise NotImplementedError("TODO: implement ask")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("-k", type=int, default=5)
    args = parser.parse_args()
    ask(args.question, k=args.k)


if __name__ == "__main__":
    main()

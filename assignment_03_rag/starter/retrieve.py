"""Retrieve top-k chunks from the Chroma index for a query."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CHROMA_DIR = REPO_ROOT / "chroma_db"
COLLECTION_NAME = "acme_docs"
EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")


@dataclass
class RetrievedChunk:
    text: str
    source_path: str
    chunk_index: int
    similarity: float    # 1 - cosine_distance, higher is better


def embed_query(client: OpenAI, query: str) -> list[float]:
    """Embed a single query string.

    TODO:
      - Call client.embeddings.create(model=EMBED_MODEL, input=query).
      - Return the resulting embedding (list[float]).
    """
    raise NotImplementedError("TODO: implement embed_query")


def retrieve(query: str, k: int = 5, chroma_dir: Path | None = None) -> list[RetrievedChunk]:
    """Return the top-k chunks for `query`, sorted by similarity (highest first).

    TODO:
      - Open the Chroma collection at `chroma_dir` (default DEFAULT_CHROMA_DIR).
      - Embed the query.
      - collection.query(query_embeddings=[embedding], n_results=k) returns a dict
        with keys: "documents", "metadatas", "distances", "ids" (each is a list of lists).
      - Convert distances to similarity = 1 - distance.
      - Build and return list[RetrievedChunk] sorted by similarity descending.
    """
    raise NotImplementedError("TODO: implement retrieve")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("-k", type=int, default=5)
    args = parser.parse_args()

    hits = retrieve(args.query, k=args.k)
    for i, h in enumerate(hits, 1):
        print(f"[{i}] {h.source_path} (chunk {h.chunk_index}, score {h.similarity:.3f})")
        print(h.text[:200].replace("\n", " ") + ("..." if len(h.text) > 200 else ""))
        print()


if __name__ == "__main__":
    main()

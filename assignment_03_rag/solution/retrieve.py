"""Reference solution: retrieve top-k chunks."""

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
    similarity: float


def embed_query(client: OpenAI, query: str) -> list[float]:
    resp = client.embeddings.create(model=EMBED_MODEL, input=query)
    return resp.data[0].embedding


def retrieve(query: str, k: int = 5, chroma_dir: Path | None = None) -> list[RetrievedChunk]:
    chroma_dir = chroma_dir or DEFAULT_CHROMA_DIR
    chroma_client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = chroma_client.get_collection(name=COLLECTION_NAME)

    openai_client = OpenAI()
    q_embedding = embed_query(openai_client, query)

    res = collection.query(query_embeddings=[q_embedding], n_results=k)
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    distances = res["distances"][0]

    chunks = [
        RetrievedChunk(
            text=doc,
            source_path=meta.get("source_path", "unknown"),
            chunk_index=int(meta.get("chunk_index", -1)),
            similarity=1.0 - float(dist),
        )
        for doc, meta, dist in zip(docs, metas, distances)
    ]
    chunks.sort(key=lambda c: c.similarity, reverse=True)
    return chunks


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

"""Ingest documents into a Chroma vector store.

Run:
    python -m assignment_03_rag.starter.ingest --chunk-size 500 --chunk-overlap 50

You must complete every TODO. Do not change the public function signatures.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOCS_DIR = REPO_ROOT / "data" / "docs"
DEFAULT_CHROMA_DIR = REPO_ROOT / "chroma_db"
COLLECTION_NAME = "acme_docs"
EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")


@dataclass
class Document:
    path: str         # filename only, e.g. "02-leave-policy.md"
    content: str


def load_documents(docs_dir: str | Path) -> list[Document]:
    """Load every .md file under `docs_dir` as a Document.

    TODO:
      - Iterate over *.md files in docs_dir (non-recursive is fine for this dataset).
      - Read each file as UTF-8.
      - Return a list[Document] with `path` set to the filename only (not the full path).
    """
    raise NotImplementedError("TODO: implement load_documents")


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Recursively split `text` into chunks of approximately `chunk_size` characters.

    TODO:
      - Implement a recursive splitter that tries separators in this order:
        ["\\n\\n", "\\n", ". ", " "].
      - Each chunk should be at most `chunk_size` characters.
      - Adjacent chunks should share `chunk_overlap` characters of overlap to preserve context.
      - Strip whitespace from each chunk and drop empty chunks.
    """
    raise NotImplementedError("TODO: implement chunk_text")


def embed_chunks(client: OpenAI, chunks: list[str]) -> list[list[float]]:
    """Embed a list of text chunks using `text-embedding-3-small`.

    TODO:
      - Batch chunks into groups of <= 100 (the API accepts a list).
      - Call client.embeddings.create(model=EMBED_MODEL, input=batch).
      - Return embeddings in the SAME order as the input chunks.
    """
    raise NotImplementedError("TODO: implement embed_chunks")


def build_index(
    docs_dir: Path,
    chroma_dir: Path,
    chunk_size: int,
    chunk_overlap: int,
) -> int:
    """Build the vector index. Returns the number of chunks indexed.

    TODO:
      - Load documents.
      - For each document, chunk it. Track for each chunk:
          - a deterministic id (e.g. f"{doc.path}::{chunk_index}"),
          - the chunk text,
          - metadata: {"source_path": doc.path, "chunk_index": chunk_index}.
      - Embed all chunks.
      - Reset the Chroma collection (delete + recreate, OR clear then add) so the script is idempotent.
      - Add ids/documents/embeddings/metadatas to the collection.
      - Return the total chunk count.
    """
    client = OpenAI()
    chroma_client = chromadb.PersistentClient(path=str(chroma_dir))

    # TODO: implement the rest
    raise NotImplementedError("TODO: implement build_index")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    parser.add_argument("--chroma-dir", type=Path, default=DEFAULT_CHROMA_DIR)
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--chunk-overlap", type=int, default=50)
    args = parser.parse_args()

    n = build_index(args.docs_dir, args.chroma_dir, args.chunk_size, args.chunk_overlap)
    print(f"Indexed {n} chunks into {args.chroma_dir}")


if __name__ == "__main__":
    main()

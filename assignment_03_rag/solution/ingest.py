"""Reference solution: ingest documents into Chroma."""

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
EMBED_BATCH_SIZE = 64


@dataclass
class Document:
    path: str
    content: str


def load_documents(docs_dir: str | Path) -> list[Document]:
    docs: list[Document] = []
    for md_file in sorted(Path(docs_dir).glob("*.md")):
        docs.append(Document(path=md_file.name, content=md_file.read_text(encoding="utf-8")))
    return docs


def _split_recursive(text: str, separators: list[str], chunk_size: int) -> list[str]:
    """Split `text` into pieces of at most `chunk_size` chars using a hierarchy of separators.

    Tries each separator in order. If the result still has pieces > chunk_size,
    it recurses with the next separator on the oversized pieces.
    """
    if len(text) <= chunk_size:
        return [text]
    if not separators:
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    sep, *rest = separators
    if sep == "":
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    pieces = text.split(sep)
    out: list[str] = []
    for piece in pieces:
        if len(piece) <= chunk_size:
            out.append(piece)
        else:
            out.extend(_split_recursive(piece, rest, chunk_size))
    return [p for p in out if p]


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    pieces = _split_recursive(text, ["\n\n", "\n", ". ", " "], chunk_size)

    chunks: list[str] = []
    buf = ""
    for piece in pieces:
        candidate = (buf + " " + piece).strip() if buf else piece
        if len(candidate) <= chunk_size:
            buf = candidate
        else:
            if buf:
                chunks.append(buf)
            if len(piece) > chunk_size:
                for i in range(0, len(piece), chunk_size - chunk_overlap):
                    chunks.append(piece[i : i + chunk_size])
                buf = ""
            else:
                buf = piece
    if buf:
        chunks.append(buf)

    if chunk_overlap > 0 and len(chunks) > 1:
        overlapped: list[str] = [chunks[0]]
        for i in range(1, len(chunks)):
            tail = chunks[i - 1][-chunk_overlap:]
            overlapped.append((tail + " " + chunks[i]).strip())
        chunks = overlapped

    return [c.strip() for c in chunks if c.strip()]


def embed_chunks(client: OpenAI, chunks: list[str]) -> list[list[float]]:
    out: list[list[float]] = []
    for i in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch = chunks[i : i + EMBED_BATCH_SIZE]
        resp = client.embeddings.create(model=EMBED_MODEL, input=batch)
        out.extend(item.embedding for item in resp.data)
    return out


def build_index(
    docs_dir: Path,
    chroma_dir: Path,
    chunk_size: int,
    chunk_overlap: int,
) -> int:
    client = OpenAI()
    chroma_client = chromadb.PersistentClient(path=str(chroma_dir))

    if COLLECTION_NAME in [c.name for c in chroma_client.list_collections()]:
        chroma_client.delete_collection(COLLECTION_NAME)
    collection = chroma_client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    docs = load_documents(docs_dir)
    if not docs:
        raise RuntimeError(f"No .md files found in {docs_dir}")

    ids: list[str] = []
    texts: list[str] = []
    metadatas: list[dict] = []
    for doc in docs:
        for idx, chunk in enumerate(chunk_text(doc.content, chunk_size, chunk_overlap)):
            ids.append(f"{doc.path}::{idx}")
            texts.append(chunk)
            metadatas.append({"source_path": doc.path, "chunk_index": idx})

    print(f"Embedding {len(texts)} chunks from {len(docs)} documents...")
    embeddings = embed_chunks(client, texts)

    collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
    return len(texts)


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

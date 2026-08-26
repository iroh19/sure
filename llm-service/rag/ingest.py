"""
Index the knowledge base with the chosen model/strategy pair.

Which pair to choose is decided by `rag/bench.py`; this script only applies it.
Defaults come from environment variables so Docker and CI can configure it
without code changes.

    python -m rag.ingest
    RAG_EMBED_MODEL=tr-bert RAG_CHUNK_STRATEGY=fixed-240w python -m rag.ingest
    python -m rag.ingest --dry-run
"""
from __future__ import annotations

import argparse
import os
import time

from .chunk import STRATEGIES, chunk_all, load_documents
from .embed import MODELS, get_embedder
from .store import VectorStore, collection_name

DEFAULT_STRATEGY = os.getenv("RAG_CHUNK_STRATEGY", "heading")
DEFAULT_MODEL = os.getenv("RAG_EMBED_MODEL", "e5-small")


def ingest(model_key: str, strategy: str, dry_run: bool = False) -> int:
    docs = load_documents()
    chunks = chunk_all(strategy)

    print(f"Knowledge base : {len(docs)} documents")
    print(f"Strategy       : {strategy} -> {len(chunks)} chunks "
          f"(avg {sum(c.word_count for c in chunks) / len(chunks):.0f} words)")
    print(f"Model          : {model_key}")

    if dry_run:
        print("\n--dry-run: nothing written.")
        return 0

    embedder = get_embedder(model_key)
    embedder.verify_dim()

    store = VectorStore(dim=embedder.dim)
    store.ensure_schema()
    collection = collection_name(model_key, strategy)

    t0 = time.perf_counter()
    vectors = embedder.encode_passages([c.content for c in chunks])
    # Without clearing, a section deleted from a document lives on in the index
    # and keeps being retrieved.
    store.clear(collection)
    written = store.upsert(collection, chunks, vectors)
    elapsed = time.perf_counter() - t0

    print(f"Collection     : {collection} (table {store.table})")
    print(f"Written        : {written} chunks in {elapsed:.1f}s")
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description="Index the RAG knowledge base")
    ap.add_argument("--model", default=DEFAULT_MODEL, choices=sorted(MODELS))
    ap.add_argument("--strategy", default=DEFAULT_STRATEGY, choices=list(STRATEGIES))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ingest(args.model, args.strategy, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

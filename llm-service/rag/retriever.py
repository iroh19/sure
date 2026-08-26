"""
Retrieval entry point.

RAG is an enhancement, not a dependency. If the database is down, the collection
is empty or the embedding model will not load, `retrieve()` returns an empty list
and the system runs without it. The rule engine is deterministic and already
knows the oxygen threshold; wiring the most safety-critical path to the most
fragile component would be the wrong trade.
"""
from __future__ import annotations

import logging
import os

from .store import DEFAULT_DSN, SearchHit, VectorStore, collection_name

log = logging.getLogger("sure.rag")

RAG_ENABLED = os.getenv("RAG_ENABLED", "1") not in ("0", "false", "False")
RAG_MODEL = os.getenv("RAG_EMBED_MODEL", "e5-small")
RAG_STRATEGY = os.getenv("RAG_CHUNK_STRATEGY", "heading")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))

# Measured, not guessed — see `python -m rag.calibrate`. On e5-small/heading,
# positives score 0.841–0.892 and negatives 0.813–0.847: the distributions
# overlap, so no threshold separates them cleanly. 0.85 is the lowest value that
# lets no negative through, at the cost of 17% of positives losing context.
#
# The asymmetry justifies that trade: a missed document only weakens the model's
# reasoning and the rule engine still decides, whereas fabricated context
# presents wrong information with a citation attached.
#
# Recalibrate whenever the corpus or the collection changes.
RAG_MIN_SIMILARITY = float(os.getenv("RAG_MIN_SIMILARITY", "0.85"))

_warned = False


def _warn_once(msg: str) -> None:
    global _warned
    if not _warned:
        log.warning("RAG disabled: %s — continuing without retrieval.", msg)
        _warned = True


def retrieve(query: str, k: int | None = None) -> list[SearchHit]:
    if not RAG_ENABLED:
        return []

    try:
        from .embed import get_embedder

        embedder = get_embedder(RAG_MODEL)
        store = VectorStore(dim=embedder.dim)
        hits = store.search(
            collection_name(RAG_MODEL, RAG_STRATEGY),
            embedder.encode_query(query),
            k=k or RAG_TOP_K,
        )
    except Exception as exc:  # noqa: BLE001 — deliberate catch-all
        _warn_once(f"{type(exc).__name__}: {exc}")
        return []

    return [h for h in hits if h.similarity >= RAG_MIN_SIMILARITY]


def build_context(hits: list[SearchHit], max_chars: int = 2400) -> tuple[str, list[dict]]:
    """Turn hits into prompt context plus a source list.

    Chunks are numbered `[K1]`, `[K2]` and the model is asked to cite them, so a
    claim can be traced back to a document and a fabricated citation spotted.

    `max_chars` is a context budget: on a 1B model, long context does not improve
    accuracy, it drowns the instruction.
    """
    if not hits:
        return "", []

    parts: list[str] = []
    sources: list[dict] = []
    used = 0

    for i, h in enumerate(hits, start=1):
        body = h.content.strip()
        if used + len(body) > max_chars:
            break
        marker = f"K{i}"
        parts.append(f"[{marker}] {body}")
        sources.append({
            "marker": marker,
            "doc_id": h.doc_id,
            "heading": h.heading,
            "similarity": round(h.similarity, 3),
        })
        used += len(body)

    return "\n\n".join(parts), sources


def health() -> dict:
    info = {
        "enabled": RAG_ENABLED,
        "model": RAG_MODEL,
        "strategy": RAG_STRATEGY,
        "top_k": RAG_TOP_K,
        "min_similarity": RAG_MIN_SIMILARITY,
        "dsn": DEFAULT_DSN.rsplit("@", 1)[-1],  # never echo credentials
        "collection": collection_name(RAG_MODEL, RAG_STRATEGY),
        "chunks": None,
        "error": None,
    }
    if not RAG_ENABLED:
        return info
    try:
        from .embed import MODELS

        info["chunks"] = VectorStore(dim=MODELS[RAG_MODEL].dim).count(info["collection"])
    except Exception as exc:  # noqa: BLE001
        info["error"] = f"{type(exc).__name__}: {exc}"
    return info

"""
Chunking and embedding benchmark.

Indexes every (model x strategy) pair as its own collection, runs the labelled
evaluation set and prints a comparison, so the production collection is chosen by
measurement. Small chunks sharpen precision but cut context; large chunks keep
context but dilute the signal — which one wins on this corpus is not knowable
without running it.

Metrics are document-level: returned chunks are reduced to `doc_id` and
de-duplicated, so three chunks from one document are one hit, not three.

    python -m rag.bench
    python -m rag.bench --models e5-small
    python -m rag.bench --k 5 --json out.json
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass

from .chunk import STRATEGIES, chunk_all
from .embed import MODELS, get_embedder
from .evalset import EVAL_QUERIES, hit_at_k, reciprocal_rank
from .store import VectorStore, collection_name

# `retriever.py` caps context at ~2400 characters, roughly 380 words. Rows above
# this ask for chunks the prompt will never receive, so their measured hit rate
# is not achievable in production.
BUDGET_WORDS = 380


@dataclass
class BenchResult:
    model: str
    strategy: str
    chunks: int
    avg_words: float
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    mrr: float
    index_seconds: float
    query_ms: float
    coverage_at_k: float   # k / chunk count
    context_words: float   # words injected at top_k

    @property
    def degenerate(self) -> bool:
        """Is the search space too small for the metric to mean anything?

        With k=5 over 8 chunks, "top 5" is 62% of the corpus and hit@5 is
        essentially guaranteed — a measurement artefact, not retrieval skill.
        """
        return self.coverage_at_k >= 0.35


def _dedupe(doc_ids: list[str]) -> list[str]:
    seen: set[str] = set()
    return [d for d in doc_ids if not (d in seen or seen.add(d))]


def run_combination(model_key: str, strategy: str, k: int) -> BenchResult:
    embedder = get_embedder(model_key)
    embedder.verify_dim()

    store = VectorStore(dim=embedder.dim)
    store.ensure_schema()
    collection = collection_name(model_key, strategy)
    chunks = chunk_all(strategy)

    t0 = time.perf_counter()
    store.clear(collection)
    store.upsert(collection, chunks, embedder.encode_passages([c.content for c in chunks]))
    index_seconds = time.perf_counter() - t0

    hits1 = hits3 = hits5 = 0
    rr_total = 0.0
    query_times: list[float] = []

    for eq in EVAL_QUERIES:
        qt0 = time.perf_counter()
        hits = store.search(collection, embedder.encode_query(eq.query), k=k)
        query_times.append((time.perf_counter() - qt0) * 1000)

        ranked = _dedupe([h.doc_id for h in hits])
        hits1 += hit_at_k(ranked, eq.relevant, 1)
        hits3 += hit_at_k(ranked, eq.relevant, 3)
        hits5 += hit_at_k(ranked, eq.relevant, 5)
        rr_total += reciprocal_rank(ranked, eq.relevant)

    n = len(EVAL_QUERIES)
    avg_words = sum(c.word_count for c in chunks) / len(chunks)
    return BenchResult(
        model=model_key,
        strategy=strategy,
        chunks=len(chunks),
        avg_words=round(avg_words, 1),
        hit_at_1=round(hits1 / n, 3),
        hit_at_3=round(hits3 / n, 3),
        hit_at_5=round(hits5 / n, 3),
        mrr=round(rr_total / n, 3),
        index_seconds=round(index_seconds, 2),
        query_ms=round(sum(query_times) / len(query_times), 1),
        coverage_at_k=round(min(k, len(chunks)) / len(chunks), 3),
        context_words=round(avg_words * min(k, len(chunks)), 0),
    )


def render_table(results: list[BenchResult]) -> str:
    header = (
        "| Model | Strategy | Chunks | Avg words | hit@1 | hit@3 | hit@5 | MRR | "
        "Context (words) | Query (ms) | Note |\n"
        "|-------|----------|-------:|----------:|------:|------:|------:|----:|"
        "----------------:|-----------:|------|"
    )
    rows = [
        f"| {r.model} | {r.strategy} | {r.chunks} | {r.avg_words} | "
        f"{r.hit_at_1:.3f} | {r.hit_at_3:.3f} | {r.hit_at_5:.3f} | {r.mrr:.3f} | "
        f"{r.context_words:.0f} | {r.query_ms} | "
        f"{'narrow space' if r.degenerate else ''} |"
        for r in results
    ]
    return "\n".join([header, *rows])


def main() -> int:
    ap = argparse.ArgumentParser(description="Chunking/embedding benchmark")
    ap.add_argument("--models", nargs="+", default=sorted(MODELS), choices=sorted(MODELS))
    ap.add_argument("--strategies", nargs="+", default=list(STRATEGIES), choices=list(STRATEGIES))
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--json", metavar="FILE")
    args = ap.parse_args()

    print(f"Evaluation set: {len(EVAL_QUERIES)} queries, k={args.k}\n")

    results: list[BenchResult] = []
    for model_key in args.models:
        for strategy in args.strategies:
            print(f"  -> {model_key:10} {strategy:12} ", end="", flush=True)
            r = run_combination(model_key, strategy, args.k)
            results.append(r)
            print(f"hit@1={r.hit_at_1:.3f}  MRR={r.mrr:.3f}  ({r.chunks} chunks)")

    results.sort(key=lambda r: (-r.mrr, -r.hit_at_1))
    print("\n" + render_table(results))

    degenerate = [r for r in results if r.degenerate]
    if degenerate:
        print(f"\nSearch space too small for k={args.k} (top {args.k} is >=35% of the corpus):")
        for r in degenerate:
            print(f"    {r.model}/{r.strategy}: {r.chunks} chunks, {r.coverage_at_k:.0%} coverage. "
                  f"hit@{args.k} is near-guaranteed and does not indicate retrieval quality.")

    usable = [r for r in results if not r.degenerate]
    over_budget = [r for r in usable if r.context_words > BUDGET_WORDS]
    if over_budget:
        print(f"\nOver the ~{BUDGET_WORDS}-word context budget:")
        for r in over_budget:
            print(f"    {r.model}/{r.strategy}: k={args.k} needs ~{r.context_words:.0f} words. "
                  f"The excess never reaches the prompt.")

    affordable = [r for r in usable if r.context_words <= BUDGET_WORDS]
    pool = affordable or usable or results
    best = pool[0]

    print(
        f"\nRecommended: {best.model} / {best.strategy} — "
        f"MRR {best.mrr}, hit@1 {best.hit_at_1}, hit@3 {best.hit_at_3}, "
        f"{best.chunks} chunks, ~{best.context_words:.0f} words at k={args.k}."
    )
    if pool is affordable and affordable is not results:
        print("  (Narrow-search-space and over-budget rows were excluded; the raw MRR "
              "leader may be one of them.)")
    print(
        f"\n  RAG_EMBED_MODEL={best.model} RAG_CHUNK_STRATEGY={best.strategy} "
        f"python -m rag.ingest"
    )

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump([asdict(r) for r in results], fh, ensure_ascii=False, indent=2)
        print(f"\nJSON written: {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

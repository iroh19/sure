"""
EXP01 step 2 (read-only reproduction of rag/bench.py's metrics).

GUARDRAIL NOTE: the original `rag.bench.run_combination` clears and re-upserts
the collection under test (`store.clear()` + `store.upsert()`) before querying
it. The experiment execution guardrails for this run forbid any INSERT/UPDATE/
DELETE against the live `sure_rag` Postgres database. This script therefore
reproduces bench.py's per-query metrics (hit@1/3/5, MRR, coverage_at_k,
degenerate) by querying whatever is ALREADY indexed in each collection via
`store.search()` only -- no clear(), no upsert(). It does NOT re-index, so it
can only report on collections that already have rows (checked via
`store.count()` first and skipped, not fabricated, if empty).

This is a faithful reproduction of the query/scoring half of bench.py, not of
the indexing half. index_seconds is reported as None (not measured, since we
deliberately did not reindex).
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

SURE_LLM_SERVICE = Path("/Users/batuhancitak/Desktop/sure-project/llm-service")
sys.path.insert(0, str(SURE_LLM_SERVICE))

from rag.chunk import chunk_all  # noqa: E402
from rag.embed import MODELS, get_embedder  # noqa: E402
from rag.evalset import EVAL_QUERIES, hit_at_k, reciprocal_rank  # noqa: E402
from rag.store import VectorStore, collection_name  # noqa: E402

STRATEGIES = ("heading", "fixed-120w", "fixed-240w", "fixed-480w")


@dataclass
class ReadOnlyBenchResult:
    model: str
    strategy: str
    chunks_in_db: int
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    mrr: float
    query_ms: float
    coverage_at_k: float
    k: int

    @property
    def degenerate(self) -> bool:
        return self.coverage_at_k >= 0.35


def _dedupe(doc_ids: list[str]) -> list[str]:
    seen: set[str] = set()
    return [d for d in doc_ids if not (d in seen or seen.add(d))]


def run_readonly(model_key: str, strategy: str, k: int) -> ReadOnlyBenchResult | None:
    embedder = get_embedder(model_key)
    store = VectorStore(dim=embedder.dim)
    collection = collection_name(model_key, strategy)
    n_chunks = store.count(collection)
    if n_chunks == 0:
        print(f"  SKIP {collection}: 0 rows in DB (would require indexing, which is "
              f"forbidden by the read-only-DB guardrail)")
        return None

    hits1 = hits3 = hits5 = 0
    rr_total = 0.0
    query_times: list[float] = []
    for eq in EVAL_QUERIES:
        t0 = time.perf_counter()
        hits = store.search(collection, embedder.encode_query(eq.query), k=k)
        query_times.append((time.perf_counter() - t0) * 1000)
        ranked = _dedupe([h.doc_id for h in hits])
        hits1 += hit_at_k(ranked, eq.relevant, 1)
        hits3 += hit_at_k(ranked, eq.relevant, 3)
        hits5 += hit_at_k(ranked, eq.relevant, 5)
        rr_total += reciprocal_rank(ranked, eq.relevant)

    n = len(EVAL_QUERIES)
    return ReadOnlyBenchResult(
        model=model_key,
        strategy=strategy,
        chunks_in_db=n_chunks,
        hit_at_1=round(hits1 / n, 3),
        hit_at_3=round(hits3 / n, 3),
        hit_at_5=round(hits5 / n, 3),
        mrr=round(rr_total / n, 3),
        query_ms=round(sum(query_times) / len(query_times), 1),
        coverage_at_k=round(min(k, n_chunks) / n_chunks, 3),
        k=k,
    )


def main() -> int:
    k = 5
    print(f"Evaluation set: {len(EVAL_QUERIES)} queries, k={k} (READ-ONLY reproduction, "
          f"no reindexing performed)\n")
    results = []
    for model_key in sorted(MODELS):
        for strategy in STRATEGIES:
            print(f"  -> {model_key:10} {strategy:12} ", end="", flush=True)
            r = run_readonly(model_key, strategy, k)
            if r is not None:
                results.append(r)
                print(f"hit@1={r.hit_at_1:.3f}  MRR={r.mrr:.3f}  "
                      f"({r.chunks_in_db} chunks in DB)  degenerate={r.degenerate}")

    results.sort(key=lambda r: (-r.mrr, -r.hit_at_1))
    print("\n| Model | Strategy | Chunks (DB) | hit@1 | hit@3 | hit@5 | MRR | Query(ms) | Degenerate |")
    print("|-------|----------|------------:|------:|------:|------:|----:|----------:|:----------:|")
    for r in results:
        print(f"| {r.model} | {r.strategy} | {r.chunks_in_db} | {r.hit_at_1:.3f} | "
              f"{r.hit_at_3:.3f} | {r.hit_at_5:.3f} | {r.mrr:.3f} | {r.query_ms} | {r.degenerate} |")

    out_path = Path(__file__).parent / "bench_readonly_results.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump([asdict(r) | {"degenerate": r.degenerate} for r in results], fh, indent=2, ensure_ascii=False)
    print(f"\nJSON written: {out_path}")

    # cross-check: does chunk_all(strategy) local chunk count match store.count()?
    print("\nCross-check (local chunk_all() count vs DB row count, per strategy):")
    for strategy in STRATEGIES:
        local_n = len(chunk_all(strategy))
        db_n = next((r.chunks_in_db for r in results if r.strategy == strategy and r.model == "e5-small"), None)
        print(f"  {strategy}: local={local_n}  db(e5-small)={db_n}  "
              f"{'MATCH' if db_n == local_n else 'MISMATCH-or-not-indexed'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

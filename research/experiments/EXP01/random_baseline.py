"""
EXP01 step 3: random-retrieval baseline for the e5-small/heading collection.

Per experiment_design.json's EXP01 procedure and the resolved open_decision on
sampling scheme: for each EVAL_QUERIES query, draw k=5 chunk ids UNIFORMLY AT
RANDOM (with replacement across queries, without replacement within one draw)
from the full universe of chunks for the given strategy (`chunk_all(strategy)`
from the live sure-project code, read-only, no DB writes), fixed seed=42,
reported here. Metrics (hit@1/3/5, MRR) are computed with the exact same
`rag.evalset.hit_at_k` / `reciprocal_rank` functions bench.py uses, so the
comparison against the real retriever is apples-to-apples.

This script performs NO database writes (does not touch VectorStore at all --
the chunk universe is read directly from the knowledge/ markdown files via
chunk_all(), exactly as bench.py does before indexing).

Sampling scheme (open_decision, resolved here): uniform over ALL CHUNKS (not
uniform over documents then a chunk within), because that is what the real
per-chunk retriever (`store.search` returns individual chunks, deduped to
doc_id afterward) actually competes against -- the production system embeds and
ranks chunks, not documents.
"""
from __future__ import annotations

import json
import random
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

SURE_LLM_SERVICE = Path("/Users/batuhancitak/Desktop/sure-project/llm-service")
sys.path.insert(0, str(SURE_LLM_SERVICE))

from rag.chunk import chunk_all  # noqa: E402
from rag.evalset import EVAL_QUERIES, hit_at_k, reciprocal_rank  # noqa: E402

SEED = 42
K = 5
STRATEGY = "heading"  # matches the deployed e5-small:heading collection


@dataclass
class RandomBenchResult:
    strategy: str
    chunks: int
    k: int
    seed: int
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    mrr: float


def _dedupe(doc_ids: list[str]) -> list[str]:
    seen: set[str] = set()
    return [d for d in doc_ids if not (d in seen or seen.add(d))]


def run_random_baseline(strategy: str, k: int, seed: int) -> RandomBenchResult:
    rng = random.Random(seed)
    chunks = chunk_all(strategy)
    n = len(chunks)

    hits1 = hits3 = hits5 = 0
    rr_total = 0.0
    for eq in EVAL_QUERIES:
        sample = rng.sample(chunks, k=min(k, n))
        ranked = _dedupe([c.doc_id for c in sample])
        hits1 += hit_at_k(ranked, eq.relevant, 1)
        hits3 += hit_at_k(ranked, eq.relevant, 3)
        hits5 += hit_at_k(ranked, eq.relevant, 5)
        rr_total += reciprocal_rank(ranked, eq.relevant)

    nq = len(EVAL_QUERIES)
    return RandomBenchResult(
        strategy=strategy,
        chunks=n,
        k=k,
        seed=seed,
        hit_at_1=round(hits1 / nq, 3),
        hit_at_3=round(hits3 / nq, 3),
        hit_at_5=round(hits5 / nq, 3),
        mrr=round(rr_total / nq, 3),
    )


def main() -> int:
    print(f"Random-retrieval baseline (uniform over all {STRATEGY} chunks, "
          f"seed={SEED}, k={K}, no DB access)\n")
    result = run_random_baseline(STRATEGY, K, SEED)
    print(json.dumps(asdict(result), indent=2))

    # Repeat with a few other seeds to show the baseline is stable (sanity,
    # not part of the headline number -- headline uses seed=42 as declared).
    print("\nSeed-stability check (same strategy/k, seeds 1,2,3,42,100):")
    for s in (1, 2, 3, 42, 100):
        r = run_random_baseline(STRATEGY, K, s)
        print(f"  seed={s:4}  hit@1={r.hit_at_1:.3f}  MRR={r.mrr:.3f}")

    # e5-small/heading production figures (reproduced read-only in
    # bench_readonly.py this run): hit@1=0.793, MRR=0.856
    e5_hit1, e5_mrr = 0.793, 0.856
    margin_hit1 = round(e5_hit1 - result.hit_at_1, 3)
    margin_mrr = round(e5_mrr - result.mrr, 3)
    print(f"\ne5-small/heading (real retriever): hit@1={e5_hit1}  MRR={e5_mrr}")
    print(f"random baseline (seed={SEED}):       hit@1={result.hit_at_1}  MRR={result.mrr}")
    print(f"Margin: hit@1 +{margin_hit1}  MRR +{margin_mrr}  "
          f"(real retriever exceeds random by this much)")

    out_path = Path(__file__).parent / "random_baseline_results.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump({
            "seed42_result": asdict(result),
            "e5_small_heading_real": {"hit_at_1": e5_hit1, "mrr": e5_mrr},
            "margin": {"hit_at_1": margin_hit1, "mrr": margin_mrr},
        }, fh, indent=2)
    print(f"\nJSON written: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

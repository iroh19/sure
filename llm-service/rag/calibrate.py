"""
Calibrate the similarity threshold.

Bi-encoder retrieval returns the nearest chunk for every query, including ones
the corpus does not cover. A threshold on similarity is the only defence — but
cosine scores from models like e5 cluster in a narrow band (0.80-0.90), so a
guessed value like 0.72 filters nothing.

This compares the top-1 similarity distributions of the positive set
(`EVAL_QUERIES`) and the negative set (`NEGATIVE_QUERIES`) and sweeps candidate
thresholds. If the distributions overlap it says so rather than hiding it — in
that case the threshold only removes the worst negatives and the prompt's
"say so if you don't know" instruction is the real defence.

    python -m rag.calibrate
    python -m rag.calibrate --model e5-small --strategy heading
"""
from __future__ import annotations

import argparse
import statistics as stats

from .embed import MODELS, get_embedder
from .evalset import EVAL_QUERIES, NEGATIVE_QUERIES
from .store import VectorStore, collection_name


def _top1(embedder, store, collection, queries: list[str]) -> list[float]:
    out: list[float] = []
    for q in queries:
        hits = store.search(collection, embedder.encode_query(q), k=1)
        out.append(hits[0].similarity if hits else 0.0)
    return out


def _pct(values: list[float], q: float) -> float:
    s = sorted(values)
    return s[min(len(s) - 1, int(round(q * (len(s) - 1))))]


def _describe(name: str, values: list[float]) -> str:
    return (
        f"{name:10} n={len(values):3}  min={min(values):.3f}  p25={_pct(values, .25):.3f}  "
        f"median={stats.median(values):.3f}  p75={_pct(values, .75):.3f}  max={max(values):.3f}"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Calibrate RAG_MIN_SIMILARITY")
    ap.add_argument("--model", default="e5-small", choices=sorted(MODELS))
    ap.add_argument("--strategy", default="heading")
    args = ap.parse_args()

    embedder = get_embedder(args.model)
    store = VectorStore(dim=embedder.dim)
    collection = collection_name(args.model, args.strategy)

    if store.count(collection) == 0:
        print(f"Collection is empty: {collection}\nRun: python -m rag.ingest")
        return 1

    pos = _top1(embedder, store, collection, [q.query for q in EVAL_QUERIES])
    neg = _top1(embedder, store, collection, list(NEGATIVE_QUERIES))

    print(f"Collection: {collection} ({store.count(collection)} chunks)\n")
    print(_describe("positive", pos))
    print(_describe("negative", neg))

    overlap = max(neg) >= min(pos)
    print(
        f"\nSeparation: negative max {max(neg):.3f} "
        f"{'>=' if overlap else '<'} positive min {min(pos):.3f}"
        f"  ->  {'OVERLAP' if overlap else 'clean'}"
    )

    print("\n| Threshold | Positives | Negatives | Precision | Recall | F1 |")
    print("|-----------|----------:|----------:|----------:|-------:|---:|")

    rows: list[tuple[float, int, int, float, float, float]] = []
    lo, hi, step = min(min(pos), min(neg)), max(max(pos), max(neg)), 0.01
    t = round(lo - step, 2)
    while t <= hi + step:
        tp = sum(1 for s in pos if s >= t)
        fp = sum(1 for s in neg if s >= t)
        precision = tp / (tp + fp) if (tp + fp) else 1.0
        recall = tp / len(pos)
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        print(f"| {t:.2f} | {tp:9} | {fp:9} | {precision:9.3f} | {recall:6.3f} | {f1:.3f} |")
        rows.append((t, tp, fp, precision, recall, f1))
        t = round(t + step, 2)

    best_f1 = max(rows, key=lambda r: r[5])

    # Selection is precision-first, not F1. F1 weights the two errors equally and
    # ours are not equal: a missed positive leaves the model without context but
    # the rule engine still guarantees safety, while a passed negative hands it
    # irrelevant text to blend into a confident wrong answer with a citation.
    # So: the lowest threshold that lets no negative through.
    clean = [r for r in rows if r[3] >= 1.0 and r[1] > 0]
    if clean:
        chosen = min(clean, key=lambda r: r[0])
        reason = (f"lowest threshold with precision 1.000 "
                  f"(no negatives pass, {chosen[4]:.0%} of positives kept)")
    else:
        chosen = best_f1
        reason = "no threshold reaches precision 1.000 — fell back to best F1"

    print(f"\nBest F1  : {best_f1[0]:.2f} "
          f"(F1 {best_f1[5]:.3f}, precision {best_f1[3]:.3f}, recall {best_f1[4]:.3f})")
    print(f"Selected : {chosen[0]:.2f} — {reason}")
    if chosen[0] != best_f1[0]:
        print(f"  Trade-off: {len(pos) - chosen[1]}/{len(pos)} valid queries lose context. "
              f"There the model answers from its weights and the rule engine still decides.")

    if overlap:
        print(
            "\nThe distributions overlap: some negatives score above some positives, so a\n"
            "similarity threshold alone cannot reject out-of-domain queries. It still\n"
            "removes the worst of them, but the prompt instruction to decline unknown\n"
            "questions is the real defence. A cross-encoder reranker would separate them\n"
            "better than this corpus size justifies."
        )

    print(f"\n  RAG_MIN_SIMILARITY={chosen[0]:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

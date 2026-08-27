"""Aggregate aqua1b_results.jsonl / aqua7b_results.jsonl using the identical
aggregation logic bench_agent.py's own main() uses (format%, selection%, mean
steps, mean duration, constant-answer flag), computed separately for the
original-5 subset and the full expanded (n=9) set, for direct before/after
comparison, per EXP04's procedure step 4."""
import json
import statistics
from pathlib import Path

HERE = Path(__file__).parent


def load(stem: str) -> list[dict]:
    with open(HERE / f"{stem}_results.jsonl", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def aggregate(rows: list[dict], label: str) -> dict:
    n = len(rows)
    fmt = sum(r["format_ok"] for r in rows) / n
    scored = [r for r in rows if r["selection_ok"] is not None]
    sel = (sum(r["selection_ok"] for r in scored) / len(scored)) if scored else None
    mean_steps = statistics.fmean(r["steps"] for r in rows)
    mean_seconds = statistics.fmean(r["seconds"] for r in rows)
    chosen = [r["first_tool"] for r in rows if r["first_tool"]]
    constant = len(chosen) >= 3 and len(set(chosen)) == 1
    return {
        "label": label,
        "n": n,
        "format_pct": round(fmt * 100, 1),
        "n_scored_for_selection": len(scored),
        "selection_pct": round(sel * 100, 1) if sel is not None else None,
        "mean_steps": round(mean_steps, 2),
        "mean_seconds": round(mean_seconds, 2),
        "chosen_tools": chosen,
        "distinct_tools_chosen": sorted(set(chosen)),
        "constant_answer": constant,
    }


def main():
    for stem, model in (("aqua1b", "AQUA-1B"), ("aqua7b", "AQUA-7B")):
        rows = load(stem)
        original = [r for r in rows if r["origin"] == "original"]
        full = rows
        print("=" * 78)
        print(f"{model}  (adapter unset -- base model, matching bench_agent.py's own "
              f"'test the base model' framing)")
        print("=" * 78)
        for subset, label in ((original, "original n=5"), (full, f"expanded n={len(full)}")):
            agg = aggregate(subset, label)
            print(json.dumps(agg, indent=2, ensure_ascii=False))
        print()


if __name__ == "__main__":
    main()

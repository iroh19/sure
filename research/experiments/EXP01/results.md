# EXP01 — RAG Threshold Sweep Reproduction + Random-Retrieval Baseline

**Status:** success (strong criterion met)
**Git HEAD of sure-project at run time:** 3c1b9fa
**Environment:** `/opt/anaconda3/bin/python3` (Python 3.13.9), run from `llm-service/`, `RAG_DATABASE_URL=postgresql:///sure_rag` (default). All DB access was read-only (`store.search`, `store.count` only) — no `INSERT`/`UPDATE`/`DELETE` was issued against `sure_rag` at any point in this experiment, per the execution guardrails.

## Open decisions resolved

1. **Postgres auth path** (whether the anaconda python's psycopg resolves `postgresql:///sure_rag` without explicit user/password): confirmed working via peer auth — `VectorStore(dim=384).count('e5-small:heading')` returned `44` on the first try. No special DSN needed.
2. **Random-baseline sampling scheme**: resolved as uniform-over-all-chunks (not uniform-over-docs-then-chunk), because the production retriever (`store.search`) ranks and returns individual chunks, deduped to `doc_id` only after retrieval — chunks, not documents, are what real retrieval competes against. Documented in `random_baseline.py`'s docstring. Seed = 42 (fixed, reported; a 5-seed stability check is also included).

## Step 1 — `rag.calibrate` (read-only, unmodified)

Ran `python -m rag.calibrate --model e5-small --strategy heading` against the live `sure_rag` collection (44 chunks). Full output: `calibrate_output.log`.

- True F1-argmax: **threshold 0.84, F1 = 0.951** (precision 0.906, recall 1.000)
- Deployed threshold 0.85: **F1 = 0.906** (precision 1.000, recall 0.828)
- This reproduces the published figures exactly: F1-argmax at 0.84, deployed at 0.85, confirming H4's framing of 0.85 as a deliberate precision-favoring choice one step below the F1-argmax.
- Distributions **overlap** (negative max 0.847 ≥ positive min 0.841) — confirmed as-documented; a similarity threshold alone cannot fully separate in-domain from out-of-domain queries on this corpus.

## Step 2 — `rag.bench`-equivalent metrics (read-only reproduction)

**Guardrail note:** the real `rag.bench.run_combination` clears and re-upserts each collection before querying it (`store.clear()` + `store.upsert()`), which is a DELETE+INSERT against the production DB — forbidden by this run's guardrails. Instead, `bench_readonly.py` reproduces the query/scoring half of `bench.py` (identical `hit_at_k`/`reciprocal_rank` functions, identical dedup-by-`doc_id` logic) against whatever is **already indexed**, performing zero writes. A cross-check (`chunk_all(strategy)` local count vs. DB row count) confirmed the live DB content matches the current knowledge-base files exactly for all 4 strategies, so this is not a stale-data concern.

| Model | Strategy | Chunks (DB) | hit@1 | hit@3 | hit@5 | MRR | Degenerate |
|---|---|---:|---:|---:|---:|---:|:---:|
| e5-small | fixed-480w | 8 | 0.862 | 0.897 | 1.000 | 0.900 | **True** |
| e5-small | fixed-240w | 16 | 0.759 | 1.000 | 1.000 | 0.868 | False |
| **e5-small** | **heading** | **44** | **0.793** | **0.931** | **0.931** | **0.856** | **False** |
| tr-bert | heading | 44 | 0.724 | 0.931 | 1.000 | 0.833 | False |
| e5-small | fixed-120w | 28 | 0.690 | 0.966 | 0.966 | 0.828 | False |
| tr-bert | fixed-120w | 28 | 0.621 | 0.793 | 0.793 | 0.701 | False |
| tr-bert | fixed-240w | 16 | 0.517 | 0.759 | 0.828 | 0.638 | False |
| tr-bert | fixed-480w | 8 | 0.414 | 0.828 | 0.931 | 0.614 | **True** |

**e5-small/heading exactly reproduces the published figures: hit@1 = 0.793, MRR = 0.856.** `coverage_at_k >= 0.35` (`degenerate`) correctly fires for the two `fixed-480w` configurations (8 chunks, k=5 = 62% coverage) and correctly does NOT fire for `heading` (44 chunks, k=5 = 11% coverage) — the deployed collection's reported numbers are not a small-corpus measurement artefact in the `bench.py` sense.

## Step 3 — Random-retrieval baseline (new script, zero DB access)

`random_baseline.py` draws k=5 chunk ids uniformly at random (seed=42, `chunk_all('heading')` universe of 44 chunks — no DB queries at all, so this step has zero database interaction of any kind) for each of the 29 `EVAL_QUERIES`, scored with the identical metric functions.

| | hit@1 | MRR |
|---|---:|---:|
| e5-small/heading (real retriever) | 0.793 | 0.856 |
| Random baseline (seed=42) | 0.207 | 0.418 |
| **Margin** | **+0.586** | **+0.438** |

Seed-stability check (seeds 1, 2, 3, 42, 100): hit@1 ranges 0.138–0.310, MRR ranges 0.244–0.418 — the margin is not an artefact of one lucky/unlucky seed; the real retriever's hit@1 (0.793) and MRR (0.856) sit well above the entire observed random-baseline range.

**Honest caveat:** the random baseline's MRR (0.418) and hit@5 (0.724) are not near zero — with only **8 source documents** in the corpus, 5 randomly-drawn chunks (deduped to doc_id) span most of the document set by chance alone, so even random retrieval "hits" the right document reasonably often at k≥3. This is the same corpus-size effect `bench.py`'s own `degenerate` flag warns about, applied here to the baseline rather than the retriever under test. The margin at hit@1 (the strictest, least corpus-size-inflated metric) is the most defensible number: real retrieval is nearly 4x random chance at rank 1.

## Precision Check paragraph (for manuscript, citing sources 16 & 17)

> The deployed `RAG_MIN_SIMILARITY=0.85` is a precision-first choice, not the F1-optimum (0.84, F1=0.951) — trading 17.2 points of recall (0.828 vs. 1.000) for zero negative leakage (precision 1.000), because a missed positive costs the model context it can compensate for structurally (decline / defer to the rule engine), while a passed negative hands a 1B model irrelevant material to blend into a confidently-cited wrong answer. This design choice should be read against the retrieval-evaluation literature's own caution that precision/recall/F1 on a small, hand-labelled query set are per-corpus, per-model calibration artefacts, not portable guarantees (source 16), and against recent findings that embedding-similarity-based hallucination gating has certified, structural limits — the "Semantic Illusion" result and HALT-RAG's calibrated-abstention framing (source 17) both show that a similarity threshold, however well-calibrated, cannot fully substitute for an explicit uncertainty/abstention mechanism. The random-retrieval baseline measured here (hit@1 margin +0.586, MRR margin +0.438 over uniform-random chunk selection) establishes that e5-small/heading's reported skill is real semantic retrieval, not a corpus-size artefact — but the overlapping positive/negative similarity distributions found by `calibrate.py` (negative max 0.847 ≥ positive min 0.841) independently confirm source 17's caution: the threshold alone cannot cleanly separate in-domain from out-of-domain queries on this corpus, and the model's own "decline if unsure" prompt instruction is doing real, unmeasured work that a similarity cutoff cannot substitute for.

## Success criteria assessment

**Strong criterion: MET.** `calibrate.py`'s sweep reproduces F1-argmax at 0.84 exactly; `bench.py`'s degenerate flag reproduced correctly (read-only) for all 8 model/strategy combinations; the new random baseline shows a non-negligible, seed-stable margin; paragraph cites sources 16/17.

**Primary metrics:**
- F1-argmax threshold: 0.84 (F1 0.951) — reproduced exactly
- Deployed threshold F1: 0.85 (F1 0.906) — reproduced exactly
- e5-small/heading: hit@1=0.793, MRR=0.856 — reproduced exactly, read-only
- Random baseline: hit@1=0.207, MRR=0.418 (seed=42)
- Margin: hit@1 +0.586, MRR +0.438

## Files
- `bench_readonly.py`, `bench_readonly_output.log`, `bench_readonly_results.json`
- `calibrate_output.log`
- `random_baseline.py`, `random_baseline_output.log`, `random_baseline_results.json`

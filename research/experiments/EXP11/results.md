# EXP11 — Manuscript-Wide Stale-Figure Grep + Commit-Hash Provenance Table

**Status:** `success (finalized)` — see "FINALIZATION PASS" section below for the completed run.
The section immediately following this notice is the **original 4-of-11 partial run**, preserved
unmodified for its own historical accuracy (what was known and executed at that point in the
pipeline). It is superseded, not replaced, by the Finalization Pass section further down, which
now covers all 10 other experiments (EXP01–EXP10) and adds a consolidated list of every
stale/inconsistent figure found across the complete experiment set.

---

## [ORIGINAL PARTIAL RUN — preserved for history; see Finalization Pass below for the completed version]

**Original status:** `partial` — scoped down from the full EXP11 spec, honestly. Two reasons, both structural, neither a shortcut taken during execution:
1. **No manuscript draft exists yet.** `state.json` confirms `"current_phase": "experiment_track"`, `"finished": false` — EXP11's own open_decision #1 ("this experiment is not executable until a draft exists") is directly confirmed. There is nothing to grep except the pipeline's planning artifacts and the live repo itself, which is exactly what this run does.
2. **This execution pass covers only EXP02/EXP08/EXP09/EXP11** (a deliberate 4-of-11 subset). EXP01, EXP03–EXP07, EXP10 were not run here, so the full commit-hash provenance table (which depends on all of G1–G9's numbers) cannot be completed. This is reported as a gap, not concealed.

What **is** claimed as complete: the `minimum_viable` success criterion's core check — **the 0.695-vs-0.719 grep pass** — plus provenance for everything this run itself produced (EXP02, EXP08, EXP09), plus the recall figure's own git-verified correction chain. See `provenance_table.json` for the structured version of everything below.

Script: `g11_stale_figure_grep.sh`. Raw grep output: `grep_output.txt`.

## 1. The 0.695-vs-0.719 grep pass

**Result: PASS**, with one genuinely new finding (below) that the design pass's earlier inspection did not catch.

### In the live sure-project repo

`0.695` appears in exactly 4 text/doc files (YOLO label-file numeric coincidences in `data/frames/*.txt` and `data/sure_dataset/*/labels/*.txt` excluded — those are bounding-box coordinates, not metric citations):

| file | line | context |
|---|---|---|
| `MODEL_RAPORU.md` | 25, 135 | **Expected, not a leak** — inside the document's own 2026-08-26 correction note, explicitly narrating *why* 0.695 (epoch 73) was wrong and 0.719 (epoch 77) is correct. |
| `TODOS.md` | 11 | **Expected, not a leak** — a pre-existing, self-flagged-as-stale P2 planning item (per the design pass's own prior finding, re-confirmed here). |
| `llm-service/knowledge/06-davranis-ve-refah-gostergeleri.md` | 58 | **NEW FINDING — a genuine, live stale-figure leak.** See section 2 below. |

`0.719` appears correctly in every place vision recall is cited as a live, current number: `MODEL_RAPORU.md:15`, `README.md:19,384`, `README.tr.md:19,382`, `research_task.md:15` (and its identical copy at `pipeline/initial_context/research_task.md:15`).

### In the pipeline's own `initial_context/` and `paper_workspace/`

- `initial_context/`: same pattern as the live repo (it's a mirror of `MODEL_RAPORU.md`, `TODOS.md`, `README.md`, `research_task.md`) — 0.695 appears only inside the correction-note/self-flagged-stale contexts, 0.719 appears correctly everywhere recall is cited live.
- `paper_workspace/`: `0.695` appears in `research_goals.json`, `research_plan.md`, `novelty_assessment.json`, `track_decomposition.json`, `brainstorm.json/.md/_partial.md`, `research_proposal.md`, and three `persona_narrative_round_*.md` files. **Every single occurrence checked (all of them read in full for this pass) discusses the 0.695-vs-0.719 guardrail itself** — e.g. `research_proposal.md` line 190: *"The manuscript must state vision recall as 0.719 ... `TODOS.md` item #1 ... still carries the superseded figure of 0.695 ... this is a live hazard ... and the 0.695 figure must never appear in the manuscript."* None of these documents use 0.695 as a live claim. This is exactly the intended "process discipline already working" outcome.

## 2. New finding: a real stale-figure leak in the RAG knowledge base

`llm-service/knowledge/06-davranis-ve-refah-gostergeleri.md` line 58 states, as a live fact (not flagged as historical):

> **"Tespit modelinin recall'ı ~0.695'tir"** ("The detection model's recall is ~0.695")

This is **not** a dead planning document like `TODOS.md`. `llm-service/knowledge/` is the source directory `llm-service/rag/ingest.py` reads to populate the pgvector knowledge base (confirmed: `grep -l "knowledge" llm-service/rag/*.py` matches `chunk.py`, `ingest.py`, `evalset.py`, `thresholds.py`) — meaning this stale number is a candidate for retrieval and could be surfaced verbatim by the RAG-augmented LLM when answering a question about detection reliability or activity-metric limitations. This is a genuinely new, previously-undocumented instance of the exact hazard EXP11 exists to catch — distinct from the already-known/self-flagged `TODOS.md` case.

**Git-verified timeline of why this happened:**
- `0e8b414` (2026-08-26 **07:31:43** +0300, "Add RAG: pgvector knowledge base, measured chunking, calibrated threshold") — introduced this knowledge file, citing 0.695 (the epoch-73 number that was the accepted truth *at that moment*).
- `9a260af` (2026-08-26 **08:14:54** +0300, "Add edge export benchmark, and correct the reported detector metrics") — corrected the recall figure to 0.719 in `MODEL_RAPORU.md`/`README.md`/`README.tr.md`, **43 minutes later**, but did not touch `llm-service/knowledge/06-davranis-ve-refah-gostergeleri.md`.

This is a clean, git-provable "correction landed in the docs but not in the RAG corpus" gap — worth stating explicitly in the manuscript's Known Limitations / data-integrity section, since it directly affects what the deployed LLM can say to a user, not just what a reader of `README.md` sees.

**Not fixed here**, per the read-only guardrail on sure-project — reported for the writeup phase / a future commit to action.

## 3. Provenance table

Full structured version: `provenance_table.json`. Summary:

| number | value | commit | date | status |
|---|---|---|---|---|
| Vision recall (stale) | 0.695 | `d709836` | 2026-08-26 07:31:00+03:00 | superseded — epoch-73 numbers mislabeled as best.pt's |
| Vision recall (corrected) | 0.719 | `9a260af` | 2026-08-26 08:14:54+03:00 | authoritative — epoch-77, matches fresh `val()` to 4 decimals |
| RAG knowledge base's stale citation | 0.695 | `0e8b414` | 2026-08-26 07:31:43+03:00 | **not yet corrected** (new finding above) |
| EXP02 rule-path consistency (8/8) | — | measured against `3c1b9fa` | 2026-08-26 (this session) | this run |
| EXP08 PSI sweep + retrain gate | — | measured against `3c1b9fa` | 2026-08-26 (this session) | this run |
| EXP09 test suite (18/19 + 4 new) | — | `twin_bridge/` is **untracked**, no commit exists | file present as of this session | this run — see caveat below |

**twin_bridge provenance caveat:** `git status` shows `?? twin_bridge/` and `git log --oneline -- twin_bridge` returns nothing — this module has never been committed. Its "provenance" cannot be a commit hash; it can only be "file contents as read during this session, 2026-08-26." This is carried over from EXP09's own finding and repeated here because it directly affects what EXP11's provenance table can promise for that module.

## Coverage against EXP11's own success criteria

- **Strong criterion** ("100% of G1–G9 numbers have commit-hash provenance"): **NOT MET** — only EXP02/EXP08/EXP09 were run in this pass; EXP01/03/04/05/06/07/10 have no entries.
- **Minimum viable criterion** ("0.695-vs-0.719 grep passes; provenance for G1's RAG sweep, G3's eval.py run, G6's export_bench.py table"): **PARTIALLY MET**. The grep check passes (plus surfaces the new RAG-knowledge-base finding above). G3's eval.py rule-path has a close analogue here via EXP02, but G1 (RAG sweep) and G6 (export_bench.py) were not executed in this run — no fabricated numbers are supplied for them; they are left as open gaps for whichever run covers EXP01/EXP06.

## Open decisions resolved

1. *"No manuscript draft exists yet"* — reconfirmed directly via `state.json` (`current_phase: experiment_track`, `finished: false`) rather than assumed; this experiment's scope was executed as the QA-procedure dry run the design doc itself anticipates for this situation ("describes the QA procedure to run once that draft exists").
2. *"Should EXP01–EXP09 log commit hash/date live at run time?"* — Done for this run's own experiments: EXP02's script computes `git rev-parse --short HEAD` / `git log -1 --format=%cI` live and embeds it in `exp02_output.json`; EXP08's script does the same in `exp08_output.json`. This directly implements the recommendation this open_decision made, for the two experiments in this batch where it applied.

---

## FINALIZATION PASS — all EXP01–EXP10 now complete

All 9 other empirical experiments (EXP01–EXP09) plus the cross-layer framing decision (EXP10)
are now complete (`execution_log.json`). This pass re-runs the manuscript-wide stale-figure grep
against the now-complete experiment set, adds provenance entries for every remaining headline
number, and consolidates every stale/inconsistent/superseded figure found — not just 0.695-vs-0.719
— into one list. **No manuscript draft exists yet** (`state.json` still shows
`current_phase: experiment_track`, `finished: false`), so section 1 below is a re-verification
grep, not a first-time one; nothing in the repo or `paper_workspace/` changed between the original
pass and this one that would flip the grep result.

### F1. Re-verified: the 0.695-vs-0.719 grep pass still PASSES

Re-ran the same check against the current `sure-project` HEAD (`3c1b9fa`, unchanged) and the
now-complete `paper_workspace/`. Result is identical to the original pass: `0.695` appears only in
the two already-known, self-flagged-as-historical contexts (`TODOS.md:11`,
`MODEL_RAPORU.md:25,135`) plus the one live, unfixed leak in the RAG knowledge base
(`llm-service/knowledge/06-davranis-ve-refah-gostergeleri.md:58`, re-confirmed still present and
still uncorrected — see `provenance_table.json`'s `stale_and_inconsistent_figures[0]`). `0.719`
still resolves correctly everywhere it is cited as a live number. **No new occurrence of 0.695 was
introduced by any of EXP01/EXP03–EXP07/EXP10's own output artifacts** (all six were grepped as
part of this pass).

### F2. Full provenance coverage — strong success criterion now MET

Every one of EXP01–EXP09's headline numbers plus EXP10's framing-decision output now has a
provenance entry in `provenance_table.json`, each anchored to `sure-project` commit `3c1b9fa`
(2026-08-26T08:57:33+03:00) at measurement time, with finer-grained per-file commit history given
wherever a file has its own distinct commit (e.g. `mlops/drift.py`'s single commit; the two
distinct commits in the recall-figure correction chain) and explicitly flagged as **untracked**
wherever no commit exists (`twin_bridge/`, the `sure-aqua-adapter` LoRA weights). See
`provenance_table.json`'s `exp01_provenance` through `exp10_provenance` keys for the full detail;
summary:

| Exp | Headline number(s) | Commit anchor |
|---|---|---|
| EXP01 | F1-argmax 0.84/0.951; deployed 0.85/0.906; e5-small/heading hit@1 0.793/MRR 0.856; random baseline hit@1 0.207/MRR 0.418 | `3c1b9fa` |
| EXP02 | eval.py-vs-main.py rule agreement 8/8 | `45d42c7` (rule-engine single-source-of-truth extraction) |
| EXP03 | 4-bucket distribution (4/3/1/0 of 8); `test_decision.py` 18/18 | `3c1b9fa`; LoRA adapter is gitignored/untracked (mtime-only) |
| EXP04 | Constant-answer: AQUA-1B 0%/0% (n=5, n=9); AQUA-7B true (5/5, 9/9) | `3c1b9fa` |
| EXP05 | 32 near-duplicate pairs (strict threshold), 14 adjacent-index, 0 exact overlaps | `3c1b9fa` (dataset content, not individually commit-tracked) |
| EXP06 | Six-config table; CoreML p50 9.03±0.22ms; 0/98 ONNX-vs-TorchScript meaningfully different | `3c1b9fa`; baseline table from `9a260af` |
| EXP07 | 0/98 empirical full-frame misses; deployed-point P=0.720/R=0.782; F1-argmax conf=0.341 | `3c1b9fa` |
| EXP08 | Quantile vs equal-width PSI sweep; `decide()`/`gate()` three-way outcomes | `3c1b9fa` (only commit touching `mlops/drift.py`/`retrain.py`) |
| EXP09 | `test_bridge.py` 18/19 + 4 new tests | `twin_bridge/` **untracked**, no commit exists |
| EXP10 | Confirmatory literature search (no closer prior instance); CT-3 framing confirmed | `3c1b9fa` (not a codebase measurement) |

### F3. Consolidated list of stale/inconsistent/superseded figures — beyond 0.695

Six items total (full detail, severity, and recommendation for each in
`provenance_table.json`'s `stale_and_inconsistent_figures` array):

1. **[Already known, re-confirmed]** `llm-service/knowledge/06-davranis-ve-refah-gostergeleri.md:58` still states recall "~0.695" as a live fact and is ingested into the production RAG vector store. **Severity: HIGH** (production data-integrity bug). Not fixed (read-only guardrail).
2. **[NEW]** Vision recall has two distinct, both-genuinely-correct numbers depending on the question asked: **0.719** (F1-argmax/headline) vs. **0.782** (actual precision/recall at the deployed `conf=0.20` operating point, per EXP07). No current `paper_workspace/` artifact distinguishes them — Known Limitations item #1 in `research_proposal.md` only covers 0.695-vs-0.719, not this second ambiguity. **Severity: MEDIUM-HIGH — must be resolved/disclosed before manuscript freeze**, because it changes which number governs the H7 safety discussion (0.782 is the correct one to cite there, and it is the more reassuring figure, not less).
3. **[NEW]** `MODEL_RAPORU.md`'s own summary table states Precision=0.858, which is a rounding inconsistency against its own correction narrative's cited raw `val()` output (0.8590, which rounds to 0.859) two paragraphs earlier in the same document — propagated unchanged into `README.md`, `README.tr.md`, `research_task.md`. Independently re-confirmed as 0.859 by both EXP06 and EXP07's fresh reproductions. **Severity: LOW** (thousandths-place rounding nit, not safety-relevant).
4. **[NEW]** `README.md`'s published agent-benchmark table (AQUA-7B: format 60%, mean steps 3.6) has drifted from EXP04's fresh, code-unmodified reproduction (100% format, 2.0 mean steps) — selection% and the constant-answer conclusion reproduce exactly, format/step-count do not, with no configuration difference found to explain it (most likely `mlx-lm`/model-stack drift). **Severity: MEDIUM** — does not affect the negative-result conclusion, but is an unexplained, undocumented drift that the manuscript must footnote rather than silently pick one source for.
5. **[NEW]** EXP08's own internal PSI sweep table (delta=0.04 quantile PSI=0.728) is inconsistent with its own separately-drawn "significant-drift window" at the same nominal delta (PSI=0.9070) — an artifact of unseeded-per-call resampling variance within a fixed-seed script (the seed reproduces the whole run, not equal values across two separate calls at the "same" delta). **Severity: LOW**, self-contained within EXP08's own output; no headline manuscript number depends on the exact value of either intermediate figure.
6. **[NEW]** EXP05's near-duplicate leakage finding (32 pairs, 14 adjacent-index) is not yet reflected as a caveat anywhere the headline mAP50/precision/recall numbers are reported. **Severity: MEDIUM** — milder than the already-disclosed `ogretmen` leakage case, but a real, previously-undocumented risk to the same headline numbers reported without this caveat elsewhere.

**On the specific question of whether 0.719 vs. 0.782 needs resolution:** **Yes, unambiguously.**
Both numbers are correctly measured (0.719 is confirmed the true F1-argmax by EXP07's fine-grained
curve; 0.782 is the actual recall at the deployed `CONF_THRESH=0.20`), so this is not a bug to fix
in the code — but the manuscript currently has zero language distinguishing them, and citing 0.719
in the H7 safety-blind-spot discussion (as the pre-EXP07 proposal draft implicitly does) would
understate real-world recall, not overstate it. This is a required disclosure, not optional
polish, and is now recorded as `stale_and_inconsistent_figures[1]` with an explicit
recommendation.

### F4. Updated coverage against EXP11's own success criteria

- **Strong criterion** ("100% of G1–G9 numbers have commit-hash provenance"): **MET.** All of
  EXP01–EXP09 plus EXP10 now have entries in `provenance_table.json`.
- **Minimum viable criterion**: **MET AND EXCEEDED.** The 0.695-vs-0.719 grep still passes; all
  three originally-named highest-priority numbers (G1's RAG sweep, G3's eval.py+model-behavioral
  run, G6's export_bench.py table) now have full provenance entries, plus every other G1–G9 number
  and G10's framing output.

### F5. Manuscript-readiness handoff note

No manuscript draft exists yet as of this finalization (`state.json`:
`current_phase: experiment_track`, `finished: false`). `provenance_table.json` and the six-item
stale-figure list above (§F3) are handed to the writeup phase as the authoritative
pre-drafting reference — every number the manuscript cites should be checked against this table
before freeze, with items 2, 4, and 6 above requiring an explicit sentence of disclosure
(not merely a citation of the "correct" number) because in each case two different, both-real
numbers exist and the manuscript must say which one applies where and why.

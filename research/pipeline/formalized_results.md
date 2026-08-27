# Formalized Results — S.U.R.E. Applied-Systems Paper (project_000)

**Role:** Results Formalization Specialist. **Inputs:** `research_goals.json`, `track_decomposition.json`,
`track_merge_summary.md`, `theory_track_summary.json`, `experiment_track_summary.json`,
`experiment_design.json`, `verification_results.json`, `verification_handoff.md`, and all 11
`experiment_workspace/experiment_runs/EXP01`–`EXP11/results.md` files (read in full). Every claim
below carries a `source_file` pointer; the structured, machine-readable version of this document is
`formalized_results.json` in this same directory.

## Executive Summary

All 11 research goals (G1–G11) have sufficient, independently-verified evidence to write the
paper's Results section. **8 goals reach `achieved_strong`, 3 reach `achieved_minimum`
(G3, G5, G8), 0 are `partially_achieved`, `not_achieved`, `blocked`, or `not_attempted`.** This
matches `verification_handoff.md`'s "8 pass / 3 partial / 0 fail" experiment-level verdict,
recast here in goal-achievement vocabulary against each goal's own `strong`/`minimum_viable`
criteria in `research_goals.json`. No fabricated numbers, manufactured significance, or hidden
failures were found anywhere in the chain (design → execution → verification → this pass) — every
number re-checked here traces to a raw artifact on disk.

G5's previously open item — verification marked it `partial` because a corrected/caveated headline
vision number was never produced, only proposed — **is resolved in this pass** by directly
recomputing `model.val()` on the deployed checkpoint with the flagged near-duplicate validation
images excluded (see **G5 Resolution** below). G5 is accordingly assessed here as
`achieved_minimum`, not `partially_achieved`.

Six emergent findings were identified beyond the 11 planned goals (four already flagged by the
pipeline's own verification pass, two newly surfaced in this synthesis): AQUA-1B's fabricated
sensor values surviving inside "agreeing" outputs, a live stale-figure leak in the production RAG
knowledge base, the 0.719-vs-0.782 recall ambiguity, the zero-sparse-frame dataset-coverage gap,
an unexplained AQUA-7B agentic-benchmark reproducibility drift, and a counter-intuitive
INT8-loses-less-than-fp32 export finding. None require re-running an experiment before manuscript
freeze; several require explicit new disclosure sentences that do not yet exist anywhere in
`paper_workspace/` (see **Evidence Gaps**).

## Goal-by-Goal Results

### G1 — RAG Retrieval Calibration Reliability — `achieved_strong`
`calibrate.py`'s sweep reproduces the F1-argmax at threshold 0.84 (F1=0.951) against the deployed
0.85 (F1=0.906) exactly. A new random/no-retrieval baseline (authored this run, since `bench.py`'s
real path writes to the live production DB) shows e5-small/heading clears random by hit@1 +0.586
(0.793 vs. 0.207) and MRR +0.438 (0.856 vs. 0.418), stable across 5 seeds. Both `strong`-criterion
sub-requirements (sweep reproduction + quantified random baseline) are met.
*Source: `experiment_workspace/experiment_runs/EXP01/results.md`, `calibrate_output.log`,
`random_baseline_results.json`.*

### G2 — Eval-Harness / Production Rule-Path Consistency Audit — `achieved_strong`
`eval.py` and `backend/main.py`'s `apply_rule_override` are confirmed to resolve to the **exact
same in-memory `rules` module object** (Python `is` identity check), not merely matching output —
stronger evidence than the `strong` criterion required. 8/8 scenario agreement.
*Source: `experiment_workspace/experiment_runs/EXP02/results.md`, `exp02_output.json`.*

### G3 — Behavioral Measurement of the Dual-Layer Decision System — `achieved_minimum`
The 4-bucket distribution over AQUA-1B's 8 `eval.py` scenarios is unparseable-defaulted-to-ok 4/8
(50%), parseable-and-agrees 3/8 (38%), parseable-and-under-calls-and-escalated 1/8 (12%),
parseable-and-over-calls 0/8 (0%). This is the pre-registered `minimum_viable` fallback finding
("malformed-output fail-safe is the dominant observed pathway, not severity-correction") — the
`strong` criterion's implicit hope of clean severity-correction dominance is **not** met (only 12%
under-call-and-escalate). H2's non-enumerable-failure-mode requirement is exceeded: 6/8 (not
merely ≥1) reasoning strings contain fabricated sensor values. `backend/test_decision.py` (18/18)
is correctly kept separate as mechanism-correctness evidence, never substituted for the behavioral
finding. **Conservative per this audit's brief**: `achieved_minimum`, not `achieved_strong`.
*Source: `experiment_workspace/experiment_runs/EXP03/results.md`, `g3_results.json`.*

### G4 — Agentic Tool-Routing Negative-Result Robustness — `achieved_strong`
Fresh re-run plus 4 genuinely new scenarios (n=5→n=9) preserves and strengthens the negative
result: AQUA-1B 0%/0% on both n=5 and n=9; AQUA-7B's constant-answer flag holds on both n=5 (5/5
`get_sensor_trend`) and n=9 (9/9). Disclosed, not concealed: the published README's format%/mean-
steps (60%/3.6) does not reproduce (100%/2.0); no configuration difference found to explain it.
*Source: `experiment_workspace/experiment_runs/EXP04/results.md`, `aqua1b_results.jsonl`,
`aqua7b_results.jsonl`.*

### G5 — Vision Dataset Leakage Audit — `achieved_minimum` (upgraded by this audit; see resolution below)
The `strong` criterion (zero cross-split leakage beyond `ogretmen`) is **not** met: 32 near-
duplicate train/val pairs (≤5-bit aHash/dHash distance) across videos 2/4/5/6/7 and
`frame_source0`, 14 of them adjacent frame indices of the same source video (0 exact frame-index
overlaps — milder than, and distinct from, `ogretmen`'s already-corrected exact-duplicate leak).
`minimum_viable`'s first clause (enumerate affected files/videos) was already met by EXP05.
**The second clause — state a corrected, caveated headline number — was outstanding at
verification time and is closed by this audit; see G5 Resolution.**
*Source: `experiment_workspace/experiment_runs/EXP05/results.md`, `exp05_summary.json`.*

### G6 — Export-Format Accuracy Loss: Mechanism and Reproducibility — `achieved_strong`
Six-configuration table reproduced with commit hash. CoreML/ANE latency measured across 3
independent process invocations: p50 9.03±0.22ms, p95 9.60±0.18ms — genuine multi-session
variance, not a single sample. A new per-image ONNX-vs-TorchScript diff finds 0/98 images
meaningfully different (median matched-pair IoU 0.99999976) — stronger direct evidence for the
shared-post-processing-path claim than the design anticipated, with the honest caveat that this
confirms the two exports agree with *each other*, not a full pre-NMS isolation of the mechanism.
*Source: `experiment_workspace/experiment_runs/EXP06/results.md`, `run1_full_table.json`,
`g6_onnx_ts_diff_summary.json`.*

### G7 — Vision Operating-Point Safety Trace — `achieved_strong`
Fish-per-frame distribution computed directly from val labels (min k=3, avg 15.56). Full-frame-
miss rate quantified both empirically (0/98 at deployed conf=0.20) and via an independence
approximation (0.053 expected). Confidence-threshold sweep confirms 0.858/0.719 is (within curve
resolution) the true F1-argmax. **Must-disclose finding, correctly surfaced rather than
concealed**: the deployed operating point (conf=0.20) actually runs at P=0.720/R=0.782, materially
different from the headline academic-argmax the rest of the manuscript cites — this is exactly the
kind of falsifiable, numeric disclosure the `strong` criterion calls for, which is why this remains
`achieved_strong` rather than being downgraded.
*Source: `experiment_workspace/experiment_runs/EXP07/results.md`, `exp07_conf_curve_summary.json`,
`exp07_fish_per_frame_summary.json`.*

### G8 — MLOps PSI Drift-Binning Systematic Sweep & Three-Way Gate Exercise — `achieved_minimum`
The 16-point severity sweep precisely reports where quantile-vs-equal-width binning does and does
not separate cleanly: quantile is **more** sensitive at δ≤0.06 (δ=0.02: 0.164 vs. 0.078) — the
literal opposite of H5's "equal-width jumps early" wording — with equal-width overtaking and
becoming more explosive only from δ≥0.08 onward (δ=0.30: 4.844 vs. 7.649), mechanism confirmed via
per-bin decomposition. The `strong` criterion's qualitative-shape claim is corrected, not
confirmed, matching the pre-registered `minimum_viable` failure branch precisely. `retrain.py`'s
three-way `decide()` gate and the `gate()` MIN_IMPROVEMENT exercise both behave exactly as
designed. **Conservative per this audit's brief**: `achieved_minimum`, not `achieved_strong`.
*Source: `experiment_workspace/experiment_runs/EXP08/results.md`, `exp08_output.json`.*

### G9 — twin_bridge Mechanism-Evidence Inventory — `achieved_strong`
This fallback goal's success criteria equal its own `minimum_viable` ceiling, fully reached:
`test_bridge.py` (18 passed, 1 failed, root-caused to a test-helper float-truncation bug, not a
production defect); 4 new FakeTwin-scripted edge-case tests targeting a previously-unreached
`compare_once()` branch; the Results 5.6 paragraph states twin_bridge's status honestly as
unit-tested-only, never "validated."
*Source: `experiment_workspace/experiment_runs/EXP09/results.md`, `existing_test_bridge_run.log`,
`new_edge_case_test_run.log`.*

### G10 — Cross-Layer Thesis Framing & Confirmatory Literature Check — `achieved_strong`
Confirmatory search found no closer prior instance of the cross-layer thesis (C2); C2 correctly
kept OPEN/medium confidence. Framing CT-3 selected and refined against the real EXP03/EXP07/EXP08
findings (not the idealized pre-run narrative). All 11 `novelty_flags.json` claims cross-checked
against real data with zero status changes.
*Source: `experiment_workspace/experiment_runs/EXP10/results.md`,
`exp10_cross_layer_synthesis.md`, `exp10_literature_search.md`.*

### G11 — Manuscript-Wide Data-Integrity & Provenance Discipline — `achieved_strong`
Grep pass confirms the stale 0.695 figure never ships inside `paper_workspace` itself. Provenance
coverage reaches all of EXP01–EXP10, each anchored to commit `3c1b9fa` (finer per-file commits
given where they exist). The one live/unfixed 0.695 occurrence found (inside the production RAG
knowledge base) is a disclosed *finding* this goal exists to catch, not a failure of the goal.
*Source: `experiment_workspace/experiment_runs/EXP11/results.md`, `provenance_table.json`,
`grep_output.txt`.*

**Goal status summary:** 8 `achieved_strong` (G1, G2, G4, G6, G7, G9, G10, G11), 3
`achieved_minimum` (G3, G5, G8), 0 in any lower category.

## G5 Resolution — Special Task

`verify_completion.json` marked G5 `partial`: EXP05 enumerated the 32 near-duplicate train/val
pairs (14 adjacent-frame-index) but never produced a corrected/caveated headline vision number,
only proposed inserting a caveat sentence.

**Option (a) was chosen and executed** (not option b): raw val-set images/labels
(`data/sure_dataset/val/{images,labels}`) and the exact checkpoint behind every headline vision
number (`sure_models/sure_v1/weights/best.pt`) are both present and directly usable with
Ultralytics' existing `model.val()` — no retraining, no relabeling, and no modification of
`sure-project` was required, making a directly-computed number strictly better evidence than a
caveat sentence alone.

**Method**: from `exp05_summary.json`'s `strict_threshold_hits_detail` (the 32 pairs), two
exclusion sets were built: (1) the **13 distinct val images** touched by the **14 adjacent-frame-
index pairs** (the textbook temporal-adjacency leak pattern) → an 85-image filtered val set; (2)
the **17 distinct val images** touched by **all 32** strict-threshold pairs (a conservative bound)
→ an 81-image filtered val set. Filtered val splits were built via symlinks in a scratch directory
outside `sure-project` (the training split and repo files were never modified). `model.val()` was
re-run against `best.pt` for the unfiltered 98-image baseline and both filtered sets in the same
session for an apples-to-apples comparison.

**Result:**

| Val set | N | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|---:|
| Baseline (uncorrected, this session) | 98 | 0.859 | 0.719 | 0.8395 | 0.5952 |
| Corrected — excl. 13 images (14 adjacent-index pairs) | 85 | 0.852 | 0.712 | 0.8345 | 0.5877 |
| Corrected — excl. 17 images (all 32 strict pairs, conservative) | 81 | 0.846 | 0.712 | 0.8335 | 0.5869 |

The correction is real but modest: precision −0.7 to −1.3 points, recall −0.7 points, mAP50 −0.5
to −0.6 points, depending on which exclusion set is used — smaller than the already-disclosed
`ogretmen` exact-duplicate leak, and not conclusion-changing, but now measured rather than merely
flagged as "unquantified."

**Recommended manuscript caveat sentence** (for use alongside the headline numbers):

> "After excluding the 13–17 validation frames identified as near-duplicate (temporally adjacent)
> with training frames from the same source video, re-evaluation of the deployed checkpoint yields
> precision=0.846–0.852 / recall=0.712 / mAP50=0.8335–0.8345 (vs. the unfiltered headline
> 0.859/0.719/0.8395) — a modest, quantified optimistic bias of roughly 0.5–1.3 points depending on
> the exclusion threshold used."

**Honest limit of this resolution**: this is a same-checkpoint *re-evaluation* on a smaller held-
out set, not a retrain on a re-split, clip-disjoint dataset — the flagged near-duplicate training
frames remain in the training set that produced `best.pt`'s weights. It estimates the optimistic-
bias *direction and rough magnitude*, not a fully leakage-free number. A fully clean number would
require retraining after re-splitting by whole video/clip, which is out of this audit's scope and
recommended as follow-up work.

*Source: `experiment_workspace/experiment_runs/EXP05/g5_resolution_corrected_metrics.py` (new
script, this audit), `g5_resolution_corrected_metrics_full.json` (new raw output, this audit),
`exp05_summary.json`, `near_duplicate_pairs_full.json`.*

## Theory Track Summary

The theory track was **intentionally not run** — this is a deliberate empirical-only scope
decision made at the brainstorm/formalize_goals phase, not a gap or an incomplete track.
`track_decomposition.json` sets `recommended_track: "empirical"` and `theory_questions: []`,
honoring `brainstorm.json`'s own `track_recommendation.needs_theory_track = false`: the paper's
only four formalization needs (the `final_severity = max(severity_rule, severity_llm)`
monotonicity property, the enumerable/non-enumerable failure-mode distinction, the PSI-gating
three-way decision rule, and the vision operating-point tradeoff framing) are all expository
restatements of already-implemented code (`backend/main.py`'s `apply_rule_override`,
`mlops/drift.py`'s PSI pipeline, `mlops/retrain.py`'s `MIN_IMPROVEMENT` gate), not new mathematical
derivations — there is no unresolved convergence, statistical-learning-theory, or
optimization-theory question anywhere in the proposal that would justify a dedicated proof track.
Accordingly, these four items were folded as short Methodology-subsection prose directly into G3
(H1/H2), G7 (H7), and G8 (H5). No `math_workspace/` directory exists under `project_000/`,
confirmed on disk — this is the expected, correct state, requiring no remediation.
*Source: `paper_workspace/theory_track_summary.json`, `paper_workspace/track_decomposition.json`.*

## Experiment Track Summary

All 11 experiments (EXP01–EXP11) ran to completion with 0 failures: 8 verified `strong`, 3
verified `minimum_viable` (EXP03/G3, EXP05/G5, EXP08/G8). Every metric independently recomputed
from raw output files by `verification_results.json` matched the corresponding `results.md` figure
to within rounding noise (largest observed discrepancy: 0.09% relative, EXP07's argmax-F1 cell —
not conclusion-changing). No fabricated numbers, manufactured significance, or hidden failures were
found anywhere in the chain. Recommended presentation order (per `verification_handoff.md`,
unchanged by this pass): EXP02 → EXP03 → EXP04 → EXP01 → EXP06 → EXP07 → EXP05 → EXP08 → EXP09 →
EXP10 → EXP11.
*Source: `paper_workspace/experiment_track_summary.json`, `experiment_workspace/verification_results.json`,
`experiment_workspace/verification_handoff.md`.*

## Emergent Findings

Six findings were genuinely unexpected — not restatements of any G1–G11 planned deliverable —
verified against a specific artifact each:

1. **Fabricated sensor values inside "agreeing" AQUA-1B outputs** (EXP03): 6/8 scenarios contain a
   free-text reasoning claim with a fabricated sensor value; in 2 cases the model reaches the
   *correct* final status via an entirely invented causal narrative, invisible to any status-only
   check. *Source: `experiment_workspace/experiment_runs/EXP03/results.md`.*
2. **A live, unfixed stale-figure leak inside the production RAG knowledge base** (EXP11):
   `llm-service/knowledge/06-davranis-ve-refah-gostergeleri.md:58` states recall as "~0.695" as a
   live fact and is ingested into the production vector store — a retrievable, user-facing stale
   claim, git-provably introduced 43 minutes before the correcting commit and never fixed.
   *Source: `experiment_workspace/experiment_runs/EXP11/results.md`.*
3. **The 0.719-vs-0.782 recall ambiguity** (EXP07): the headline F1-argmax (0.719) and the actual
   deployed-operating-point recall (0.782) are both correct but govern different questions; the
   manuscript currently has no language distinguishing them, and 0.782 — the more reassuring figure
   — is the one that should govern the H7 safety discussion. *Source:
   `experiment_workspace/experiment_runs/EXP07/results.md`.*
4. **Zero sparse-frame (k=1/k=2) coverage in the validation set** (EXP07): the reassuring
   empirical 0/98 full-frame-miss result says nothing about the sparse-frame regime, which the val
   set does not contain at all — a dataset-coverage gap, not merely a rare-event finding. *Source:
   `experiment_workspace/experiment_runs/EXP07/results.md`.*
5. **AQUA-7B's agentic-benchmark format%/step-count figures do not reproduce** (EXP04): a fresh,
   code-unmodified re-run measures 100%/2.0 steps vs. the published README's 60%/3.6 steps, with no
   configuration difference found to explain it (most likely `mlx-lm`/model-stack drift) — the
   selection% and constant-answer conclusions reproduce exactly, but this specific figure does not.
   *Source: `experiment_workspace/experiment_runs/EXP04/results.md`.*
6. **INT8 quantization loses less accuracy than fp32 export** (EXP06): ΔmAP50 for INT8
   (−0.0082) is smaller in magnitude than for fp32 ONNX/TorchScript (−0.0104) — counter to the
   naive expectation that a more aggressively optimized format should lose more accuracy, and
   consistent with export/NMS-path mismatches (not weight precision) dominating the loss. *Source:
   `experiment_workspace/experiment_runs/EXP06/results.md`.*

## Evidence Gaps (Required Disclosures Before Manuscript Freeze)

No manuscript draft exists yet (`state.json`: `current_phase: experiment_track`,
`finished: false`) — every item below is a required *addition*, not a fix to existing prose.

| Priority | Item | Required action | Source |
|---|---|---|---|
| HIGH | Live 0.695 figure in the RAG knowledge base (EF2) | Fix the source file and re-ingest, or explicitly disclose if unfixed at freeze | `EXP11/results.md` |
| MEDIUM-HIGH | 0.719 vs. 0.782 recall ambiguity (EF3) | Add explicit disambiguating language wherever H7's safety discussion cites recall | `EXP07/results.md` |
| MEDIUM | G5's leakage caveat, now with a computed corrected range | Add the recommended caveat sentence (see G5 Resolution) next to every headline vision number | `EXP05/results.md`, this audit |
| MEDIUM | AQUA-7B format%/step-count drift (EF5) | Footnote wherever the agent-benchmark README table is cited | `EXP04/results.md` |
| LOW | 0.858-vs-0.859 precision rounding inconsistency | Normalize to one value across MODEL_RAPORU.md/README.md/README.tr.md | `EXP06/results.md`, `EXP07/results.md` |
| LOW | EXP08's internal PSI resampling inconsistency (δ=0.04: 0.7279 vs. 0.9070) | Footnote if both numbers are ever quoted together | `EXP08/results.md` |

## Follow-Up Recommendations

1. Retrain on a clip-disjoint re-split of `data/sure_dataset` for a fully leakage-free vision
   number, superseding both the uncorrected and this audit's same-checkpoint corrected estimate.
2. Fix the stale 0.695 figure in the RAG knowledge base and re-run `llm-service/rag/ingest.py`.
3. Add explicit 0.719-vs-0.782 disambiguating language to the manuscript's Discussion/Known
   Limitations.
4. Collect or synthesize genuinely sparse (k=1, k=2) validation frames to empirically test the
   full-frame-miss rate where the independence approximation currently substitutes for a
   measurement.
5. Investigate the `mlx-lm`/model-serving-stack version drift behind AQUA-7B's non-reproducing
   figures.
6. Re-seed EXP08's synthetic-window generator (or footnote the current unseeded-resampling
   variance).
7. For a fully isolated G6 mechanism test, compare raw pre-NMS regression/objectness outputs
   between `pt/mps` and the export formats directly.
8. Treat TB-3 (a live Godot/CODESYS session) as an optional upgrade to G9's baseline only, per its
   pre-registered fallback-goal status.
9. Normalize the 0.858-vs-0.859 precision figure to a single value before freeze.

## Files Produced by This Pass

- `paper_workspace/formalized_results.md` (this file)
- `paper_workspace/formalized_results.json`
- `paper_workspace/results_partial.json` (Phase A/B checkpoint)
- `experiment_workspace/experiment_runs/EXP05/g5_resolution_corrected_metrics.py` (new analysis script, G5 resolution)
- `experiment_workspace/experiment_runs/EXP05/g5_resolution_corrected_metrics_full.json` (new raw output, G5 resolution)

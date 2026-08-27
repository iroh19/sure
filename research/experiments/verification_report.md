# Verification Report — S.U.R.E. Experiments EXP01–EXP11

Verifier note: this pass treats all 11 experiments as deterministic systems-analysis
measurements (per the adapted brief), not stochastic ML training runs. "Reproduction" below
means independent recomputation of a primary metric from the raw output files already on disk,
compared against the number stated in each experiment's `results.md`. Sample sizes are small in
several places (n=8, n=9, n=98) and this is stated plainly wherever it bears on verdict strength.

---

## EXP01 — G1: RAG Retrieval Calibration Reliability

**Verdict: PASS. Goal satisfaction: STRONG.**

Independent recomputation from raw files:
- `calibrate_output.log`: sweep table read directly — F1-argmax at threshold 0.84 (P=0.906, R=1.000,
  F1=0.951); deployed 0.85 → P=1.000, R=0.828, F1=0.906. **Matches results.md exactly.**
- `bench_readonly_results.json`: e5-small/heading row — hit@1=0.793, MRR=0.856, degenerate=false.
  **Matches exactly.** Degenerate flag correctly fires only for the two `fixed-480w` rows (8 chunks).
- `random_baseline_results.json`: hit@1=0.207, MRR=0.418 (seed 42). Independently recomputed the
  margin: 0.793−0.207=0.586, 0.856−0.418=0.438. **Matches the reported margins exactly.**

No discrepancy found. Baseline sanity: the reproduced RAG figures (MRR 0.856, hit@1 0.793, F1
argmax 0.84) match vision.md's originally-reported figures verbatim, and the newly-added random
baseline (a genuinely new artifact, not just a check) shows a real, seed-stable margin — addressing
G1's own risk that a small 8-document corpus could make retrieval scores an artifact of corpus size.

**Small-n caveat:** the eval set is 29 queries (positive) + a small negative set (12) — small
enough that individual-query effects matter; this is disclosed in-line in results.md and does not
change the verdict.

---

## EXP02 — G2: Eval-Harness / Production Rule-Path Consistency Audit

**Verdict: PASS. Goal satisfaction: STRONG.**

Independent recomputation from `exp02_output.json`: 8/8 `scenario_results` entries have
`agree: true`; `overall_pass: true`; all three structural checks (`eval_py_imports_rules_via_syspath`,
`main_py_imports_same_rules_module_object`, `main_py_SEVERITY_is_rules_SEVERITY`) are `true`.
**Matches results.md's "8/8" and "all 3 structural checks: pass" exactly.**

This is a static/structural audit (deterministic by construction — same module object, `is`-identity
confirmed), so there is no reproduction-variance question; the executable check is the reproduction.
Scope is honestly bounded: the audit proves the two *rule-evaluation* paths are the same object, not
that `apply_rule_override`'s interaction with live model output is safe (that is EXP03's job) —
results.md states this caveat explicitly and it is accurate.

---

## EXP03 — G3: Behavioral Measurement of the Dual-Layer Decision System

**Verdict: PARTIAL. Goal satisfaction: MINIMUM_VIABLE** (all procedural strong-criterion checklist
items were completed, but the *substantive* headline finding lands on the pre-registered
minimum-viable framing, not the strong framing). **Recommendation: accept_as_minimum_viable.**

Independent recomputation from `g3_results.json`: recomputed the bucket tally directly from the
8 `rows` entries by counting `bucket` values — **agrees=3, under-calls-and-escalated=1, over-calls=0,
unparseable-defaulted-to-ok=4** (3/1/0/4 of 8). **Matches both the `bucket_counts` field in the same
JSON and the table in results.md exactly** (38%/12%/0%/50%).

This is the paper's central, most consequential experiment, and it is honestly reported: the
dominant pathway (50%, 4/8) is malformed-output-defaults-safe, not "LLM reasons, rule engine
corrects a genuine miss" (only 1/8 = 12%). `research_goals.json`'s own risk table pre-registered
this exact outcome as a legitimate, differently-framed safety claim, so this is not a failure —
but it means G3's **strong** criterion (implicitly hoping for clean severity-correction dominance)
is **not** met on the substance, even though every procedural deliverable (4-bucket table, adapter
provenance, `test_decision.py` 18/18 reported separately, ≥1 non-enumerable failure mode, Precision
Check paragraph) was produced.

Independently verified `test_decision.py`: 18/18 pass — this is mechanism-correctness evidence,
correctly kept separate from the behavioral result, exactly as required.

**Must state plainly: n=8 is the full population of eval.py's scenarios, not a sample** — the
50%/12%/0%/38% percentages should not be read as having any confidence interval; they are exact
counts over a small, fixed, hand-authored scenario set. The manual coding of the 8 reasoning
strings (6/8 fabricated, 1 accurate, 1 uncodable) is n=8 qualitative coding by one rater (this
experiment) and should be reported as such, not as a statistically powered finding.

**Adapter provenance** is mtime-only (gitignored, no git history) — disclosed, not concealed, but
worth carrying into Known Limitations since it means the exact LoRA training snapshot behind this
run cannot be pinned to a commit.

---

## EXP04 — G4: Agentic Tool-Routing Negative-Result Robustness

**Verdict: PASS. Goal satisfaction: STRONG** (with one disclosed reproduction discrepancy — see
Issues).

Independent recomputation from raw JSONL:
- `aqua7b_results.jsonl` (9 rows): `format_ok` is `True` for all 9 → 9/9 = 100%. All 9 rows have
  `first_tool == "get_sensor_trend"` → constant answer confirmed directly from the per-scenario log,
  not just the aggregate. Filtering to the 7 rows with non-empty `acceptable` lists and counting
  `selection_ok == True` gives **5/7 = 71.4%**. **All three numbers (100%, constant-answer=true,
  71.4%) match results.md exactly.**
- `aqua1b_results.jsonl` (9 rows): `format_ok` is `False` for all 9 → 0/9 = 0%. **Matches exactly.**

**Baseline sanity / discrepancy correctly disclosed, not hidden**: the published README table
states AQUA-7B format=60%/mean-steps=3.6; this fresh re-run measured 100%/2.0. Selection% (50%→50%
on original n=5) and the constant-answer conclusion reproduce exactly; format%/steps do not, and no
code-level cause was found (results.md attributes it to likely `mlx-lm`/model-stack drift and does
not claim a resolved cause). This is a genuine, disclosed discrepancy and is correctly listed as a
must-disclose item (see EXP11 cross-check below), not smoothed into "reproduced."

**Small-n caveat**: n=9 scenarios × 2 models. The negative result (AQUA-1B: 0%/0%) held identically
across all 4 new scenarios, which is meaningful evidence within this small sample, but 9 is still a
small n and the manuscript should say so rather than imply statistical power it doesn't have.

---

## EXP05 — G5: Vision Dataset Leakage Audit

**Verdict: PARTIAL. Goal satisfaction: MINIMUM_VIABLE** (strong criterion — zero cross-split leakage
— explicitly NOT met). **Recommendation: accept_as_minimum_viable**, contingent on the manuscript
actually adding the caveat language this experiment specifies (do not silently drop it).

Independent recomputation from `exp05_summary.json`:
- `n_source_groups_crossing_splits = 6`, matching group list `['frame_source0','video2','video4',
  'video5','video6','video7']` — **matches results.md exactly.**
- `exact_frame_index_overlaps_within_colliding_groups = 0` — **matches.**
- `near_duplicate_hits_per_threshold = {5: 32, 10: 202, 16: 902}`, `min_hash_distance = 2` —
  **matches the reported 32/202/902 and min-distance-2 exactly.**
- Independently recomputed the frame-index gap distribution from the 32 `strict_threshold_hits_detail`
  entries (`abs(train_idx − val_idx)`): **14 of 32 pairs have gap=1** — **matches the "14 of the 32
  candidate pairs" claim in results.md exactly** (this number is not present as a precomputed field
  in the JSON, so this recomputation is a genuine independent check, not a restatement).
- Positive control: `ogretmen_positive_control_leak_confirmed: true` — confirmed by direct read of
  `data/ogretmen.yaml` (train/val point at the same folder), validating the detection method.

This is a real, disclosed finding, not a methodology failure: the audit correctly distinguishes
"interleaved split of a continuous video" (real, milder issue) from the already-known
`ogretmen`-style exact-duplicate leak (worse, already excluded/corrected). The **strong** criterion
of "zero leakage beyond ogretmen" genuinely fails; the **minimum-viable** criterion (enumerate
affected files, propose a caveated headline) is met with specific, checkable numbers.

**Must-disclose**: per EXP11's cross-check (§ below), this caveat is *not yet* reflected anywhere
the headline mAP50/precision/recall numbers are reported in `paper_workspace` artifacts. This is a
live gap, not a hypothetical one.

---

## EXP06 — G6: Export-Format Accuracy Loss — Mechanism and Reproducibility

**Verdict: PASS. Goal satisfaction: STRONG.**

Independent recomputation:
- `run1_full_table.json`: pt-mps/pt-cpu mAP50=0.8395, mAP50-95=0.5952, precision=0.859 (0.8590
  rounds to 0.859), recall=0.719 (0.7189 rounds to 0.719); onnx & torchscript both mAP50=0.8291
  (Δ=−0.0104 vs pt), mAP50-95=0.5867 identical to 4dp. **Matches results.md's six-configuration
  table exactly**, including the −0.0104 ΔmAP50 reproduction of MODEL_RAPORU.md's headline claim.
- CoreML 3-session variance: recomputed mean/std directly from `run1_full_table.json` (session 1:
  p50=8.77, p95=9.64), `run2_coreml_only.json` (p50=9.30, p95=9.79), `run3_coreml_only.json`
  (p50=9.01, p95=9.36). Independent computation: **p50 mean=9.03, std=0.217; p95 mean=9.60,
  std=0.178.** **Matches the reported "9.03 ± 0.22" / "9.60 ± 0.18" exactly** (population-stdev
  convention, consistent with the small n=3).
- ONNX-vs-TorchScript diff (`g6_onnx_ts_diff_summary.json`): 0/98 images meaningfully different,
  1,479 matched pairs, 0 unmatched, median IoU 0.99999976. **Matches results.md exactly** — this
  is even stronger evidence for the shared-post-processing-path claim than the design's own success
  bar required, and results.md correctly declines to over-claim full mechanism isolation (states
  it shows the *symptom*, not a full isolation of which specific stage causes it — an honest,
  appropriately hedged conclusion).

**Baseline sanity**: −0.0082 to −0.0104 pp loss sits at the low end of, but within, the
literature-cited 0.5–2.0pp calibrated band (source 9) — plausible, not an outlier claim.

---

## EXP07 — G7: Vision Operating-Point Safety Trace

**Verdict: PASS. Goal satisfaction: STRONG**, with a mandatory manuscript disclosure obligation
(see Issues / Must-Disclose below) that is not yet satisfied anywhere in `paper_workspace`.

Independent recomputation:
- `exp07_fish_per_frame_summary.json`: `total_gt_fish=1525`, `n_val_images=98` →
  1525/98 = 15.561... **matches the reported "15.56 fish/frame" and MODEL_RAPORU's ~15.6 exactly.**
  Histogram confirms zero frames with k=0,1,2 — independently confirmed by scanning the histogram
  keys (minimum key is "3").
- `exp07_conf_curve_summary.json`: at conf=0.20020 (deployed), precision=0.72049→0.720,
  recall=0.78230→0.782, F1=0.75012→0.750. **Matches the "0.720/0.782/0.750" row exactly.** True
  F1-argmax on the fine curve: conf=0.34134, P=0.8447→0.845, R=0.7305→0.730, F1=0.78346. Headline
  (box.mp/mr) F1=0.78271. Delta = 0.78346−0.78271 = 0.00075. **Minor, immaterial rounding note**:
  results.md's table cell states the argmax F1 as "0.784" where the raw value (0.78346) rounds to
  0.783, and states the delta as "0.0008" where the raw value is 0.00075 (rounds to 0.0007 at 4dp).
  Both are thousandths-place rounding artifacts (<0.1% relative error) that do not change any
  conclusion — flagged here for completeness, not as a metric-extraction failure.
- Independently recomputed the extrapolated miss-risk figures: (1−0.719)¹=28.1%, (1−0.782)¹=21.8%,
  (1−0.719)²=7.9%, (1−0.782)²≈4.75%→4.7-4.8%. **All match results.md's reported figures.**

**The central finding of this experiment is itself a must-disclose issue, correctly surfaced**:
the deployed operating point (conf=0.20) actually runs at P=0.720/R=0.782, not the headline
academic-argmax P=0.858/R=0.719 the rest of the manuscript cites. Both numbers are independently
confirmed correct (0.719 is the true F1-argmax within curve resolution; 0.782 is the actual
deployed-point recall) — this is not a bug, it is an unresolved ambiguity about *which number
governs the safety discussion*, and per EXP11's cross-check, no current paper_workspace artifact
yet distinguishes them.

**Dataset-coverage gap (new observation, not previously itemized in EXP11's list)**: the 98-image
val set has **zero** frames with k=1 or k=2 ground-truth fish, so the reassuring "0/98 empirical
full-frame misses" result says nothing about the sparse-frame regime, which is exactly the regime
where the extrapolated 22–28% miss-risk would apply. This must be stated as an untested
extrapolation, not a measurement, and results.md does state this correctly — the risk is that this
distinction gets lost if condensed for the manuscript.

---

## EXP08 — G8: MLOps PSI Drift-Binning Sweep & Gate Exercise

**Verdict: PARTIAL. Goal satisfaction: MINIMUM_VIABLE** (the literal H5 hypothesis — "equal-width
saturates/jumps discontinuously" vs "quantile grades smoothly" — does not hold in the expected
direction at low severities; the mechanism is confirmed but the qualitative shape needed
correcting). **Recommendation: accept_as_minimum_viable** — this is exactly the pre-registered
minimum-viable failure branch ("if the sweep does not cleanly separate the two binning schemes at
every severity, report exactly where it does and does not"), and it was reported precisely rather
than smoothed over.

Independent recomputation from `exp08_output.json`:
- Full 16-point sweep read directly: at delta=0.02, quantile PSI=0.1639 (moderate) vs. equal-width
  PSI=0.0776 (none) — **confirms the reported "quantile PSI is actually higher/more sensitive... the
  opposite of equal-width jumps first" finding exactly**, this is a real inversion of the naive
  hypothesis, not a misreading.
- At delta≥0.08, equal-width PSI overtakes and exceeds quantile PSI (delta=0.08: 2.1412 vs 2.1842 —
  close; delta=0.30: 7.649 vs 4.844) — **matches results.md's "equal-width overtakes... and stays
  higher through delta=0.30 (7.65 vs 4.84)" exactly.**
- Retrain gate exercise: no-drift window → `action=none`, PSI=0.0048; significant-drift window
  (delta=0.04) → `action=retrain`, PSI=0.9070. **Matches exactly.**
- `gate()` three-case exercise: below-zero (fails), inside-noise-band (fails, +0.0025 < 0.005), above
  MIN_IMPROVEMENT (passes, +0.015). **Matches exactly.**

**Internal inconsistency, correctly self-flagged**: the sweep table's own delta=0.04 entry gives
quantile PSI=0.7279, but the separately-drawn "significant-drift window" (also delta=0.04) gives
PSI=0.9070 — I independently confirmed both raw values are present in `exp08_output.json` exactly
as reported. This is due to unseeded per-call resampling-with-replacement inside a fixed-seed
script (the seed reproduces the *whole run*, not per-call equality across two separate draws at the
nominal "same" delta) — a real methodological wrinkle, low severity (no headline manuscript number
depends on the exact intermediate value), but it should be named plainly in a footnote rather than
silently picking one of the two numbers.

`git log --oneline --all -- mlops/drift.py` independently re-confirmed to return exactly 1 commit,
supporting the "faithful reconstruction, not measured history" framing for the equal-width curve.

---

## EXP09 — G9: twin_bridge Mechanism-Evidence Inventory

**Verdict: PASS. Goal satisfaction: STRONG** (this goal's success criteria are explicitly defined
to equal its own minimum-viable form, and that ceiling was fully reached, including the mandated
honest "not validated" language).

Independently re-ran the reasoning, not the model (this is a deterministic pytest suite):
`existing_test_bridge_run.log` shows **18 passed, 1 failed** — `test_scaling_is_applied` fails with
`assert 8.11 == 8.12`, root-caused in results.md to `int(8.12*100)==811` (float truncation) in the
test helper, not in production `decode()`. Independently verified this arithmetic:
`int(8.12*100) == 811` and `round(8.12*100) == 812` are both true in Python — **the root-cause
claim is correct**, and correctly attributed to the test helper, not production code.

The 4 new `FakeTwin` edge-case tests are read and are genuinely new coverage (multi-alarm
divergence naming, an unmapped-alarm branch structurally unreachable via any existing test, and a
mixed agree/expected/unexplained session) — not a restatement of existing tests.

`twin_bridge/` is confirmed untracked (`git status --short` shows `?? twin_bridge/`, `git log
--oneline -- twin_bridge` returns nothing) — independently reconfirmed by me directly. This
provenance gap is disclosed correctly (mtime/session-only, not a commit hash) and does not
misrepresent itself as more than it is. The Results 5.6 paragraph's careful language ("designed and
unit-tested... not exercised against a live twin session... 'validated' never used") is accurate to
what was actually run — no live Godot/CODESYS session exists anywhere in the repo, confirmed by
the absence of any `.st`/Godot project files.

---

## EXP10 — G10: Cross-Layer Thesis Framing & Confirmatory Literature Check

**Verdict: PASS. Goal satisfaction: STRONG.**

This experiment is a synthesis/literature exercise, not a numeric-recomputation target — verified
by reading its own supporting artifacts (`exp10_literature_search.md`, `exp10_cross_layer_synthesis.md`)
and cross-checking its per-experiment claims against my own independent reads of EXP03/04/06/07/08/09
above: every claim it makes about those experiments (EXP03's 50%/12% split, EXP04's 5/5→9/9
strengthening, EXP06's near-bit-identical agreement, EXP07's operating-point correction, EXP08's
directional inversion, EXP09's honest-incompleteness) **matches what I independently found reading
the underlying results.md/raw files myself** — this experiment is not overstating or cherry-picking
the upstream results it synthesizes.

The novelty-flags walk-through (C1–C11) is conservative and correctly declines to upgrade any
claim's confidence from a negative search result (a search that fails to find a counter-example
cannot itself promote "medium" to "high" confidence) — methodologically sound reasoning, not
overclaiming.

---

## EXP11 — G11: Manuscript-Wide Data-Integrity & Provenance Discipline

**Verdict: PASS (at Finalization Pass). Goal satisfaction: STRONG.**

Independently re-ran the core checks against the live repo myself (not just reading the report):

- **`0.695` grep, confirmed independently**: found in exactly 4 non-label locations —
  `MODEL_RAPORU.md:25` (inside the correction note itself), `MODEL_RAPORU.md:135` (inside a
  historical "before/after retraining" table, `sed`-confirmed to be a distinct 5-epoch-vs-epoch-73
  comparison, not a live claim), `TODOS.md:11` (self-flagged stale), and
  `llm-service/knowledge/06-davranis-ve-refah-gostergeleri.md:58`. **All four locations and their
  characterization (3 historical/safe, 1 live/unfixed leak) match EXP11's claims exactly** — I
  read the actual file content at each location myself, not just trusted the grep summary.
- **RAG knowledge-base leak, confirmed real**: `sed -n '50,65p'` of the knowledge file shows line 58
  literally states "Tespit modelinin recall'ı ~0.695'tir" as a live fact inside a still-published
  knowledge document that `llm-service/rag/ingest.py` sources from — **this is a real, live,
  unfixed production data-integrity bug**, not a stale-planning-doc false positive.
- **`0.719` correctly cited live**: confirmed present and correct in `README.md:19,384`,
  `README.tr.md:19,382`, `MODEL_RAPORU.md:15`.
- **twin_bridge untracked**, independently reconfirmed via `git log --oneline -- twin_bridge`
  (empty) and `git status --short` (`?? twin_bridge/`).
- **Provenance table completeness**: `provenance_table.json`'s Finalization Pass section contains
  `exp01_provenance` through `exp10_provenance` keys — I note `exp02_provenance` is **not** a
  distinct top-level key in this JSON's finalization section (minor organizational gap); however,
  EXP02's number and its commit anchor (`45d42c7`, independently confirmed via `git log --oneline
  -- backend/rules.py` and `git cat-file -t 45d42c7` → `commit`, both real) are documented in the
  human-readable `results.md` summary table (both the original-partial-run section and the F2
  finalization table). The underlying provenance claim is not fabricated or missing, just organized
  across two places instead of one JSON key — **low-severity, cosmetic, does not change the verdict.**

The 6-item stale/inconsistent-figure list (§F3) was spot-checked point by point; all 6 are real,
independently confirmed via direct file reads or raw-data recomputation above (items 1, 3, 4, 5, 6
directly verified; item 2 — the 0.719-vs-0.782 ambiguity — independently re-derived from EXP07's raw
curve data, not merely re-stated).

**One addition this verification pass surfaces beyond EXP11's own 6 items**: EXP07's dataset-coverage
gap (zero k=1/k=2 val frames) is a genuine disclosure-worthy limitation on the "0/98 full-frame-miss"
claim that is not one of EXP11's 6 stale-figure items (it isn't a stale number, it's a coverage gap)
— recommend it be added to the paper's Known Limitations alongside the other 6.

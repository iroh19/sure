# S.U.R.E. — Approach Brainstorm (Final)

*Phase C synthesis of `brainstorm_partial.md`'s Phase A (divergent candidates) and
Phase B (feasibility/risk scoring). Grounded in `vision.md`, `research_proposal.md`
(Round 3 EXIT synthesis), `literature_review.md`, `literature_review_matrix.md`,
`novelty_flags.json`, and direct inspection of the live codebase at
`/Users/batuhancitak/Desktop/sure-project/` — every script, function, and file
named below was read, not assumed.*

---

## Executive Summary

This is an applied-systems paper about an already-built, already-measured
system. The overwhelming majority of what remains is **derivation from
existing logs/code** or **short new runs against existing checkpoints and
hardware** — not new infrastructure, and not new theory. 44 of the 48
approaches below are HIGH or MEDIUM feasibility; exactly **one** (`TB-3`,
a live `twin_bridge`↔Godot/CODESYS session) requires infrastructure genuinely
absent from this environment, and it is already scoped by the proposal as a
dated go/no-go stretch goal, not a blocking dependency.

The paper's real, defensible novelty locus — per the literature review's own
adversarial novelty check (`novelty_flags.json`, claim C2) — is **not** any
single mechanism (SIS/IEC 61511, RL shielding, champion-challenger MLOps, and
PSI credit-scoring binning conventions all pre-empt the individual
mechanisms). It is the **cross-layer consistency**: the same
escalation-only-deterministic-authority discipline, independently applied and
measured across five architecturally distinct layers of one deployed system,
including one full disclosed negative result. Every framing decision below is
built around foregrounding that claim honestly (medium, not high, confidence)
rather than overselling any individual layer's mechanism as an invention.

**Track recommendation: empirical-only.** No formal-proofs theory track is
warranted (see Track Recommendation section) — the "formalization" the
proposal already scopes (monotonicity as `max()` over a severity lattice,
enumerable vs. non-enumerable definitions, the PSI-gating decision rule) is
expository, not derivational, and belongs as a short Methodology subsection,
not a parallel research track.

---

## Restated Core Hypotheses (verbatim from `research_proposal.md`)

**Central Research Question:** In a deployed edge-AI aquaculture welfare
monitoring system, does giving deterministic, code-shared logic sole,
escalation-only final authority over five architecturally distinct,
independently probabilistic surfaces — LLM severity reasoning, LLM-driven
agentic tool routing, RAG retrieval, MLOps retrain triggering, and the edge
vision detection pipeline that supplies all four of these with their raw
sensor input — measurably reduce safety-relevant failure modes relative to
trusting each surface's own probabilistic output, and at what documented cost
to coverage, recall, or measurement rigor in each layer?

- **H1 — Escalation-only override reduces missed-escalation risk for enumerable thresholds.** `backend/rules.py` is imported unmodified by both the production decision path and the evaluation harness, and severity is only ever escalated, never lowered. Holds for hard, enumerable, numeric/categorical thresholds (e.g., DO < 6 mg/L).
- **H2 — The mechanism does not extend to non-enumerable failure modes.** The rule engine has no representation of free-text reasoning quality, citation accuracy, or open-ended judgment. The central claim must be scoped to "escalation-only deterministic override for enumerable safety thresholds," not general hallucination mitigation.
- **H3 — Deterministic tool-routing outperforms LLM-driven agentic tool selection at the deployed model scale.** AQUA-1B fails outright (0% parseable-action format, 0% correct selection); AQUA-7B's headline 50% selection rate is a constant-answer artifact, not genuine competence.
- **H4 — A precision-biased RAG threshold reduces hallucinated-citation risk at a quantified recall cost.** At threshold 0.85, hard-negative pass-through drops to 0/12 at the cost of positive recall dropping from 29/29 to 24/29 (F1 0.906 vs. F1-optimal 0.951 at 0.84).
- **H5 — Quantile-edge PSI binning detects graded drift where equal-width binning produces a degenerate binary signal.** Equal-width binning jumps PSI from 0.06 to 1.05 with no intermediate signal; quantile-edge binning grades smoothly (0.039 → 0.098 → 0.265 → 8.28) across increasing synthetic degradation.
- **H6 — Export-format accuracy loss is systematic and post-processing-attributable, not a stochastic "quantization tax."** ONNX/CPU and TorchScript/CPU exports match each other's mAP50 (0.8291) and precision loss to four decimal places; INT8 quantization (mAP50 0.8313, Δ −0.0082) pays a smaller cost than the fp32 export paths already pay (Δ −0.0104) before quantization is even applied.
- **H7 — The vision layer's operating point is itself a probabilistic input that a deterministic rule must tolerate, and the tolerance boundary is narrower than the headline recall number implies.** The only vision-consuming rule (`fish_count == 0` → `warning`) triggers on total per-frame absence, not per-instance miss rate; a systematic ~28% per-instance undercount does not, on inspection of the current rule set, trip any explicit escalation unless it zeros an entire frame.

**Central cross-layer thesis (novelty_flags.json, claim C2, OPEN, medium confidence):** the same deterministic-authority-over-probabilistic-component discipline, independently applied and empirically tested across all five layers within one deployed production system, including one full disclosed negative result — this cross-layer consistency, not any single layer, is the paper's central contribution.

---

## Per-Hypothesis Approach Menu

Each approach is tagged `[type, feasibility]` and marked **(S)** strengthens,
**(N)** neutral, or **(W)** weakens/complicates relative to every hypothesis
it touches — per the Anti-Retreat Rule, "weakens" here always means "produces
an honestly-reportable negative or complicating finding," never "grounds for
dropping the hypothesis."

### H1 — Escalation-only override (enumerable thresholds)

1. **H1-1 [analysis, HIGH]** — Execute the rewritten Goal 1 exactly: run `eval.py` in model mode (`AQUA_ADAPTER_PATH=./sure-aqua-adapter python3 eval.py`, the exact command already documented in `TODOS.md` item 2), capture each of the 8 scenarios' raw parsed model status, feed each through `apply_rule_override` (new small script importing `backend.main.apply_rule_override` and `backend.rules` directly), classify into the four buckets (agrees / under-calls-and-escalated / over-calls / unparseable-defaulted-to-ok). Record LoRA adapter provenance as a zero-cost sub-step. **(S) H1, H2** — this is the single largest evidentiary gap flagged across all three persona-council rounds.
2. **H1-2 [analysis, HIGH]** — Consistency audit: confirm `eval.py`'s `rule_status()` and `backend/main.py`'s `apply_rule_override`-embedded `rule_based_decision` compute identical severities today, i.e., verify the post-drift-bug single-source-of-truth fix fully holds, not just at the moment it was patched. **(S) H1** — protects the credibility of the drift-bug narrative itself.
3. **H1-3 [empirical, MEDIUM]** — Re-run H1-1's classification with a freshly-trained v2 LoRA adapter (128-sample `sure_finetune_data_v2.jsonl`, already present) and compare bucket distributions v1 vs. v2. **(S) H1; feeds Goal 8** — resolves the LoRA-provenance risk item outright instead of merely disclosing it.
4. **H1-4 [analysis/limitation, HIGH, safe baseline]** — Report `backend/test_decision.py`'s existing unit-test suite verbatim as mechanism-correctness evidence, explicitly separated from H1-1's behavioral evidence (zero execution cost beyond `pytest -v`). **(N) H1** — necessary complement, not a substitute for H1-1.
5. **H1-5 [framing]** — Related Work positioning options for C1 (EQUIVALENT_KNOWN vs. SIS/IEC 61511/RL shielding/guardrail blogs): (A) cite prior art explicitly and frame as "measured, deployed instance in a new domain"; (B) lead with the eval-harness-drift incident as the differentiator (matches the accepted Narrative Arc). **(N) H1, H2** — resolves C1's REFORMULATE recommendation either way.
6. **H1-6 [high-risk/high-reward, same run as H1-1]** — If AQUA-1B mostly produces unparseable output (mirroring `bench_agent.py`'s 0% finding), the story shifts from "LLM proposes, rule catches misses" to "malformed-output fail-safe is the dominant observed pathway." **(W→S) H1** — a different but still safety-relevant, still fully reportable finding; explicitly not a failed approach.

### H2 — Boundary: non-enumerable failure modes

1. **H2-1 [analysis, HIGH]** — Manually code H1-1's captured `reasoning` field text for factual/citation accuracy against each scenario's ground truth; doubles as Goal 8's pre-defined "decision quality" scoring. **(S) H2, H1** (feeds Goal 8).
2. **H2-2 [analysis, HIGH]** — Cross-reference with H4: at threshold 0.85, F1 is 0.906 (not 1.0), so residual hallucinated-citation risk exists and `rules.py` has zero representation of citation-accuracy checking. **(S) H2, H4** — zero new work, reuses existing data across hypotheses.
3. **H2-3 [framing]** — Cite RL-shielding's own enumerable/formal-safety-spec requirement (novelty C3) as independent corroboration rather than presenting H2's boundary as original theory. **(S) H2**.
4. **H2-4 [limitation-reporting, HIGH]** — State explicitly in a Discussion "Precision Check" paragraph that the architecture does not audit reasoning-field prose accuracy at scale; H2-1's n=8 audit is illustrative, not systematic. **(N) H2** — prevents overclaim (Risk Assessment row 4).

### H3 — Deterministic routing beats LLM-driven agentic tool selection

1. **H3-1 [analysis, HIGH, safe baseline]** — Report the existing `bench_agent.py` measurement verbatim (AQUA-1B 0%/0%; AQUA-7B 60% format/50%-flagged-constant-answer). **(S) H3** — zero new work.
2. **H3-2 [empirical, HIGH]** — Re-run `bench_agent.py` fresh near manuscript-freeze for a live reproducibility check; record commit hash/date. **(S) H3**.
3. **H3-3 [empirical, MEDIUM]** — Author genuinely new, distinct scenarios (not `--repeat`, confirmed to produce byte-identical output at `temp=0.0`) using the existing `Scenario`/`StaticDataSource` machinery, to actually grow n past 5. **(S) H3** — the only real fix to Ablation row 3; this is the proposal's own Goal 7(a).
4. **H3-4 [analysis, HIGH]** — Audit the constant-answer check itself against the actual logged AQUA-7B run to confirm `len(set(chosen)) == 1` genuinely held. **(S) H3** — protects the second-most-important number in this hypothesis.
5. **H3-5 [framing]** — Per C4 (PARTIAL): cite the majority-class/artifact-detection literature (arXiv:2402.12483) explicitly; reframe the "constant-answer-detection technique" as a known principle applied to a new task type, not an invention. **(N) H3**.
6. **H3-6 [high-risk/high-reward, same run as H3-3]** — If new scenarios dilute the constant-answer effect and AQUA-7B shows genuine, non-constant, above-chance selection, the clean "small LLMs categorically fail" narrative softens. **(W→S) H3** — must be reported in either direction.

### H4 — Precision-biased RAG threshold

1. **H4-1 [analysis, HIGH, do first]** — Recover and report the *full* threshold sweep table already produced by `rag/calibrate.py` (not just the 0.84/0.85 pair) — zero new infra. **(S) H4** — proposal's own Goal 3, explicitly flagged as lowest-risk, do-first item.
2. **H4-2 [analysis, HIGH]** — Report `rag/bench.py`'s own `degenerate` flag (`coverage_at_k >= 0.35`) alongside MRR/hit@k. **(S/N) H4** — the tool already computes this honesty check; just surface it.
3. **H4-3 [empirical, MEDIUM]** — Add a trivial random/no-retrieval baseline against the same `EVAL_QUERIES` to quantify how much of hit@1/MRR is corpus base-rate ease vs. genuine skill (Ablation row 2). **(S/W) H4** — the only approach that actually *measures*, rather than just discloses, this concern.
4. **H4-4 [framing]** — Per C5 (PARTIAL): cite per-corpus threshold-calibration literature and embedding-similarity hallucination-mitigation-limits literature explicitly; state 0.85 as corpus-specific. **(N) H4**.
5. **H4-5 [analysis/safe-baseline, HIGH]** — Report the asymmetric-cost selection logic already implemented and commented in `calibrate.py` verbatim as the methodology description. **(S) H4** — zero-cost, high narrative value.

### H5 — Quantile-edge PSI binning vs. equal-width

1. **H5-1 [analysis, MEDIUM]** — Recover the historical equal-width-binning failure via `git log`/`git blame` on `mlops/drift.py`; if not recoverable, reconstruct an equal-width variant and clearly label it as a reconstruction, not a historical measurement. **(S) H5** — needed to make the 0.06→1.05 claim independently verifiable.
2. **H5-2 [empirical, HIGH]** — Run a systematic synthetic-degradation sweep (mean-shift, variance-inflation, multiple severities) through both binning schemes using the existing `psi()`/`histogram()`/`bin_edges()` functions, producing a full curve instead of 4 anecdotal points. **(S) H5** — meaningfully strengthens the evidence base.
3. **H5-3 [framing]** — Per C8 (REFORMULATE): cite credit-scoring PSI-binning literature explicitly; reframe as "known best practice correctly applied to a structurally different, previously-unexamined narrow-band signal." **(N) H5**.
4. **H5-4 [analysis/safe-baseline, HIGH]** — Report the `MIN_IMPROVEMENT` champion-challenger gate (`mlops/retrain.py::gate`) verbatim, citing champion-challenger MLOps literature by name (C9, KNOWN). **(N) H5**.
5. **H5-5 [empirical, HIGH]** — Exercise `mlops/retrain.py::decide`'s full three-way decision path against synthetic no-drift and significant-drift windows, reporting the exact `Decision` output for each. **(S) H5** — closes the "PSI number → actual action" loop.

### H6 — Export-format accuracy loss is systematic

1. **H6-1 [analysis, HIGH, safe baseline]** — Report the full existing six-configuration `export_bench.py` table verbatim. **(S) H6** — zero new work.
2. **H6-2 [empirical, HIGH]** — Repeat the CoreML/ANE (and other format) latency measurement across multiple sessions on the same M4 Pro to report variance (Ablation row 1 / Goal 5). **(S/W) H6** — directly answers the "single favorable sample" concern.
3. **H6-3 [analysis, MEDIUM]** — Diff actual per-image detection outputs between ONNX and TorchScript exports on the 98-image val set to test the "shared post-processing path" causal claim beyond aggregate-metric matching. **(S/W) H6** — could upgrade H6 from correlational to mechanistically demonstrated, or force a weaker "coincidental match" framing.
4. **H6-4 [empirical, HIGH]** — Re-run `val()` on `best.pt` fresh at submission time; record exact commit/date (Ablation row 6). **(S) H6, H7** — live reproducibility check against a repeat of the epoch 73→77-class error.
5. **H6-5 [framing]** — Per C6 (PARTIAL): cite the GitHub issue threads (ultralytics/yolov5#8772, onnx/onnx#6287, microsoft/onnxruntime#21689) explicitly; frame the contribution as rigorous quantification/attribution, not discovery. **(N) H6**.
6. **H6-6 [high-risk/high-reward, same run as H6-3]** — If per-image outputs diverge despite matching aggregate mAP50, the causal story weakens. **(W→S) H6** — reportable either way.

### H7 — Vision recall's safety-relevant blind spot

1. **H7-1 [analysis, HIGH]** — Quantify how rare a full-frame miss actually is under 0.719 per-instance recall, using the val-set label distribution of fish-per-frame counts. **(S) H7** — turns a qualitative gap into a numeric, falsifiable one.
2. **H7-2 [empirical, HIGH]** — Run the PR-curve/operating-point sensitivity analysis at 2–3 alternate confidence thresholds via an Ultralytics `val()` sweep (Goal 6). **(S) H7** — H7's own stated empirical basis.
3. **H7-3 [analysis, HIGH]** — Compute the fish-per-frame distribution directly from val-set labels to ground or refute the "blind spot is narrow in practice" reading. **(S/W) H7** — could make the disclosed gap read as more, not less, urgent; report exactly what is found.
4. **H7-4 [framing]** — State H7 with real confidence, not hedged language — per C7 (OPEN, no equivalent trace found in the field's own reviews). **(S) H7**.
5. **H7-5 [limitation-reporting, HIGH]** — Carry the already-drafted Known Limitations #2 language verbatim into Discussion. **(N) H7** — zero-cost consistency.

### Central Cross-Layer Thesis (C2)

1. **CT-1 [framing, Option A]** — Foreground C2 as the headline claim: "first cross-layer empirical study of deterministic-override discipline applied uniformly across five heterogeneous AI subsystems in one deployed safety-critical system." **(S) all H** — maximizes visibility; risks overclaiming past "medium confidence."
2. **CT-2 [framing, Option B]** — Present each layer's specific contribution separately and let cross-layer consistency be a secondary, closing observation. **(N) all H** — safest, most conservative; undersells the paper's most distinctive claim.
3. **CT-3 [framing, Option C — hybrid, recommended]** — Open on the eval-harness-drift incident as the hook; state the cross-layer thesis as the organizing principle with the literature review's own explicit medium-confidence caveat attached. **(S) all H** — matches the already persona-council-accepted Narrative Arc.
4. **CT-4 [analysis/framing, MEDIUM]** — Execute the literature review's own recommended follow-up search ("multi-layer AI governance case study deployed system") before finalizing C2 as the headline claim. **(S/W)** — could confirm medium→high confidence, or surface a closer prior instance requiring a narrower claim.

### Sub-question 2 / `twin_bridge` (honest-limitation focus)

1. **TB-1 [limitation-reporting, HIGH, zero infra]** — Report exactly: "designed and unit-tested (`test_bridge.py`), not exercised against a live twin session; end-to-end cross-implementation corroboration remains future work." Never "independently field-validated" absent a live session. **(N) sub-Q2**.
2. **TB-2 [analysis, HIGH, zero infra]** — Report `test_bridge.py`'s actual coverage (agree/expected/unexplained branches, `EXPECTED_DIVERGENCE` mapping) as mechanism-correctness evidence, explicitly labeled as substituting for, not replicating, field validation. **(N) sub-Q2**.
3. **TB-3 [empirical, LOW — the one genuinely missing-infrastructure item in this entire brainstorm]** — Stand up `ras-digital-twin-main` (requires the Godot 4 engine binary, absent here) + a CODESYS soft PLC (manual GUI setup) + a new capture-adapter script (does not exist anywhere in the codebase) to produce a `{"holding": [...], "input": [...]}` capture file for `compare.py --replay`. **(S if achieved) sub-Q2** — the proposal's own dated go/no-go stretch goal; High likelihood of not landing per the Risk Assessment.
4. **TB-4 [analysis, HIGH, zero infra, NEW]** — Write a synthetic `FakeTwin`-scripted integration test (using the already-present `FakeTwin` dataclass in `twin_bridge/client.py`) sequencing hand-designed register frames spanning known edge cases (DO exactly at the 6.0 mg/L boundary, DO critical, ammonia-high-only, temperature-out-of-band-only) through `compare_once`'s full classification path. **Must be labeled precisely**: this is NOT cross-implementation corroboration (frames are team-scripted, not independent PLC logic) — it only exercises `twin_bridge`'s own comparison logic more thoroughly than the existing narrow unit tests. **(S, modest) sub-Q2** — a genuine, honestly-labeled middle ground between TB-1 and TB-3.

### Cross-Cutting

1. **XC-1 [analysis, HIGH]** — Vision dataset leakage audit beyond the `ogretmen` case: check the 412/98 train/val split for shared source video (filename/timestamp adjacency or perceptual-hash near-duplicates). **(S/W) H6, H7** — protects the validity of every vision-layer number.
2. **XC-2 [process, trivial]** — Pre-submission grep for "0.695" to guarantee the stale `TODOS.md` recall figure never ships. **(N)** — pure risk mitigation.
3. **XC-3 [process, trivial]** — Record git commit hash/date next to every re-measured number manuscript-wide, consolidating the discipline several individual approaches (H1-1, H3-2, H6-4) already apply piecemeal. **(N) all H**.

---

## Analysis-Track vs. Empirical-Track vs. Framing-Decisions Breakdown

**ANALYSIS TRACK** (pure derivation from existing logs/data/code, no new model or benchmark runs): H1-2, H1-4, H2-1\*, H2-2, H3-1, H3-4, H4-1, H4-2, H4-5, H5-1\*, H5-4, H6-1, H6-5\*\*, H7-5, TB-1, TB-2, XC-2, XC-3.
(\*H2-1 depends on H1-1's output but is itself pure analysis once that data exists. \*\*H6-5 is a framing decision executed as a citation, listed here for the "zero new run" property.)

**EMPIRICAL TRACK** (new eval/benchmark runs against existing models/hardware, no new physical deployment): H1-1, H1-3, H3-2, H3-3, H4-3, H5-2, H5-5, H6-2, H6-3, H6-4, H7-1\*, H7-2, H7-3\*, TB-4.
(\*H7-1/H7-3 are small analysis scripts over existing val-set data/predictions but are grouped here because they require running/re-deriving a distributional count, not pure code inspection.)

**FRAMING/WRITING DECISIONS** (narrative and citation choices, not runs): H1-5, H2-3, H2-4, H3-5, H4-4, H5-3, H7-4, CT-1/CT-2/CT-3 (mutually exclusive — pick one), CT-4 (has an analysis component — a literature search — but resolves a framing question).

**EXPLICIT MISSING-INFRASTRUCTURE CATEGORY** (requires something genuinely absent from this environment): **TB-3 only.** Everything else in this brainstorm is executable today with the codebase, cached model weights, and the existing M4 Pro hardware.

**Parallelizable groups** (no shared dependency, can run concurrently):
- Group P1: H1-1/H1-2 (LLM decision layer) ‖ H4-1/H4-2/H4-3 (RAG layer) ‖ H5-1/H5-2/H5-5 (MLOps layer) ‖ H6-1/H6-2/H6-4 (vision export) ‖ TB-1/TB-2/TB-4 (twin_bridge) — five independent layers, five independent people/sessions could run these simultaneously.
- Group P2 (depends on P1 outputs): H1-6 and H2-1/H2-2 depend on H1-1's output; H3-6 depends on H3-3's output; H6-6 depends on H6-3's output; H7-1 benefits from (but does not strictly require) H6-4's fresh `val()` run.
- Sequencing note: **Results 5.1 cannot be written before H1-1 completes.** Results 5.4 should start with H4-1 (explicitly the lowest-risk, do-first item per the proposal). CT-4's literature search, if run, should happen before the Abstract/Introduction are drafted, since it could narrow C2's claim.

---

## Ablation Design Matrix (cross-referenced to `research_proposal.md`'s 10-row table)

| # | Alternative Explanation to Rule Out | Executing Approach(es) |
|---|---|---|
| 1 | Edge latency advantage is a batch-size-1/single-device/thermal artifact | **H6-2** |
| 2 | High RAG hit@1/MRR is inflated by small, low-overlap corpus | **H4-2** (disclose) + **H4-3** (measure) |
| 3 | Agent benchmark (n=5, 2 models) too small to generalize | **H3-3** (genuine fix) + **H3-2** (repro check) |
| 4 | LLM contributes nothing but narration | **H1-1** + **H1-6** + **H2-1** |
| 5 | INT8 "beating" fp32 ONNX is validation-set noise, not a real effect | **H6-1** (report as-is) + **H6-5** (honest framing, do not restate as "INT8 improves accuracy") |
| 6 | An undiscovered analogous error (epoch 73→77-class) may still exist | **H6-4** |
| 7 | Vision split may contain subtler leakage than the `ogretmen` case | **XC-1** |
| 8 | PSI drift-gating implies field validation it hasn't received | **H5-3** (explicit synthetic-only labeling) |
| 9 | `twin_bridge`'s clean code could be mistaken for live-validated | **TB-1** + **TB-2** (and **TB-4** if executed, still labeled correctly) |
| 10 | Vision recall (0.719) reads as a self-contained number with no safety consequence | **H7-1** + **H7-2** + **H7-3** + **H7-5** |

Every ablation row has at least one HIGH-feasibility executing approach; none require `TB-3`-class missing infrastructure.

---

## Cross-Cutting Observations

1. **The paper's two most confidently-novel single-hypothesis claims are H7 (C7, OPEN) and the central cross-layer thesis (C2, OPEN).** Every other individual mechanism (H1/H2's override pattern, H3's routing decision, H4's threshold calibration, H5's binning fix, H6's export diagnosis) has at least PARTIAL or EQUIVALENT_KNOWN prior art. Approaches H7-4 and CT-1/CT-3 should therefore carry the most confident, least-hedged language in the manuscript; H1-5, H3-5, H4-4, H5-3, H6-5 should all carry explicit "known pattern, here applied and measured" framing.
2. **Several approaches reuse the same underlying data across hypotheses** (H2-1/H2-2 reuse H1-1/H4 output; H7-1 benefits from H6-4's fresh val run; XC-3's provenance discipline wraps H1-1/H3-2/H6-4). Sequencing these correctly avoids redundant runs.
3. **The riskiest approaches to core claims are exactly the ones the proposal's own Risk Assessment already names**: H1-6 (LLM may be narration-only or mostly unparseable), H3-6 (new scenarios could soften the "small LLMs fail" claim), H6-6 (per-image diff could undercut the "shared post-processing path" causal story). None of these are reasons to skip the approach — per the Anti-Retreat Rule, an unfavorable result here is itself a legitimate, reportable finding.
4. **The codebase already does more self-disclosure than the proposal's prose credits it for**: `rag/bench.py` computes its own `degenerate` corpus-size flag; `rag/calibrate.py` already states its asymmetric-cost reasoning in code comments; `mlops/drift.py`'s own docstring narrates the equal-width failure mode. Several "approaches" above (H4-2, H4-5, H5-4) are really just "surface what the code already says," at effectively zero cost.
5. **No approach in this brainstorm requires deleting or softening any of the seven core hypotheses.** The one sub-question with a real infrastructure gap (`twin_bridge` live corroboration, TB-3) has three non-infrastructure-dependent fallback approaches (TB-1, TB-2, TB-4) that keep it honestly represented without inventing evidence.

---

## Track Recommendation

**Recommendation: empirical/systems track only. No parallel formal-proofs theory track.**

Justification: `research_proposal.md`'s own "Analysis/Theory-equivalent Plan" already scopes exactly what formalization this paper needs — a precedence relation (`final_severity = max(severity_rule, severity_llm)`), a precise enumerable/non-enumerable distinction, and a decision-rule description of the PSI-gating pipeline — and explicitly labels this "not new proofs, but rigor-grade formalization of what is already implemented." None of this requires deriving anything; it requires *stating precisely* what the code (already read, above) already does. There is no unresolved mathematical question in this system that would benefit from a dedicated proof track (no convergence claims, no statistical-learning-theory claims, no optimization-theory claims are made anywhere in the proposal). Spinning this out as a parallel track would create apparatus without content, directly contradicting Known Limitations #11's own warning that the proposal's apparatus has grown every round and needs compression, not addition.

The correct home for this formalization is a short (~1 page) subsection inside
Methodology / System Architecture, written during the empirical track's
writeup phase, using the definitions the proposal has already drafted
verbatim (the monotonicity property, the enumerable/non-enumerable boundary,
the three-way PSI decision, the vision operating-point-as-tradeoff framing).
It should not appear as its own `track_decomposition` branch with its own
approach list, dependencies, or deliverables.

---

## Recommended Priority Ordering (top approaches to actually execute)

Ordered by a combination of (a) blocking-dependency status for the mandated Results skeleton, (b) feasibility, and (c) the proposal's own explicit sequencing hints ("do this first," "highest priority, zero blocking dependency").

1. **H4-1** — Recover the full RAG threshold sweep from `rag/calibrate.py`. Trivial, zero risk, explicitly flagged in the proposal as the lowest-risk "proof of competence" item to do first. Unblocks Results 5.4.
2. **H1-2** — Consistency audit of `eval.py`'s rule path vs. `apply_rule_override`'s rule path. Quick, protects the credibility of everything H1-1 will report.
3. **H1-1** — The rewritten Goal 1: model-mode `eval.py` run → `apply_rule_override` → four-bucket classification + LoRA adapter provenance. The single highest-priority item in the entire proposal; blocks Results 5.1 and feeds H2-1.
4. **H6-4** — Fresh `val()` run on `best.pt` at submission time, with commit hash recorded. Protects every downstream vision-layer number (H6, H7) before further vision work is reported.
5. **XC-1** — Vision dataset leakage audit beyond `ogretmen`. Also protects the validity of headline vision numbers; cheap, should run alongside #4.
6. **H6-2** — Multi-session CoreML/ANE latency variance measurement. Directly answers Ablation row 1; unblocks a fully-qualified Results 5.3.
7. **H5-2** — Systematic synthetic-degradation sweep through both PSI binning schemes. Turns H5's 4 anecdotal numbers into a reproducible curve; unblocks a fully-evidenced Results 5.5.
8. **H3-3** — Author genuinely new `bench_agent.py` scenarios to grow n past 5. The only real fix to the agent-benchmark sample-size concern (Ablation row 3); medium effort, schedule after the quicker wins above, but must complete before Results 5.2 can claim more than the existing n=5.

*(Not in the top 8, but recommended as a fast follow given how cheap it is: **TB-4**, the `FakeTwin`-scripted synthetic edge-case test — it strengthens Results 5.6's honest-limitation section at near-zero cost and requires no missing infrastructure.)*

---

## Open Questions

1. Will `TB-3`'s live `twin_bridge` session (Godot 4 + CODESYS + a not-yet-written capture adapter) realistically land before the proposal's own dated go/no-go checkpoint, given the infrastructure gap confirmed by direct inspection of this environment?
2. Is **H1-3** (retraining a v2 LoRA adapter to resolve provenance ambiguity outright) worth the time before manuscript freeze, or should the paper simply disclose whichever adapter (v1 or v8) is currently deployed without retraining — i.e., does Goal 8's dependency on this justify the extra empirical work?
3. Should **CT-4**'s additional literature search ("multi-layer AI governance case study deployed system") be run before the Abstract/Introduction are drafted, given it could narrow the central C2 claim — and if it surfaces closer prior art, how much rewriting does that force?
4. How much will the length/venue compression pass (Known Limitations #11, not yet resolved) end up cutting, and does that change which of the top-8 priority approaches survive into the final manuscript versus being compressed into a footnote or appendix?
5. If **H3-3**'s new scenarios shift AQUA-7B's apparent tool-selection competence upward, does the Motivation section's "evidence-driven abandonment of LLM tool routing" framing need to be re-litigated, or does it still hold at the deployed AQUA-1B scale regardless of AQUA-7B's behavior?
6. If **H6-3**'s per-image diff (a stretch item, not in the top 8) shows ONNX and TorchScript detections do *not* closely match despite matching aggregate mAP50, does H6's "shared post-processing path" causal claim need to be walked back to "coincidental match, mechanism unconfirmed" — and how much does that weaken H6's standing as a named Results subsection?
7. If **H7-1**/**H7-3**'s quantification of the frame-level fish-count distribution shows many val-set frames are sparse (1–2 fish), does the disclosed H7 blind spot read as *more* urgent than the current draft implies — and should that change the Expected Contributions/Practice guideline #6 from a general caution into a more specific numeric warning?

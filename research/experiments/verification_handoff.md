# Verification Handoff — EXP01–EXP11

Overall: **8 pass / 3 partial / 0 fail** across the 11 experiments. No fabricated numbers,
manufactured significance, or hidden failures were found. Every metric independently
recomputed from raw output files on disk matched the corresponding results.md figure to within
rounding noise (largest observed rounding artifact: 0.09% relative, in EXP07's argmax-F1 table
cell — not conclusion-changing).

---

## Fully Passed Experiments (goal_satisfaction: strong)

| Exp | Goal | Why it passed strong |
|---|---|---|
| EXP01 | G1 | Sweep, degenerate flag, and new random baseline all reproduce exactly; margin is seed-stable. |
| EXP02 | G2 | Module-identity-level proof (not just output matching); 8/8 scenario agreement independently confirmed. |
| EXP04 | G4 | Fresh re-run + 4 new scenarios (n=9) preserve/strengthen the negative result; one discrepancy (format%/steps vs. README) honestly disclosed, does not affect the constant-answer conclusion. |
| EXP06 | G6 | Six-config table, 3-session CoreML variance, and a near-bit-identical ONNX/TorchScript per-image diff all independently reproduce exactly — evidence stronger than the design's own success bar. |
| EXP07 | G7 | Fish-per-frame distribution, empirical 0/98 full-frame-miss rate, and F1-argmax confirmation all reproduce exactly; the experiment itself correctly surfaces the 0.719-vs-0.782 ambiguity as a required disclosure (see Must-Disclose below) rather than concealing it — this is why it still counts as strong, not partial: the finding-and-disclosure loop worked as designed. |
| EXP09 | G9 | This goal's success criteria equal its own minimum-viable ceiling; that ceiling was fully reached, including a correctly root-caused pre-existing test failure and 4 genuinely new edge-case tests. |
| EXP10 | G10 | Confirmatory literature search correctly declines to over-claim from a negative result; synthesis of EXP01–EXP09 accurately reflects the underlying data (independently cross-checked). |
| EXP11 | G11 | Finalization pass genuinely completes provenance coverage; the 0.695-vs-0.719 grep and the RAG-knowledge-base leak finding are both independently reconfirmed as real. |

## Partial Experiments (with recommendations)

| Exp | Goal | Goal satisfaction | Why partial | Recommendation |
|---|---|---|---|---|
| EXP03 | G3 | minimum_viable | All procedural deliverables done, but the central finding (50% malformed-output-defaults-safe vs. only 12% textbook under-call-and-escalate) satisfies the pre-registered minimum-viable framing, not the strong framing's implicit hope of clean severity-correction dominance. | **accept_as_minimum_viable** — this is an honestly reported, pre-registered legitimate outcome, not a broken experiment; a rerun cannot change what AQUA-1B actually outputs. |
| EXP05 | G5 | minimum_viable | Strong criterion (zero cross-split leakage) explicitly fails: 32 near-duplicate pairs found, 14 adjacent-frame. Minimum-viable (enumerate affected files, propose caveat) is met with checkable numbers. | **accept_as_minimum_viable** — contingent on the manuscript actually adding the specified caveat sentence near the headline vision numbers; do not silently drop it. |
| EXP08 | G8 | minimum_viable | Literal H5 direction ("equal-width jumps early") is inverted at low severities (quantile is more sensitive there); mechanism is confirmed via per-bin decomposition but the qualitative shape claim needed correcting, exactly the pre-registered minimum-viable failure branch. | **accept_as_minimum_viable** — the disciplined per-bin-decomposition contribution survives and is the paper's actual defensible claim; do not restate the original naive H5 direction as confirmed. |

## Failed Experiments

None. All 11 experiments produced usable, honestly-reported evidence for their goal, even where
that evidence fell short of the "strong" success criterion.

## Goal Satisfaction Summary

| Goal | Experiment | Satisfaction |
|---|---|---|
| G1 | EXP01 | strong |
| G2 | EXP02 | strong |
| G3 | EXP03 | minimum_viable |
| G4 | EXP04 | strong |
| G5 | EXP05 | minimum_viable |
| G6 | EXP06 | strong |
| G7 | EXP07 | strong |
| G8 | EXP08 | minimum_viable |
| G9 | EXP09 | strong |
| G10 | EXP10 | strong |
| G11 | EXP11 | strong |

## Recommended Presentation Order for the Results Section

1. **EXP02 (rule-path identity)** — establishes the mechanism baseline (same module object) before any behavioral claim is made about it.
2. **EXP03 (behavioral 4-bucket measurement)** — the paper's central decision-layer finding; present the honest 50%/38%/12%/0% split and the fabricated-reasoning finding together, framed via G3's minimum-viable language, not oversold.
3. **EXP04 (agentic tool-routing negative result)** — the strongest, cleanest disclosed negative result; present after EXP03 as a second, independently-confirmed instance of "deterministic authority, probabilistic component."
4. **EXP01 (RAG calibration)** — third layer; the random-baseline addition is the strongest new evidence in this section.
5. **EXP06 (export accuracy loss) → EXP07 (operating-point safety trace) → EXP05 (leakage audit)** — present the vision layer as one coherent block in this order: mechanism (EXP06) → what recall number governs safety and why (EXP07, must include the 0.719-vs-0.782 disclosure) → the caveat on the underlying split (EXP05).
6. **EXP08 (PSI/MLOps gate)** — present the per-bin-decomposition mechanism as the actual contribution, with the corrected (not naive) directional claim.
7. **EXP09 (twin_bridge)** — present last among the technical layers, explicitly as designed-and-unit-tested, not live-validated.
8. **EXP10 (cross-layer synthesis) → EXP11 (data-integrity appendix)** — close with the honest, narrowed cross-layer claim (EXP10's draft Abstract/Conclusion paragraph is usable near-verbatim), then the provenance/data-integrity appendix (EXP11) as a transparency device, not an afterthought.

## Must-Disclose Issues

These must appear in the paper's Known Limitations or Results text. Items 1–6 originate from
EXP11's own audit and are independently reconfirmed here by direct file inspection or raw-data
recomputation; item 7 is newly added by this verification pass.

1. **[HIGH] Live RAG knowledge-base leak.** `llm-service/knowledge/06-davranis-ve-refah-gostergeleri.md:58` states detection recall as "~0.695" as a live fact. This file is a source the RAG ingest pipeline reads into the production vector store, so a stale, superseded number is retrievable and could be surfaced verbatim by the deployed LLM. Independently confirmed by direct read of the file; not fixed (read-only guardrail on the live repo).
2. **[MEDIUM-HIGH] 0.719 vs. 0.782 recall ambiguity.** Vision recall has two both-correct numbers depending on the question: 0.719 (F1-argmax, academic headline) vs. 0.782 (actual recall at the deployed `conf=0.20` operating point). The manuscript currently has no language distinguishing them, and the H7 safety discussion must cite 0.782, not 0.719, as the number governing real-world full-frame-miss risk (0.782 is the more reassuring figure). Independently re-derived from EXP07's raw confidence-curve data, not merely re-stated from EXP11.
3. **[LOW] Precision rounding inconsistency.** `MODEL_RAPORU.md`'s summary table states Precision=0.858; its own correction narrative two paragraphs earlier cites raw `val()` output 0.8590 (rounds to 0.859), and both EXP06 and EXP07 independently reproduce 0.859. Thousandths-place, not safety-relevant, but propagates unchanged into README.md/README.tr.md/research_task.md.
4. **[MEDIUM] Agent-benchmark table drift.** Published README table (AQUA-7B: 60% format, 3.6 mean steps) does not reproduce in EXP04's fresh, code-unmodified re-run (100% format, 2.0 mean steps). Selection% and the constant-answer conclusion reproduce exactly; no configuration difference was found to explain the format/step drift (most likely `mlx-lm`/model-stack version drift). Must be footnoted, not silently resolved by picking one source.
5. **[LOW] EXP08 internal PSI inconsistency.** The systematic sweep's own delta=0.04 entry (quantile PSI=0.7279) differs from the separately-drawn "significant-drift window" at the same nominal delta (PSI=0.9070), due to unseeded per-call resampling inside a fixed-seed script. Self-contained within EXP08's own output; no headline manuscript number depends on the exact value of either.
6. **[MEDIUM] EXP05 leakage caveat not yet propagated.** 32 near-duplicate train/val pairs (14 adjacent-frame) found by EXP05 are not yet reflected as a caveat anywhere the headline mAP50/precision/recall numbers are reported elsewhere in `paper_workspace`. Milder than the already-disclosed `ogretmen` case, but a real, previously-undocumented risk to the same headline numbers.
7. **[NEW, MEDIUM] Vision val-set has zero sparse frames.** The 98-image val set contains no frames with k=1 or k=2 ground-truth fish, so the reassuring "0/98 empirical full-frame-miss" result (EXP07) says nothing about the sparse-frame regime — precisely the regime where the extrapolated miss-risk (21.8%–28.1% at k=1, using the two candidate recall figures from item 2) is highest. This is a dataset-coverage gap, not a stale number, and is not one of EXP11's original 6 items; recommend adding it explicitly to Known Limitations alongside them.

### Secondary, lower-priority notes (not required disclosures, but worth a maintainer footnote)
- `twin_bridge/` has zero git history (untracked); any provenance claim about it can only be "file contents as of session date," never a commit hash.
- `provenance_table.json`'s machine-readable Finalization Pass section has no distinct `exp02_provenance` key (the number is present instead in the human-readable summary tables) — cosmetic, not a missing claim.
- AQUA-1B/AQUA-7B LoRA adapter (`sure-aqua-adapter/adapters.safetensors`) provenance is mtime-only (gitignored, no git history) — disclosed as a limitation in EXP03, not concealed.

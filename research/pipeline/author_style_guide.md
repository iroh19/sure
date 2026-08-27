# Author Style Guide — S.U.R.E. Applied-Systems Paper (project_000)

**Status:** binding for the writeup (Phase 8). Merges the bundled default guide
(`/Users/batuhancitak/.claude/skills/poggioai-msc-claude/templates/author_style_guide_default.md`,
written for ML theory papers but whose structural/epistemic discipline transfers directly) with
`narrative_brief.md`'s paper-specific voice decisions (Phase 7c). No paper-specific rule below
contradicts the default guide; where the default guide's ML-theory framing (theorems, proofs,
lemmas) does not apply to an applied-systems paper, it is reinterpreted below rather than dropped —
"proved" becomes "measured/observed," "theorem" becomes "Formalization" (see `theorem_map.json`).

---

## Part A — General principles (from the bundled default guide, reinterpreted for this paper)

### What a strong paper does
- The reader can state the main result in one sentence after the Abstract.
- The Introduction makes the problem, the surprise, and the stakes legible immediately.
- Related Work maps the field's actual clusters and states a critical judgment, not a bibliography
  dump.
- Prose distinguishes what was **measured** (11 experiments, real deployed system), what is
  **derived/expository** (the 4 Key Formalizations — restatements of already-implemented code, not
  proofs), what is **conjectural** (the one hedged generalization claim in Discussion), and what is
  **disclosed as unresolved** (twin_bridge, the live RAG 0.695 leak, the sparse-frame gap).
- The document never sounds more certain than the evidence warrants — this paper has 8
  `achieved_strong` and 3 `achieved_minimum` goals; the minimum-viable goals (G3, G5, G8) are not
  written around as failures, they are the paper's most interesting findings, stated with their
  own honest scope.

### Non-negotiable principles (applied to this paper)
1. **One central intellectual spine.** The spine is `pre_writeup_synthesis.md`'s central-claim
   framing (see below): the backstop's soundness never depended on the LLM reasoning correctly,
   only on one enumerable field being extractable and the system defaulting safe when it isn't.
   Every other finding (RAG calibration, PSI binning, export-format loss, the agentic negative
   result) is a consequence or a parallel instance of the same "narrow enumerable interface"
   discipline applied at a different layer — not an equal-weight independent contribution.
2. **Every sentence knows its epistemic status.** Distinguish: measured-and-reproduced (most
   numbers here, each traceable to a specific `EXPnn/results.md` or raw JSON file); measured-once
   with disclosed scope limits (G3's n=8, G9's unit-tests-only); expository/formal restatement (the
   4 Formalizations); hedged conjecture (exactly one, in Discussion — the cross-domain
   transferability suggestion).
3. **No internal bookkeeping in high-level exposition.** Formalization numbers, goal IDs (G1-G11),
   experiment IDs (EXP01-EXP11) belong in the body/methods/appendix, not in the Abstract, and only
   sparingly in the Introduction.
4. **Local fluency does not excuse global incoherence.** A well-written Results subsection that
   doesn't serve the central spine above gets compressed or cut (this is why twin_bridge/G9 is one
   paragraph, not a subsection — see narrative_brief.md's structural recommendation).
5. **Compress.** Eleven goals and six emergent findings do not get eleven equal-weight subsections.
   Billing follows `pre_writeup_synthesis.md`'s Updated Structural Recommendation exactly (Results
   5.1-5.6, priority order below).

### Global anti-patterns to avoid (from the default guide, unchanged)
- Abstract-as-mini-paper; Introduction restating the Abstract; Related Work as a flat list;
  Conclusion re-abstracting instead of adding judgment; many "contributions" with no central claim;
  uniform confidence throughout; citations as seriousness markers; every sub-result treated as
  equally load-bearing.
- Sentence-level: "Furthermore/Moreover/Additionally" chains; "It is important to note that";
  "In recent years..." throat-clearing; symmetric hedging on claims that are actually well-evidenced;
  noun-pile prose.
- Epistemic: "prove" used for an experiment; conjectures narrated as conclusions; survey-breadth
  with no judgment; suspiciously convenient citations.

### Deletion pass (apply to every section before it is considered done)
Ask: if I delete this paragraph, does the paper lose a finding, a caveat that changes what a
downstream decision-maker should do, or a citation-grounded claim? If not, cut or merge it. This is
especially binding for: G9/twin_bridge (target: one paragraph), the 0.858-vs-0.859 rounding nit
(target: one footnote), and any temptation to write a standalone subsection per goal (target: the
5.1-5.6 structure below, not 11 subsections).

---

## Part B — Paper-specific voice decisions (from `narrative_brief.md`, Phase 7c — binding)

### Vision-drift verdict (context, not a writing instruction)
The empirical run is assessed as a **deepening**, not a drift, relative to `vision.md`. All four
vision pillars resolved to `achieved_strong` or `achieved_minimum`; zero goals fell to
`partially_achieved`/`not_achieved`/`blocked`. The Introduction and Conclusion should state the
*deepened* thesis directly (the enumerable-field framing below), not the original proposal's
softer "the LLM proposes, the rule engine catches misses" framing, which the data complicates.

### Central-claim framing (verbatim anchor, from `pre_writeup_synthesis.md` §3 — use near-verbatim
in Introduction and Conclusion)
> This paper's central finding is that a deterministic safety backstop's soundness never depended
> on its LLM component reasoning correctly — only on a single enumerable status field being
> extractable from the model's output, and on the system defaulting to the safe state when it
> isn't.

### Surprise markers — exactly three, at exact locations (do not add a fourth)
1. **Results 5.1, opening beat**: the 50%-fail-safe-defaulting + fabrication-in-agreement finding,
   as ONE combined surprise beat (not two separate "surprisingly" sentences). Close phrasing to
   narrative_brief.md's exact suggested sentence.
2. **Results 5.1, adapter-provenance sentence**: stated as confident disclosure, NOT a surprise
   beat. No "surprisingly." Flat, declarative, "held anyway" register.
3. **Results 5.3, H6/export subsection**: the INT8-loses-less-than-fp32 finding.
Every other honest complication (G1, G5, G7's 0.719/0.782, G8's crossover, G11's RAG leak) is
stated as confident, direct, caveated-in-the-same-breath prose — not a fourth surprise beat.

### Must-disclose-early items (binding placement — see full table in `narrative_brief.md` §v)
- Adapter provenance: first appears in Methods/System Architecture at first mention of AQUA-1B/G3,
  repeated as the opening clause of Results 5.1. Scoped to G3/EXP03 only — never attached to
  G4/EXP04 (base model, no adapter).
- 0.719 vs. 0.782 recall: both numbers, same sentence, in the Abstract (0.719 is `vision.md`'s
  immutable locked figure; 0.782 must be added alongside it, never substituted). Also a named
  callout in Results, not a figure caption.
- Live RAG 0.695 leak: one rhetorical sentence in Introduction or Discussion, plus the
  data-integrity table.
- Sparse-frame coverage gap: stated beside the 0/98 headline number in Results, and again in
  Limitations.
- G3's 38%-agrees bucket: never cited without its adjacent fabrication-rate annotation (2 of 3
  agrees cases contain fabricated values), every time the bucket percentages are quoted.
- G5's corrected vision numbers: never described as "corrected" without "same-checkpoint
  re-evaluation, not a leakage-free retrain" in the same sentence.
- G8's crossover: never compressed to "quantile is more sensitive, use quantile" — state the
  crossover (δ≤0.06 vs. δ≥0.08) and its mechanism.

### Related Work framing (binding structure — see `literature_review_matrix.md` for the underlying
six themes)
Two/three-cluster structure with an explicit, load-bearing pivot sentence — not a flat six-theme
list:
- Cluster A: domain/deployment literature (precision aquaculture + edge AI deployment) — earns
  citations, claims no novelty, establishes the setting is real and current.
- Pivot: states plainly the paper does **not** invent deterministic override, interlocks, or
  shielding. Cites SIS/IEC 61508-61511 and RL-safety shielding by name. States the one real
  architectural difference: S.U.R.E.'s independence is logical/code-level (a shared Python module),
  not IEC 61511's physical sensor/actuator independence.
- Cluster B: LLM-guardrail/safety/reliability literature (including the SIS/shielding prior art
  and small-model agentic tool-calling reliability) — framed critically: most guardrail work
  re-validates via a second model or schema check, not a dependency-free deterministic rule engine
  with code-shared escalation-only precedence.
- Cluster C: retrieval/MLOps calibration literature (RAG threshold calibration, PSI drift) —
  careful applications, not claimed inventions.
- Closing pivot, one sentence: the real novelty locus is the cross-layer generalization — the same
  narrow-enumerable-interface discipline measured across five architecturally distinct layers in
  one deployed system, including a full disclosed negative result and a fabrication-detection
  finding the SIS/shielding literature has no equivalent for (it is built for enumerable
  action/state spaces, not free-text reasoning).

### Anti-AI voice table (verbatim, binding)
| Avoid | Use instead |
|---|---|
| Every paragraph same structure | Vary: some short and punchy, some flowing |
| "Furthermore, Moreover, Additionally" chains | Vary connectives; sometimes none at all |
| Balanced hedging everywhere | Confident where evidence is strong, genuinely uncertain where it isn't |
| Related work = flat list of summaries | Opinionated narrative with groupings and critique |
| "We propose X. X achieves Y." | "One might expect X, but surprisingly Y" |
| Conclusion restates abstract | Reflection, honest limitations, genuine open questions |
| Perfect parallelism in lists | Natural asymmetry |
| "It is important to note that..." | Just state the thing |
| No first-person judgment | "We found this surprising because..." (only where marked) |

### Discussion blueprint (binding content, not just tone)
Honest limitations to state explicitly, never let evaporate under space pressure: n=8 is the
entire fixed scenario population behind G3 (no CI implied); single-device (M4 Pro) edge
benchmarking; twin_bridge unit-tested-only, never "field-validated"; adapter caveat scoped to
G3/derivatives only, never G4; zero k=1/k=2 frames in the val set. Genuine open questions: would
the 128-example v2 adapter change the 50% unparseable rate (untested); does the narrow-interface
pattern hold for agentic routing at larger on-device scale; does the extrapolated 22-28% sparse-
frame miss risk match reality. Exactly one carefully-hedged conjecture: narrow-enumerable-field
validator interfaces may be a transferable safety-design principle beyond this domain — "these
results suggest"/"this may point to," never "prove."

---

## Part C — Formalization-specific reinterpretation of the default guide's theorem rules

This is an empirical-only project (no `math_workspace/`, confirmed). The default guide's "theorem
statement" rules are reused for the 4 Key Formalizations, with "Theorem" replaced by
"Formalization" throughout (per `resource_inventory.tex` §"Key Formalizations"): state the object,
scope, and dependency cleanly; give the simple version before any nuance; each Formalization must
carry a `% SOURCE_CLAIM` comment pointing to its grounding file; do not present these as proofs —
they are expository restatements of already-implemented code, empirically grounded by specific
experiments (EXP02/EXP03 for severity monotonicity; EXP03 for the enumerable/non-enumerable
boundary; EXP08 for the PSI gate; EXP07 for the operating-point framing).

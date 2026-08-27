# Narrative Brief — S.U.R.E. Applied-Systems Paper (project_000)

**Role:** Narrative Architect, Phase 7c (solo, extensive round). **Status:** advisory-binding —
this brief sets voice/tone; it does not reopen any finding. **Inputs read in full:**
`research_proposal.md`, `formalized_results.md`/`.json`, `resource_inventory.tex`, all 4
`pre_writeup_persona_{narrative,rigor,practical}_round_{1,2}.md` files (practical has no round 2
distinct file beyond the one read — confirmed both rounds read), `pre_writeup_synthesis.md`,
`track_merge_summary.md`, `research_goals.json` (targeted), `vision.md`, `novelty_flags.json`,
`literature_review.md`, `initial_context/README.md`, `initial_context/MODEL_RAPORU.md` (background
consulted via README's stated corrections). Confirmed: no `*style*`/`*voice*`/`*writing*` file
exists in `initial_context/` — the bundled default
`/Users/batuhancitak/.claude/skills/poggioai-msc-claude/templates/author_style_guide_default.md`
governs writing mechanics; this brief covers only this paper's specific voice decisions within
that standard. Confirmed: no `math_workspace/` exists — intentional, empirical-only scope.

---

## Vision Drift Assessment

**This is a DEEPENING, not a drift or regression.** Three independent lines of evidence converge
on this conclusion:

1. **`research_proposal.md` itself already documents this pattern one level down** (Round 1→2→3):
   its own "Narrative Continuity Assessment" states plainly that the Round 2 proposal "is a
   DEEPENING, not a regression" relative to Round 1, for the same structural reason now repeating
   one level up — nothing covered was dropped, a mid-synthesis narrowing (the Edge Vision Pipeline
   briefly falling out of the thesis) was caught and genuinely restored rather than re-labeled, and
   vague goals became precise, falsifiable ones. The empirical run that followed extends this exact
   pattern rather than breaking it.
2. **All four `vision.md` pillars are covered with real section homes, and none were softened to
   get there.** Dual-Layer Decision (G1–G4), Edge Vision Pipeline (G5–G7), Optimized RAG (G1/G4's
   sibling H4 goal), and MLOps/Drift Detection (G8) each resolved to `achieved_strong` or
   `achieved_minimum` — 0 goals fell to `partially_achieved`, `not_achieved`, or `blocked` per
   `formalized_results.md`'s Executive Summary. The `research_proposal.md` Vision Coverage Map's
   claim that "no vision element is DEFERRED" survived the empirical run intact.
3. **The central thesis got sharper, not vaguer, and the honest complications are being promoted,
   not buried.** `pre_writeup_synthesis.md`'s final central-claim framing (§3) states the mature
   version precisely: the backstop's soundness "never depended on its LLM component reasoning
   correctly — only on a single enumerable status field being extractable... and on the system
   defaulting to the safe state when it isn't," demonstrated against "an 8-example LoRA adapter
   that the project's own training pipeline documents as an insufficient, smoke-test-only
   artifact." That is a **stronger, more falsifiable, more reviewer-proof claim** than the original
   proposal's "the LLM proposes, the rule engine catches misses" framing — and it was arrived at
   *because* the two pre-registered acceptable-failure branches (H2's non-enumerable-failure-mode
   limit, H5's possible qualitative-shape reversal) both fired, landing exactly on G3 and G8 as
   `achieved_minimum`. `track_merge_summary.md`'s own framing of this (§4, "Cross-Cutting Honest
   Complications Carried Forward — must not be smoothed over downstream") and all three pre-writeup
   personas' unanimous, twice-repeated ACCEPT verdicts confirm: a council that pre-committed to what
   an honest miss looks like, and then got that miss, produced a paper that is more credible and
   more publishable than one that got everything it hoped for. Nothing here is a fallback story
   dressed up as a finding.

**Practical implication for the writeup:** do not write around G3/G5/G8 as if they are weaknesses
to be minimized. They are the paper's evidentiary backbone. The Introduction and Conclusion should
state the deepened thesis directly, not the pre-registered one.

---

## (i) What Is Surprising

Four candidates were evaluated against the "expectation violated, not manufactured drama"
standard. All four pass; the writeup should use the strongest three as explicit surprise-voice
moments (see §v) and state the fourth as confident, non-hedged disclosure rather than a surprise
beat, per an explicit persona finding (below).

**1. The dominant escalation pathway is fail-safe defaulting, not sophisticated correction.**
One might expect a dual-layer safety architecture's value to be demonstrated by the rule engine
catching the LLM's occasional wrong severity call — that is the proposal's own original
"proposes/disposes" framing. What actually happened: in 4 of 8 scenarios (50%), the model's output
did not parse at all, and the architecture's safety property came from defaulting to the safe
state, not from correcting a judgment. Only 1 of 8 (12%) is a genuine under-call-and-escalate case
— the "sophisticated correction" the framing implicitly promised. This is interesting, not just
unexpected, because it relocates what is actually being validated: not "does the rule catch the
LLM's mistakes" but "does the architecture survive an LLM that mostly produces nothing usable at
all" — a materially harder and more general claim, and one immune to the "a smarter model would
change this" objection precisely because the mechanism never depended on the model trying
successfully in the first place.

**2. AQUA-1B fabricates specific numeric sensor values even inside "agreeing" outputs.**
One might expect that when a model's final status label matches the correct answer, its stated
reasoning got there honestly. In 2 of the 3 "agrees" scenarios (and 6 of 8 total), the free-text
reasoning cites a sensor value that was never in the input (e.g., stating DO = 6.0 mg/L when the
actual reading was 5.7). This is interesting, not just unexpected, because it is invisible to any
evaluation that checks only the output label — the exact evaluation regime most guardrail papers
run — and it falsifies a folklore claim broader than "hallucination exists": *a model that gives
the right answer got the right answer.* It is also the paper's most novel empirical contribution:
a fabrication-detection finding inside a correctness-graded bucket, not merely a hallucination-rate
number.

**3. The deployed adapter is an 8-record smoke-test artifact, not the properly-sized one — and the
safety property held anyway.** One might expect that a poor showing from the LLM component would
need to be explained away, discounted, or flagged as a threat to external validity. What actually
happened, per the Rigor persona's independently re-derived record-count-plus-mtime-ordering
evidence: the deployed `sure-aqua-adapter` trains on exactly 8 records, matching
`sure_finetune_data.jsonl` — the file `finetune.py`'s own docstring calls "el yazımı 8 örnek
(yetersiz, sadece duman testi)" ("8 handwritten examples, insufficient, smoke-test only") — while
the documented 128-example `sure_finetune_data_v2.jsonl` existed on disk, unused, *before* the
deployed adapter was even trained (v2 mtime precedes the adapter's `_mlx_data` mtime). This is
interesting, not just unexpected, because it pre-empts rather than defers the single most obvious
reviewer objection ("a better-tuned model would fix this") — the paper can state, on the record,
that it tested the architecture against close to the worst plausible version of its own model
component, and the safety property held regardless. **Voice instruction, per unanimous persona
consensus (Practical R2, Narrative R2, Rigor R2): this fact must never be voiced as a hedge or an
apology.** State it as a stress-test framing, in the same declarative register as a confident
result — not with "surprisingly" language, which would wrongly imply the finding weakens the
paper. See §v.

**4. INT8 quantization loses less accuracy than fp32 ONNX/TorchScript export.** One might expect
that a more aggressively optimized format (INT8) pays a larger accuracy cost than an unquantized
export. ΔmAP50 for INT8 (−0.0082) is smaller in magnitude than for the fp32 ONNX/TorchScript
exports (−0.0104) — the quantization is not where the accuracy is actually being lost. This is
interesting, not just unexpected, because it directly falsifies a named folklore claim
("quantization is where you pay for edge speed") and relocates the real cause to a shared
export/post-processing (NMS) code path — evidenced further by a per-image ONNX-vs-TorchScript diff
showing near-bit-identical agreement (0/98 images meaningfully different, median IoU 0.99999976).
It converts a "huh, weird" result into an actionable diagnostic principle: measure the whole
exported pipeline before blaming the numeric precision.

---

## (ii) What Is Good

Ranked by strength, honestly — not every `achieved_strong`/`achieved_minimum` label carries equal
evidentiary weight.

1. **G4 — Agentic tool-routing negative result (EXP04).** What: AQUA-1B fails at agentic
   tool-calling (0%/0% format/selection) and AQUA-7B's headline selection rate is a
   constant-answer artifact, both confirmed on a fresh re-run at n=9 (up from n=5), with genuinely
   new scenarios, not padding. Why compelling: a negative result that survives someone actively
   trying to break or strengthen it is rare in applied-AI papers, and it directly refutes the "more
   LLM autonomy is more capability" folklore with a replicated, adversarially-tested result rather
   than a single run. Limitations: still n=9 on one prompt/scenario design, one model family; the
   published README's format%/step-count figures do not reproduce (footnoted, unexplained).

2. **G3 — Behavioral measurement of the dual-layer decision system (EXP03).** What: the four-bucket
   distribution plus the fabrication-inside-agreement finding, now correctly scoped to the
   self-documented-inadequate adapter. Why compelling: this is the paper's central empirical result
   and the sharpest, most falsifiable version of its thesis, strengthened rather than weakened by
   the adapter-provenance correction. Limitations: n=8 is the entire fixed scenario population (no
   confidence interval implied), the fabrication coding is single-rater (though the discrepancies
   are objectively checkable against sensor snapshots, not subjective), and `achieved_minimum` per
   its own pre-registered honest-miss criterion, not `achieved_strong`.

3. **G6 — Export-format accuracy loss mechanism (EXP06).** What: the six-configuration export table
   plus a new per-image ONNX-vs-TorchScript diff isolating the loss to a shared post-processing
   path, with CoreML/ANE latency variance measured across 3 independent sessions. Why compelling:
   clean, replicated, immediately actionable, and directly falsifies a named folklore claim. This
   is the emergent-finding-to-methodology conversion the paper does best. Limitations: single
   device (Apple M4 Pro), single training run's checkpoint, toolchain-specific — explicitly not
   claimed to generalize to other detector architectures.

4. **G7 — Vision operating-point safety trace (EXP07).** What: the fine-grained confidence-sweep
   curve reveals the deployed operating point (conf=0.20) actually runs at P=0.720/R=0.782,
   materially different from the headline academic-argmax (P=0.858/R=0.719) the rest of the
   manuscript cites — surfaced and disclosed, not concealed. Why compelling: it is exactly the kind
   of falsifiable, numeric self-correction that gives the paper's honesty argument teeth, and it
   feeds directly into the safety discussion (0.782, not 0.719, is what should govern it).
   Limitations: the reassuring 0/98 full-frame-miss result is conditional on a validation set that
   contains zero k=1/k=2 (sparse-fish) frames — the regime most likely to matter for a welfare check
   was never tested, only extrapolated.

5. **G1 — RAG retrieval calibration reliability (EXP01).** What: the F1-argmax/deployed-threshold
   sweep is reproduced exactly, plus a new random/no-retrieval baseline showing e5-small clears
   random by a wide, stable margin across 5 seeds. Why compelling: a genuinely new baseline
   authored specifically to avoid writing to the live production DB — careful experimental hygiene.
   Limitations: single 8-document/44-chunk Turkish-language corpus; 29 positive queries / 12 hard
   negatives is a small, domain-specific evaluation set.

6. **G11 — Manuscript-wide data-integrity audit (EXP11).** What: a grep-and-provenance pass across
   the whole paper trail that itself *found* a live, unfixed stale-0.695-recall leak inside the
   production RAG knowledge base. Why compelling: the paper practicing its own thesis at the meta
   level — self-audit catching a stale figure is a genuinely persuasive, self-demonstrating
   artifact for a hallucination-discipline paper. Limitations: this is a process/audit
   contribution, not a novel empirical result in itself; its value is almost entirely rhetorical
   and disclosure-quality, not a new measurement.

7. **G9 — twin_bridge mechanism-evidence inventory (EXP09).** What: existing and newly-authored
   unit tests for the PLC/CODESYS bridge module, honestly reported as unit-tested-only. Why
   compelling: none, particularly — its own success criteria equal its minimum-viable ceiling, and
   it was correctly never oversold as cross-implementation corroboration. Limitations: no live twin
   session was ever exercised; this is the weakest contribution in the paper by design, and the
   pre-writeup council unanimously recommends compressing it to a short paragraph, not a named
   subsection.

8. **G5 — Vision dataset leakage audit and correction (EXP05).** What: 32 near-duplicate train/val
   pairs found beyond the already-corrected `ogretmen` case, with a same-checkpoint re-evaluation
   producing a quantified (if modest) corrected precision/recall/mAP50 range. Why compelling: a
   real, previously undocumented data-integrity finding, closed with a directly-computed number
   rather than left as an unquantified caveat. Limitations: `achieved_minimum` — this is a
   re-evaluation on a smaller held-out set, not a leakage-free retrain; the flagged frames remain in
   the training set that produced the deployed weights.

9. **G8 — PSI drift-binning sweep (EXP08).** What: a 16-point severity sweep that finds quantile
   binning is *more* sensitive at low drift severity (the literal opposite of the pre-registered
   H5 direction), with equal-width only overtaking from δ≥0.08. Why compelling: a genuine,
   mechanistically-explained correction (one large equal-width bin emptying), not a confirmed
   monotonic story — more interesting than what was hypothesized. Limitations: `achieved_minimum`
   per its own pre-registered correction-not-confirmation branch; an internal unseeded-resampling
   inconsistency (δ=0.04: 0.7279 vs. 0.9070) is a known, footnoted wrinkle.

---

## (iii) Why It Matters for ML/Applied-AI

The applied-AI discourse on LLM agents in safety-critical or industrial settings currently sits
between two extremes: hype ("agents will run the plant autonomously") and vague hand-wringing
("we need guardrails," unspecified). What is scarce is a *measured, deployed* instance of a
guardrail pattern that states its own failure modes in numbers rather than principle. This paper's
contribution to that debate is not the override-authority pattern itself — the literature review's
own adversarial novelty check correctly classifies "deterministic final authority over a
probabilistic component" as EQUIVALENT_KNOWN, tracing directly to Safety Instrumented Systems /
IEC 61508–61511 interlock doctrine in industrial safety engineering (pre-dating ML entirely) and to
"shielding" in the safe-RL literature, both of which independently state the same enumerable/
non-enumerable boundary condition this paper's H2 derived from first-hand system observation. What
this paper contributes is empirical validation of that known pattern in a new, real, deployed
domain — aquaculture RAS, LLM-mediated rather than RL-policy-mediated — with a documented near-miss
(the eval-harness drift bug) and, critically, a genuinely novel fabrication-detection finding that
the SIS/shielding literature has no equivalent for, because that literature is built around
enumerable action/state spaces, not free-text reasoning that can be factually wrong while the
enumerable output is correct.

That fabrication finding also speaks directly to hallucination/confabulation research from an angle
most benchmark papers cannot reach: status-only or answer-only grading is the dominant evaluation
regime in agentic-benchmark and guardrail literature, and this system's own scenario set shows that
regime missing a real failure mode inside its own "success" bucket. The paper is not claiming a new
hallucination-detection method — it is demonstrating, with a small but concrete n, that a
correctness-graded output can conceal fabricated internal justification, which is a distinct and
underexplored claim from "the model sometimes hallucinates." Combined with the "more autonomy is
more capability" folklore directly refuted by the agentic tool-routing negative result (replicated
under adversarial re-run, not a single unchallenged pass), the paper gives the field two
citable, numbered data points against two separate pieces of currently under-evidenced folklore.

Finally, the paper's actual novelty locus — as `novelty_flags.json`'s own confirmatory analysis
concludes — is the cross-layer generalization: the same "read one enumerable field, ignore
everything else, default safe" discipline independently applied and measured across five
architecturally distinct layers (decision, agent routing, RAG, MLOps, vision) inside one production
system, including one full disclosed negative result. That is a claim about *interface design* as a
safety mechanism (the validator's narrow read of the model's output, not the override logic per se,
is what makes the model's unreliability harmless) — a transferable idea for anyone building an
LLM-plus-validator pipeline in a domain where errors are not merely embarrassing but costly.

---

## (iv) What It Explains of Practice

`pre_writeup_synthesis.md` already drafted the paper's sharpest practitioner rule; state it near
verbatim as the anchor sentence, then expand:

> "Architect a safety-critical LLM-plus-validator pipeline assuming the model will frequently
> produce nothing usable, verify your fallback default is conservative, never let your validator
> read anything beyond the one enumerable field it certifies."

Three more, each grounded in a specific finding, not generic advice:

- **RAG threshold tuning for hallucination-averse domains should optimize for asymmetric cost, not
  raw F1.** G1/H4's threshold selection (0.85 over the F1-optimal 0.84) sacrifices measurable
  recall specifically to drive hard-negative pass-through to zero, because a fabricated citation
  actively misinforms while a missed document only weakens reasoning a downstream deterministic
  layer still adjudicates. The practitioner takeaway is the cost function, not the specific
  threshold value: know which error type is actually expensive in your domain before you optimize.

- **PSI-gate retraining on the measured shape of your confidence distribution, not on an assumed
  binning convention.** G8's finding — quantile binning is *more* sensitive at low drift severity,
  the opposite of the naive expectation, with equal-width only becoming useful at high severity —
  means "use quantile binning" is not a universal rule; it is a consequence of this system's
  confidence outputs being concentrated in a narrow band. The transferable practice is: sweep your
  own severity range and check for a crossover before committing to one binning scheme, rather than
  copying a convention from credit-scoring literature unchecked.

- **Select an edge export format by measuring the whole exported pipeline, not by reasoning about
  numeric precision in isolation.** G6's finding that INT8 loses less accuracy than fp32 exports
  means the standard mental model ("lower precision costs more accuracy") can be wrong for a given
  toolchain if the real loss is in a shared post-processing/NMS path common to every export target.
  Practitioners should benchmark the full six-way (or however many) configuration matrix before
  attributing an accuracy delta to the compression step that is easiest to blame.

- **Audit your own deployed artifacts with the same rigor you audit your headline metrics.** The
  adapter-provenance finding (G3) and the live 0.695 RAG-corpus leak (G11) are the same phenomenon
  at two different layers of the stack: an artifact silently drifted or was mis-identified between
  being produced and being used to draw a conclusion. Both were caught by simple, cheap file-level
  checks (record counts, mtimes, grep) that most teams skip because they trust "we deployed the
  right thing" as an assumption rather than a checked fact.

---

## (v) Voice Guidance for the Writeup

### Surprise markers (exactly 3 — do not add more)

1. **Results 5.1, opening beat (combines candidates 1 and 2 above into one surprise moment, per
   `pre_writeup_synthesis.md`'s explicit instruction that these are "one combined beat, not
   separate call-outs").** Use one surprise-voice sentence covering both facts as a single
   escalating reveal, not two separate "surprisingly" interjections:
   > "One might expect a dual-layer safety system's value to come from the rule engine catching
   > the model's occasional wrong call. It rarely gets the chance to: half the time (4/8) the
   > model's output does not parse at all, and — more surprising still — even when its final status
   > agreed with the rule engine, in two of those three cases the reasoning behind it cited a
   > sensor value that was never in the input."
   Follow immediately, in the *same* paragraph, with the adapter-provenance sentence stated as
   **confident disclosure, not a second surprise beat** (see below) — this is a deliberate
   register shift, not an inconsistency: the model's unreliability is the surprise; the reason it
   was tested against a near-worst-case component is not narrated as surprising, it is narrated as
   the reason the finding is trustworthy.

2. **Results 5.1, adapter-provenance sentence (no "surprisingly," stated flatly and confidently).**
   > "We did not give the LLM a fair chance — the deployed adapter trained on 8 handwritten
   > examples the project's own training pipeline calls insufficient, while a documented,
   > properly-sized 128-example alternative sat unused on disk — and the architecture's safety
   > property held anyway."
   This is intentionally *not* one of the three counted surprise markers; it is the payoff that
   makes marker 1 land as strength rather than weakness. Do not hedge it, do not apologize for it,
   and do not let a later compression pass soften "held anyway" into something tentative.

3. **Results 5.3, H6/export subsection.**
   > "One might expect the more aggressively compressed format to pay the larger accuracy cost.
   > INT8 quantization loses less (ΔmAP50 −0.0082) than the unquantized fp32 ONNX and TorchScript
   > exports already do (−0.0104) — the loss lives in a shared export/post-processing path, not in
   > the numeric precision that gets blamed by default."

The rest of the paper — including G1, G5, G7's 0.719/0.782 disclosure, G8's crossover, G11's RAG
leak — should be stated as confident, direct findings with their caveats attached in the same
breath, not dramatized as additional surprises. Reserve the authorial "surprisingly" register for
these three moments only.

### Related work framing

Organize Related Work around the literature review's six themes, but group them into two
super-clusters with an explicit pivot sentence between them, not a flat six-item list:

- **Cluster A — domain and deployment literature** (Theme 1: precision aquaculture/RAS monitoring;
  Theme 2: edge AI deployment for vision models). Position S.U.R.E.'s vision pipeline and edge
  export findings as belonging to an active, competitive sub-literature (lightweight-YOLO-in-RAS,
  CoreML/ANE benchmarking) — this cluster earns citations but no novelty claim; it establishes that
  the *setting* is real and current.
- **Pivot sentence, explicit and load-bearing:** state plainly that the paper does **not** claim to
  invent deterministic override, interlocks, or runtime shielding. Cite Safety Instrumented Systems
  / IEC 61508–61511 interlock doctrine and the RL-safety "shielding" literature (both correctly
  flagged EQUIVALENT_KNOWN in `novelty_flags.json`) by name, and state the one real architectural
  difference worth naming rather than glossing over: S.U.R.E.'s independence is *logical/code-level*
  (a shared Python module imported by both production and evaluation), not the *physical* sensor/
  actuator independence IEC 61511's Independent Protection Layer criteria were written around.
- **Cluster B — LLM-guardrail, safety, and reliability literature** (Theme 3: LLM safety/guardrails
  in safety-critical systems, including the SIS/shielding prior art just cited; Theme 5: agentic
  tool-calling reliability at small model scale). Frame this cluster critically, not as a
  bibliography dump: most guardrail literature re-validates model output via a second model or a
  schema check, not a dependency-free deterministic rule engine with escalation-only precedence
  enforced by literal code-sharing — name that gap explicitly before pivoting to what's new here.
- **Cluster C — retrieval and MLOps calibration literature** (Theme 4: RAG threshold calibration;
  Theme 6: PSI drift detection). These ground H4 and H5/H8 as applications of active,
  well-established sub-literatures (asymmetric RAG threshold calibration is an active 2025–2026
  concern; PSI's quantile-vs-equal-width binning sensitivity is already a documented concern in the
  credit-scoring literature this system's MLOps borrows the metric from) — position these as
  careful, measured applications, not claimed inventions, same register as Cluster A.
- **"What's actually new here" pivot, after all three clusters:** the paper's real, defensible
  novelty locus is the cross-layer generalization — the same escalation-only, narrow-enumerable-
  interface discipline independently measured across five architecturally distinct layers in one
  deployed, production system, including one full disclosed negative result and a fabrication-
  detection finding the SIS/shielding literature (built for enumerable action/state spaces, not
  free-text reasoning) has no equivalent for. State this as the paper's one sentence of claimed
  novelty, immediately after the two prior-art clusters, not diffused across the Introduction.

### Discussion blueprint

**Honest limitations (state each explicitly, do not let any evaporate under space pressure):**
- n=8 is the entire fixed scenario population behind the paper's central empirical result (G3); no
  confidence interval is implied or should be stated.
- Single-device (Apple M4 Pro), single-session-class edge benchmarking; multi-session
  thermal-throttling effects are not characterized beyond the 3 independent CoreML/ANE sessions
  already run.
- `twin_bridge` remains unresolved: unit-tested only, never exercised against a live
  Godot/CODESYS session. State this plainly; never use "independently field-validated."
- The undertrained-adapter caveat applies to **G3 and its derivatives only** (the fabrication
  finding, the "narrow interface" novelty claim) — it must **not** be attached to G4, which ran the
  base model with no adapter loaded at all. Misapplying it to G4 would be a new factual error, not
  added precision (per Rigor R2's explicit scoping check).
- The validation set has zero k=1/k=2 (sparse-fish) frames; the reassuring 0/98 full-frame-miss
  result says nothing about that regime, which was never designed into the dataset.

**Genuine open questions:**
- Whether a better-tuned adapter (the 128-example v2, still unused) would reduce the 50%
  unparseable rate is untested — state this as future work, paired immediately with what would
  *not* change regardless: the architecture's independence from the model's free-text reasoning,
  since the rule engine never reads it irrespective of adapter quality.
- Whether the escalation-only, narrow-interface pattern holds at larger on-device model scale for
  agentic tool-routing (this system tested one ~1B and one larger model, both failing or producing
  artifacts) remains open.
- Whether the sparse-frame full-frame-miss risk (extrapolated ~22–28% at k=1) matches reality
  requires collecting or synthesizing frames the current dataset does not contain.

**Carefully-hedged conjecture (one, clearly marked as such):** the paper may suggest — using "these
results suggest" or "this may point to," never "prove" — that narrow-enumerable-field validator
interfaces are a generally transferable safety-design principle for LLM-plus-validator pipelines
beyond this domain. This is supported by the cross-layer consistency observed here but not by any
test outside this one system, and must be framed as a direction worth testing elsewhere, not a
demonstrated generalization.

### Anti-AI voice rules (verbatim from the prompt template — binding for the writeup)

| Avoid (AI tell) | Use instead (human equivalent) |
|---|---|
| Every paragraph same structure | Vary: some short punchy, some flowing |
| "Furthermore, Moreover, Additionally" chains | Vary connectives; sometimes no connective at all |
| Balanced hedging everywhere | Confident where evidence is strong, genuinely uncertain where it isn't |
| Related work = flat list of summaries | Opinionated narrative with groupings and critique |
| "We propose X. X achieves Y." (no surprise) | "One might expect X, but surprisingly Y" |
| Conclusion restates abstract | Reflection, honest limitations, genuine open questions |
| Perfect parallelism in all lists | Natural asymmetry |
| "It is important to note that..." | Just state the thing |
| No first-person judgment | "We found this surprising because..." (only where marked) |

### Must-disclose-early checklist (refined from `pre_writeup_synthesis.md`, with exact placement)

| Item | Must first appear in | Exact guidance |
|---|---|---|
| **Adapter provenance** (deployed adapter = 8-example smoke-test dataset, not the 128-example v2) | **Methods**, at first mention of AQUA-1B/G3's setup — repeated as the opening clause of the Results 5.1 beat | Scope strictly to G3/EXP03 derivatives; never attach to G4/EXP04 (base model, no adapter loaded). State the direction of inference ("stronger, not weaker") in the same sentence — see Surprise Marker 2 above for exact phrasing. Never let this read as an apology. |
| **0.719 vs. 0.782 recall** | **Abstract** (both numbers, same sentence — `vision.md` mandates 0.719 verbatim and is immutable, so 0.782 must be added alongside it, never substituted) and **Results** (a named callout/boxed paragraph, not a figure caption) | Highest-priority item: the single most likely failure mode is an Abstract frozen on 0.719 alone (drafted from `vision.md`'s locked figure) before the body's 0.782 correction propagates up. State explicitly which number governs the safety discussion (0.782). |
| **Live RAG 0.695 leak** | **Introduction or Discussion** (one rhetorical sentence: "even this system's own production knowledge base was found, during this audit, to be serving a stale figure it had already corrected elsewhere") + **data-integrity table** for the record | Do not bury as only a table row — it is a self-demonstrating artifact for the paper's hallucination-discipline argument and should do rhetorical work in prose. |
| **Sparse-frame coverage gap** (val set has zero k=1/k=2 frames; the 0/98 full-frame-miss result doesn't cover the sparse regime) | **Results** (immediately beside the 0/98 headline number) and **Limitations** | State the conditional explicitly: "this result is conditional on a val-set property that was never designed in, at exactly the regime most likely to matter for a welfare check" — never let it read as a shrug. |
| **G3's 38%-agrees bucket** (must not be read as an LLM competence data point) | **Results 5.1**, immediately adjacent to the four-bucket percentages, every time they are cited (not just once) | Never state "the model agreed 38% of the time" without the adjacent fabrication-rate annotation (2 of 3 agrees cases contain fabricated values); any figure or table showing the split without this annotation understates the LLM's unreliability by omission. |
| **G5's corrected vision numbers** (bias estimate resolved, leakage not removed) | **Wherever the headline vision P/R/mAP50 numbers are first cited** | Never use "corrected vision numbers" as a standalone phrase without "same-checkpoint re-evaluation, not a leakage-free retrain" in the same sentence — every time, not once in a footnote. |
| **G8's crossover finding** (corrected, not confirmed) | **Results, G8/H5 subsection**, and **Abstract/Conclusion if H5 is summarized there** | Never compress to "quantile binning is more sensitive, use quantile" — the actual, more interesting finding is the crossover (quantile more sensitive at δ≤0.06, equal-width overtaking at δ≥0.08) and its mechanism (a large equal-width bin emptying). |

---

**Verdict for the writeup agent:** the story is fully ready to write. Every open item across all
three pre-writeup personas and both rounds is a disclosure, sequencing, or billing decision — none
require new data or reopen a finding. Follow this brief's surprise-marker placement and
must-disclose-early checklist as binding; treat the ranked "What Is Good" ordering as the
main-body-vs-appendix priority signal alongside `pre_writeup_synthesis.md`'s Updated Structural
Recommendation (§2).

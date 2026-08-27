# Paper Outline — S.U.R.E. Applied-Systems Paper (Cycle 1)

Skeleton mandated by `vision.md` (Abstract, Introduction, Related Work, System Architecture
[LLM vs. Rule Engine emphasis], Experimental Setup & Edge Metrics, Results, Conclusion), extended
per the pre-writeup council's structural recommendation (`pre_writeup_synthesis.md` §2) with
Background, Discussion, Known Limitations, Acknowledgements, and an Appendix. Write order for
drafting (Passes 2-4) differs from reading order: Related Work + Background (Pass 2) -> System
Architecture + Experimental Setup + Results (Pass 3) -> Discussion + Known Limitations ->
Introduction -> Abstract (Pass 4, in that sequence, per the prompt's explicit instruction to write
framing sections last).

## Final section order (`final_paper.tex`, Pass 5)

1. **Abstract** (`sections/abstract.tex`)
2. **Introduction** (`sections/introduction.tex`)
3. **Related Work** (`sections/related_work.tex`)
4. **Background** (`sections/background.tex`)
5. **System Architecture** (`sections/system_architecture.tex`)
6. **Experimental Setup & Edge Metrics** (`sections/experimental_setup.tex`)
7. **Results** (`sections/results.tex`)
8. **Discussion** (`sections/discussion.tex`)
9. **Known Limitations** (`sections/known_limitations.tex`)
10. **Conclusion** (`sections/conclusion.tex`)
11. **Acknowledgements** (`sections/acknowledgements.tex`)
12. Bibliography (`\bibliography{references}`, `\bibliographystyle{plain}`)
13. Appendix (`sections/appendix.tex`) — full 16-point PSI sweep table, full 8-scenario EXP03
    per-scenario detail table, full six-config EXP06 table if not already in body Table 1.

## Per-section content plan

### Abstract (~150-190 words, no citations, no \ref, at most 2-3 headline numbers)
Problem (1-2 sentences): safety-critical RAS welfare monitoring cannot let an LLM's occasional
unreliability become the failure mode. What we did + found (4-5 sentences): dual-layer system,
deployed and measured across 5 layers; the central finding (fail-safe defaulting dominant, not
correction; fabrication survives inside "agreeing" outputs); MUST include the 0.719-vs-0.782
recall disclosure in the same sentence. Why it matters (1 sentence): a falsifiable practitioner
rule about narrow-enumerable-field validator interfaces.

### Introduction (`intro_skeleton.tex` governs structure)
Explicit research questions (RQ1: does escalation-only deterministic authority survive an
unreliable LLM in practice, not just in principle; RQ2: what does "survive" actually mean once
measured — correction or defaulting; RQ3: does the same narrow-interface discipline generalize
across architecturally distinct layers of one system). Explicit takeaways, each pointing to a
specific figure/section: (1) Fig 1 / Results 5.1 — fail-safe defaulting dominates; (2) Results 5.1
— fabrication survives inside agreement, invisible to status-only checks; (3) Results 5.2 — the
agentic negative result replicates under adversarial re-run; (4) Fig 2 / Results 5.3 — 0.719 vs.
0.782 and why it matters for the safety rule; (5) Fig 3 / Results 5.3 — INT8 loses less than fp32
export. Rhetorical sentence disclosing the live RAG 0.695 leak. Must NOT overclaim "solves LLM
unreliability" — states the falsifiable practitioner rule instead. One-paragraph roadmap.

### Related Work (Pass 2)
Cluster A (domain/deployment) -> pivot (SIS/IEC 61508-61511, RL shielding; states no invention of
override) -> Cluster B (LLM guardrails/reliability, agentic tool-calling) -> Cluster C
(RAG threshold calibration, PSI/MLOps) -> closing novelty-locus sentence (cross-layer
generalization + fabrication-detection finding). Every claim cited; keys checked against
`references.bib` before writing (grep first).

### Background (Pass 2, concise)
RAS domain primer (DO thresholds, why <6 mg/L is urgent) sourced from README.md/MODEL_RAPORU.md
and lindholm2023waterquality/agmrc2026waterquality. S.U.R.E. system overview at a glance (services,
data flow). Definitions used throughout: severity levels (ok/warning/critical), the rule engine
(`backend/rules.py`), RAG, PSI — kept tight, no re-explanation of Related Work's literature.

### System Architecture (Pass 3)
Dual-layer decision system: `apply_rule_override`, enumerable `status` field, escalation-only
monotonicity (`final_severity = max(severity_rule, severity_llm)`) as Formalization 1. Edge vision
pipeline (YOLOv11s + ByteTrack). RAG pipeline (pgvector + e5-small, heading-chunking, 0.85
precision-biased threshold). MLOps/PSI drift-gated retraining as Formalization 3. Enumerable vs.
non-enumerable failure modes as Formalization 2, immediately before/near the LLM description.
AQUA-1B + LoRA adapter provenance disclosed here at first mention (2-3 sentences, confident
stress-test framing, scoped explicitly to what G3 measures).

### Experimental Setup & Edge Metrics (Pass 3)
All 11 experiments' methodology: sample sizes (n=8 EXP03, n=9 EXP04, n=98 val images, n=44 RAG
chunks/29 queries, n=1467 PSI reference window, etc.), hardware (Apple M4 Pro, CoreML/ANE),
software versions where relevant, what was measured and how (behavioral tracing via real
`apply_rule_override`, fine-grained P/R curve reading vs. `val(conf=X)` trap, perceptual hashing
for leakage, module-identity check for G2). Explicit statement: real deployed-system data, not
synthetic benchmarks; every number traces to a specific experiment run directory.

### Results (Pass 3 — the core section, 5.1-5.6 per pre_writeup_synthesis.md)
- 5.1 Dual-layer decision system (EXP02 module-identity + EXP03 four-bucket + fabrication finding
  as ONE beat + adapter provenance). Formalizations 1 and 2 referenced here. Figure 1, Table 2 (or
  2 placed at section close).
- 5.2 Agentic tool-routing negative result (EXP04), promoted second, "we tried to break this and
  could not" framing.
- 5.3 Edge vision (EXP05/06/07): six-config table, CoreML/ANE latency, INT8-vs-fp32 surprise
  marker, G5-corrected numbers alongside originals with the re-evaluation-not-retrain caveat, the
  0.719-vs-0.782 disclosure as a named callout, sparse-frame gap flagged beside the 0/98 number.
  Figures 2 and 3, Table 1.
- 5.4 RAG (EXP01): F1-argmax vs. deployed threshold, random-baseline margin, asymmetric-cost
  framing. Figure 5 optional.
- 5.5 MLOps/PSI (EXP08): 16-point sweep, the crossover finding (not "H5 confirmed"), the
  three-way gate exercise. Figure 4.
- 5.6 Auxiliary evidence (EXP09 twin_bridge, compressed to one paragraph) + brief data-integrity
  callout to Table 3 (six stale/inconsistent figures) with the live RAG 0.695 leak given rhetorical
  weight, not just a table row.

### Discussion (Pass 4)
Genuine open questions (untested v2 adapter; does narrow-interface pattern hold at larger
on-device scale for agentic routing; does extrapolated sparse-frame risk match reality). One
carefully-hedged conjecture (narrow-enumerable-field interfaces as a transferable safety-design
principle). Practitioner rules (from narrative_brief.md §iv): RAG threshold = asymmetric cost, not
raw F1; PSI-gate on the measured shape of your own distribution, not an assumed convention; select
edge export format by measuring the whole pipeline, not by reasoning about precision in isolation;
audit your own deployed artifacts with the rigor you audit your headline metrics.

### Known Limitations (Pass 4)
n=8 central-result population; single-device edge benchmarking; twin_bridge unresolved (never
"field-validated"); adapter caveat scoped to G3 only, not G4; sparse-frame val-set gap; live
unfixed RAG 0.695 knowledge-base leak flagged prominently as a genuine unresolved production issue;
0.858-vs-0.859 rounding footnote; AQUA-7B format/step-count non-reproduction footnote; EXP08's
internal PSI resampling-seed footnote.

### Conclusion
States the deepened central-claim framing directly (near-verbatim from pre_writeup_synthesis.md
§3). Adds judgment, does not re-abstract. Points to the practitioner rule as the paper's
transferable takeaway. One sentence on what would need to change (leakage-free retrain, live
twin_bridge session, larger on-device agentic model) to strengthen the claim further.

### Acknowledgements
Mandatory pAI/MSc sentence (verbatim, see Pass 4 instructions) + funding/competition
acknowledgement (TEKNOFEST, per README.md's closing line) + author list already given in vision.md.

### Appendix
Full 16-point EXP08 PSveep table; full EXP03 8-scenario per-scenario table (already partially in
body — appendix carries the full manual-coding table); full EXP04 n=9 scenario table if not fully
in body; any other derivation-style detail that would bloat the main body.

## Figures (5, per `resource_inventory.tex` — built fresh in Pass 3/5, no existing plotting code)
Fig 1: EXP03 four-bucket bar chart. Fig 2: EXP07 PR-tradeoff curve (argmax vs. deployed point).
Fig 3: EXP06 six-config latency-vs-mAP50 scatter. Fig 4: EXP08 PSI quantile-vs-equal-width sweep.
Fig 5 (optional): EXP01 RAG threshold P/R/F1 curve.

## Tables (3, per `resource_inventory.tex`)
Table 1: headline metrics (vision + G5-corrected, edge latency, RAG, INT8 delta).
Table 2: per-goal achievement summary (11 goals, strong/minimum_viable).
Table 3: 6 stale/inconsistent figures (data-integrity/transparency table).

## Formalizations (4, labeled "Formalization" not "Theorem" — see `theorem_map.json`)
1. Severity monotonicity (escalate-only invariant).
2. Enumerable vs. non-enumerable failure modes.
3. PSI three-way gate.
4. Vision operating-point tradeoff framing (H7).

---

## PASS 7 — Critical re-read findings (Cycle 2)

Read the full compiled draft (all 12 section files + final_paper.tex) as a skeptical reviewer,
cross-checked against `author_style_guide.md`, `narrative_brief.md`, `pre_writeup_synthesis.md`,
`review_1/pre_writeup_concerns.md`, and spot-checked 15+ headline numbers directly against their
`experiment_workspace/experiment_runs/EXPnn/results.md`/raw-JSON source. Overall verdict: Cycle 1
is exceptionally disciplined — structure, voice, disclosure placement, and formalization labeling
all already match the binding contracts almost exactly. Two genuine issues found, both fixed in
Passes 8-10; everything else below was checked and found compliant (listed for the audit trail).

### Genuine issues found and fixed

1. **Overstated fabrication count (results.tex §5.1, system_architecture.tex Formalization 2
   SOURCE_CLAIM comment).** Both say "6 of 8 [scenarios] contain a fabricated numeric value."
   Checked against `EXP03/results.md` line 67 (the experiment's own synthesis paragraph): only
   3 of 8 scenarios (T02, T05, T08) are shown to fabricate a *specific numeric sensor reading not
   present in the input* — the other 3 "inaccurate" scenarios (T03, T06, T07) are inaccurate for a
   different reason (T03 and T07 make false qualitative claims with no invented number at all —
   "all parameters safe/optimal"; T06 misapplies a plausibly-real temperature value via an
   internally incoherent threshold comparison, not a fabricated one). The correct, source-supported
   claim is "6 of 8 contain reasoning that materially misrepresents the true sensor snapshot, 3 of
   which (including 2 inside the 'agrees' bucket) fabricate a specific numeric sensor value never
   present in the input." This matters precisely because this paper's own thesis is about
   precision in exactly this kind of claim. **Fixed in Pass 9** (results.tex prose + the
   SOURCE_CLAIM comment in system_architecture.tex). The Abstract/Introduction/Conclusion's
   "two of three" framing (the agrees-bucket fabrication rate) was independently re-verified and
   is exactly correct as written — no change needed there.

2. **Conclusion opens by closely paraphrasing the Abstract's central-finding sentences almost
   1:1** (same facts, same order: unparseable/default-safe, fabrication-in-agreement, adapter
   stress-test framing) before pivoting to genuine reflection. The anti-AI voice table
   (`author_style_guide.md` Part B) flags "Conclusion restates abstract" as the anti-pattern to
   avoid, using "reflection, honest limitations, genuine open questions" instead. The back half of
   the Conclusion already does this well (SIS/shielding positioning, concrete future-work list);
   the opening paragraph did not need to re-tread the same sentence shapes to get there. **Fixed in
   Pass 10** — opening reframed to lead with the interface-design judgment rather than
   re-narrating the bucket percentages verbatim.

### Checked and found already compliant (no change needed)

- **Abstract voice rules**: zero `\cite`/`\ref`/`$` in `sections/abstract.tex` (grep-verified);
  0.719-vs-0.782 both present in the same sentence; no "N-fold" opener; opens with the deployed
  system, not a citation or a formula.
- **Surprise markers**: exactly 3 "One might expect..." constructions in the entire manuscript
  (Results 5.1 opening beat, Results 5.3 export finding, plus the Abstract's condensed echo of
  marker 1, which is expected since the Abstract summarizes the paper). The literal word
  "surpris-" appears exactly once, inside marker 1's specified phrasing ("more surprising
  still") — not overused elsewhere. Adapter-provenance sentence (marker 2 per the brief) is
  correctly un-hedged, no "surprisingly," flat declarative "held anyway" register, as required.
- **LoRA adapter caveat scope**: confirmed disclosed at first mention (System Architecture
  §"AQUA-1B and adapter provenance") and repeated at the open of Results 5.1; confirmed the scope
  note explicitly excludes G4/EXP04 in three places (system_architecture.tex, results.tex §5.2
  opening sentence, known_limitations.tex) — never misapplied to the agentic-routing result.
- **Live RAG 0.695 leak**: disclosed in Introduction (prose, not buried), given a full paragraph
  plus Table 3 row 1 in Results §5.6, and restated in Known Limitations as "a genuine, currently
  unresolved production issue" — not a historical footnote anywhere.
- **Number-to-source traceability**: 15 headline numbers spot-checked directly against
  `experiment_runs/EXPnn/results.md` or raw JSON (EXP01 RAG threshold/MRR/hit@1/random-baseline;
  EXP03 adapter provenance + per-scenario bucket/reasoning table; EXP04 agentic %ages across n=5
  and n=9; EXP05 corrected precision/recall/mAP50 ranges via
  `g5_resolution_corrected_metrics_full.json`; EXP06 six-config table incl. INT8/fp32 deltas and
  CoreML p50/p95 latency; EXP07 deployed-vs-argmax P/R and the 0.053/22-28% miss-risk figures;
  EXP08 full 16-point PSI sweep table and the two synthetic-window PSI values; EXP09 18/19 unit
  tests; EXP11 the 0.695 leak and the 43-minute commit gap) — all matched exactly except finding
  #1 above.
- **Results 5.1-5.6 ordering**: matches `pre_writeup_synthesis.md`'s Updated Structural
  Recommendation exactly — G3 (dual-layer+fabrication+adapter, one combined beat) opens; G4
  (agentic negative result) protected second; G7's 0.719-vs-0.782 disclosure is a named
  `\disclosure{}` callout, not a figure caption; G5's corrected numbers are a caveat sentence
  beside Table 1, not a subsection; G9/twin_bridge is one paragraph inside a combined "auxiliary
  evidence" subsection (§5.6), not a standalone subsection.
- **Formalizations**: all 4 labeled "Formalization" via the custom `\newtheorem` environment,
  never "Theorem"/"Lemma"/"Proposition." One deliberate, correctly-scoped exception: system_
  architecture.tex line 38 states "This is not a proved theorem" — an explicit disclaimer, not a
  mislabel — left as-is.
- **Related Work**: organized in the mandated Cluster A / pivot / Cluster B / Cluster C / "what's
  new" structure, argumentative prose with citations embedded in sentences (`\citet{X}'s survey
  organizes...`), not a flat "Author X did Y" catalogue — checked via a pattern grep, only 5 of the
  section's ~20 citations use the `\citet{}...'s` subject-of-sentence form, and each is followed by
  a substantive claim about what that source shows, not a bare summary.
- **Citations**: all 47 distinct `\cite{}` keys used across `sections/*.tex` resolve against
  `references.bib` (script-verified); zero `[cite:` placeholders anywhere.
- **Cross-references**: 78 `\ref{}` usages script-verified against 36 defined `\label{}`s — zero
  orphaned references.
- **Discussion**: the one hedged conjecture uses "suggest"/"do not demonstrate beyond this one
  system"/"a direction worth testing... not a demonstrated generalization" — no "proves" or
  unhedged generalization anywhere in Discussion or Conclusion.

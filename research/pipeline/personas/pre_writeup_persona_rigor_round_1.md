# Rigor & Novelty — Pre-Writeup Council, Round 1

**Reviewer posture:** skepticism by default. **Scope:** formalized_results.md/.json,
resource_inventory.tex, vision.md, research_proposal.md (Round 3 exit synthesis), and
experiment_workspace/verification_results.json + verification_handoff.md, cross-checked directly
against the underlying artifact files where the paper trail left a gap.

## Assessment

The evidence chain is unusually clean for a pre-writeup checkpoint. I spot-checked
`formalized_results.json`'s G3 evidence pointers (`EXP03/results.md`, `EXP03/g3_results.json`,
`verification_results.json`) against the independent verification record and they match exactly:
the 4-bucket tally (agrees=3, under-calls-and-escalated=1, over-calls=0, unparseable=4) is
recomputed independently from `g3_results.json`'s raw `bucket` field, not merely re-typed from
`results.md`, and the verification record explicitly flags that n=8 is the entire fixed scenario
population and "should not be reported as if [percentages] carry a confidence interval." That
caveat is already present at the verification layer, already surfaced in `formalized_results.json`
as a `gap`, and already reflected in `resource_inventory.tex`'s Figure 1 spec (which requires "n=8
stated prominently in the caption" and a bracketed annotation distinguishing "fail-safe defaulting"
from "correction"). This is the right discipline running through three independent layers of the
pipeline before a single sentence of manuscript prose exists. I found no instance, across G1–G11,
of a claim in `formalized_results.md` that outruns its cited `verification_results.json` entry.

The one place I want to press harder is exactly the one the task calls out: G3/EXP03. The 50%
unparseable-defaulted-to-ok / 38% agrees / 12% under-calls-and-escalated / 0% over-calls split is
real, verified, and — critically — *pre-registered as a legitimate outcome before the run*, not a
post-hoc rescue. `research_proposal.md`'s H1 mechanism text (line 46) explicitly names "malformed
LLM output, LLM service unavailability, and a correctly-parsed but under-severe LLM judgment" as
three distinct failure inputs the escalation composition must handle identically. That the dominant
observed case turned out to be the first of those three, not the third, is a finding *within* H1's
own stated scope, not outside it. So the mechanism claim (the merge is monotonic and escalate-only)
survives cleanly. What does not survive unscathed is the *implicit* framing in earlier drafts of
the proposal ("the LLM proposes, the rule engine catches misses") — that framing quietly assumes
the LLM is usually trying, and sometimes needs correcting. EXP03 shows the LLM is mostly not
producing usable output at all (50% garbage) and, on the 7/8 scenarios where it produces prose,
that prose is factually wrong about the sensor state in 6 cases — including 2 of the 3 "agrees"
cases, where the correct status label is reached via an invented causal story. Only 1/8 scenarios
(T01) is both parseable and factually accurate. That is a much weaker claim about the LLM's
contribution than "proposes, sometimes needs correcting," and the writeup will be tempted to soften
it back toward the more flattering framing because the T07 result (garbage input, correct escalated
output) is genuinely a strong data point for the *architecture*. Both things are true at once and
the manuscript needs to hold them without contradiction: the architecture is vindicated; the model
component's usefulness as anything beyond a triggerable, ignorable severity-format emitter is not.

A second-order concern, resolved during this review rather than left open: the council has
repeatedly flagged LoRA adapter provenance as "mtime-only" and unresolvable without git history
(the directory is gitignored). That is true for a *commit-hash* provenance claim, but it understates
what is cheaply checkable from files already on disk. `llm-service/sure-aqua-adapter/adapter_config.json`
points at training data `sure-aqua-adapter/_mlx_data/{train,valid}.jsonl`, which contain 7 and 1
records respectively — 8 total. `finetune.py`'s own docstring names exactly two candidate datasets:
`sure_finetune_data.jsonl` (8 examples, "el yazımı 8 örnek (yetersiz, sadece duman testi)" — "8
handwritten examples, insufficient, smoke-test only") and `sure_finetune_data_v2.jsonl` (128
examples, the documented default). `sure_finetune_data.jsonl` itself has exactly 8 lines. This is a
record-count match, not a hash match, so it is not absolute proof — but it is strong, free,
already-available evidence that **the deployed adapter behind every AQUA-1B number in this paper is
the v1 adapter that the codebase's own training script calls insufficient**, not the untested v2.
That materially changes how the 50%-unparseable finding should be narrated: it is not evidence
about "sub-2B on-device LLMs in this decision-support role" in general, it is evidence about one
specific, self-documented-as-inadequate 8-example LoRA adapter. The paper can and should say this
plainly — it makes the safety argument *stronger*, not weaker (the architecture held up against a
component its own training pipeline warns is undertrained), while closing off a generalization the
current draft plan leaves ambiguous.

## Novelty Analysis (given the empirical findings, not just the literature review)

The literature-review-stage novelty claims (constitutional-AI-style guardrails, LLM-as-advisor
patterns, PSI drift binning, RAG threshold calibration) are reasonable prior-art placements and I
have no rigor objection to them. But the *empirical* run changes what the actually-novel claim is,
and the current framing in `novelty_assessment.json` and the proposal has not fully caught up:

- The pre-registered novelty claim was "a deterministic rule engine with escalation-only precedence
  over an LLM's severity judgment." The *measured* novelty is narrower and, I'd argue, more
  interesting: a system where the deterministic layer never reads anything except one enumerable
  field (`status`) from the LLM, and where — empirically, on this scenario set — that abstinence is
  precisely what keeps free-text hallucination (present in 6/8 outputs, including inside the
  "agrees" bucket) from ever reaching the final decision. The novel finding is not "the rule engine
  corrects the model," it is "the rule engine's narrow interface to the model is what makes the
  model's unreliability harmless" — a claim about interface design (read one enum, ignore the
  prose) rather than about override logic per se. This is worth a sentence of its own in Discussion;
  it is currently implicit rather than named.
- The constant-answer-detection technique (H3/EXP04) and the shared-post-processing-path diagnosis
  (H6/EXP06) both hold up as genuinely small, transferable methodology contributions independent of
  the results they produced — I have no rigor concern there; both are cheaply falsifiable and both
  were independently re-verified (EXP06's per-image ONNX/TorchScript diff at 0/98 meaningfully
  different images is stronger evidence than the design called for).
- The cross-layer thesis (C2 in `exp10_literature_search.md`, "kept OPEN/medium confidence") is
  correctly not oversold. Good discipline — resist any temptation in the writeup to upgrade this to
  "confirmed novel" on the strength of a single confirmatory search pass.

## Logical Gaps

1. **"Escalation-only override" is the headline phrase, but the measured mechanism that actually
   fired most often was *default*-based, not *override*-based.** `apply_rule_override` only visibly
   "overrides" in 1/8 cases (T02) and arguably a second time in spirit (T07, where it escalates a
   *defaulted* status). The word "override" in the paper's title/abstract-level framing risks
   implying the LLM's judgment is routinely present and routinely corrected. Recommend the abstract
   and intro state the mechanism as "escalate-only final authority over an enumerable status field,
   robust to three distinct upstream failure modes (parse failure, service unavailability, and
   genuine under-call)" rather than leading with "override," which the data shows is the rarest of
   the three paths actually observed.
2. **The "agrees" bucket is not epistemically clean.** 2 of 3 "agrees" scenarios (T05, T08) reach
   the correct label via a fabricated causal story. If a reader skims only the 4-bucket bar chart
   (Figure 1) without reading the manual-coding table, they will read "38% agrees" as a success
   rate for the LLM's reasoning, which it is not (only T01, 12.5% of n=8, is coded fully accurate).
   `resource_inventory.tex`'s Figure 1 caption already gestures at this ("See Section~X for the
   fabricated-sensor-value finding, which is invisible to this status-only bucketing") but the
   cross-reference needs to be a hard editorial requirement, not an optional caption line — a reader
   who only sees Figure 1 should not come away more reassured about the LLM than the data supports.
3. **Adapter provenance was reported as an unresolvable gap when it was not (see Assessment).**
   This isn't fatal, but leaving it as "mtime-only, unresolvable" when a two-file record-count check
   resolves it in the model's disfavor (the insufficient v1 dataset) is a case where the honest,
   more-work-required framing was actually less rigorous than the free evidence already sitting on
   disk. This should be corrected before freeze, not carried forward as an open limitation.
4. **n=8/n=9/n=98 generalization risk is already well-guarded in the source documents** (verification
   explicitly says no CI implied, G4's n=9 is stated as "not a sample," G7's 98-image val set is
   flagged for zero sparse-frame coverage). My one addition: watch the Abstract and Conclusion
   specifically — those are the two places in any applied-systems paper where hedged qualifiers
   from Results quietly evaporate under space pressure. "Fixes hallucination via deterministic
   override" is a one-line summary that will be reached for and is not what was shown; "the
   architecture's abstinence from reading LLM prose beat back the LLM's failure to produce anything
   trustworthy, on this scenario set, with this adapter" is the honest one-line summary and is
   admittedly a much harder sentence to make sing. That tension is the writeup's real job here, not
   a rigor defect in the results themselves.

## Required Ablations

None of the remaining items require new experimental runs; they are disclosure/framing fixes, plus
one already-resolvable-from-existing-files provenance question:

1. **Not an ablation, a correction:** replace the "adapter provenance is unresolvable without git
   history" language wherever it appears (`EXP03/results.md`, `formalized_results.json`'s G3 gaps,
   any Known Limitations draft) with the record-count finding above (7+1=8 records in
   `_mlx_data/{train,valid}.jsonl` matching `sure_finetune_data.jsonl`'s 8 lines, which
   `finetune.py`'s own docstring calls "yetersiz, sadece duman testi"). This costs a paragraph, not
   a re-run.
2. **Optional, cheap, not required for validity:** if a second human rater is available before
   freeze, a second coder on the 8 reasoning strings (currently single-rater) would strengthen the
   "6/8 inaccurate" figure, which is qualitative and currently rests on one person's judgment. Given
   the fabrications are numerically checkable against the actual sensor snapshot (e.g., "states 6.0
   mg/L, actual snapshot 5.7 mg/L") rather than requiring subjective judgment, I do not consider this
   blocking — the discrepancies are objective, not interpretive — but a second pass would remove any
   residual "single-rater" caveat cheaply if time permits.
3. No re-run of EXP03 is warranted. The Risk Assessment table in `research_proposal.md` explicitly
   pre-registered this exact outcome ("malformed-output fail-safe is the dominant observed pathway")
   as a legitimate result requiring honest reporting, not a rerun. A rerun cannot change what a
   temp-governed, already-fixed-adapter model emits on a fixed scenario set; it would only be useful
   if the adapter itself changes (e.g., retraining on the 128-sample v2), which is future work, not
   a pre-writeup gate.

## Verdict rationale

The central claim survives, but only in its precisely-scoped form, and the honest version is
actually the more compelling one if the writeup has the nerve to lead with it: this is a system
whose safety property was demonstrated *because* the deterministic layer refuses to read anything
from the LLM except one enumerable field, and where the measured evidence shows that abstinence
being tested against a genuinely unreliable, self-documented-as-undertrained model component 50% of
whose outputs are unparseable and 75% of whose parseable prose (6/8 total) contains fabricated
sensor values — and the final decision was never compromised regardless. That is a *stronger* safety
story than "the rule engine catches the LLM's occasional mistakes," not a weaker one, provided the
manuscript states it in those terms instead of the softer "proposes/catches-misses" framing the
Round 3 proposal narrative still leans on in places. The evidence chain from raw artifact to
verification to formalized result is intact and independently re-checked at every hop I sampled. The
one factual correction available (adapter provenance) makes the paper's disclosed-honesty argument
stronger, not weaker, once made.

VERDICT: ACCEPT

# EXP10 — Cross-Layer Thesis Framing Decision + Confirmatory Literature Search — Results

**Status: SUCCESS (strong criterion met).** This experiment was structurally blocked until now
because it depends on EXP03/EXP04/EXP06/EXP07/EXP08/EXP09 (G3, G4, G6, G7, G8, G9) all having
real, completed results — they now do (all 9 of EXP01–EXP09 are complete; see
`execution_log.json`). This run performs the two things the design doc scoped for it: (1) one
additional confirmatory literature search beyond `literature_review_matrix.md`'s existing Theme 3
sources, and (2) reading back through the real EXP01–EXP09 outputs (not the design pass's
predictions of them) to decide which framing option (CT-1 foreground / CT-2 separate / CT-3
hybrid) the actual evidence supports, and to state the central claim honestly.

Supporting artifacts: `exp10_literature_search.md` (search log, both queries, source-by-source
relevance assessment), `exp10_cross_layer_synthesis.md` (per-experiment held-cleanly-vs-corrected
table).

## 1. Confirmatory literature search — result

Two searches run (queries and full source list in `exp10_literature_search.md`):
1. `multi-layer AI governance case study deployed system deterministic override probabilistic components`
2. `deterministic safety layer probabilistic AI industrial deployment cross-component guardrail empirical evaluation case study`

**Finding: no source surfaced in either search is closer to C2 (the cross-layer thesis) than
`literature_review_matrix.md`'s existing Theme 3 entries (11, 26, 12, 13, 14.1).** The single
closest new hit for the *general* pattern — a 2026 *AI and Ethics* paper on a "bounded
deterministic arbitration kernel" for generative-system moderation — narrows C1 further (yet
another equivalent-known instance of deterministic-override-of-a-probabilistic-classifier, this
time in content moderation) but does not address cross-layer consistency across five
architecturally distinct system surfaces within one deployed production system, nor a disclosed
negative result used as design evidence. The closest "multi-layer" architecture papers found
(the CASE framework; a three-layer assume-guarantee position paper for LLM agents; an
ISO-compliant perception-compute-control robotics safety agent) each decompose the problem along a
different axis than S.U.R.E.'s five-surface decomposition (organizational scale; a single agent's
internal control loop; a single robotics domain) and are proposed architectures or position
papers, not measured, deployed-system studies with a disclosed negative result.

**Per the design doc's own success criteria, this is the "Strong" outcome**: the search confirms
(does not falsify) medium-to-high confidence that no closer prior instance exists.
`novelty_flags.json`'s own stated caveat — confidence is "medium," not "high," because web search
cannot exhaustively rule out an unindexed or non-English prior system — is unchanged by this pass;
a confirmatory search that fails to find a counterexample cannot itself promote medium confidence
to high. **C2's novelty status remains OPEN, confidence medium, exactly as `novelty_flags.json`
already states.** No claim in `novelty_flags.json` needs reclassifying (no BLOCKING finding, no
status change on any of C1–C11) as a result of this search.

## 2. Reading back through the real EXP01–EXP09 results

Full per-experiment detail in `exp10_cross_layer_synthesis.md`. Summary: **zero outright
falsifications, and zero clean confirmations of the literal hypothesis wording on the three
layers that were exercised behaviorally rather than structurally** (EXP03/H1-H2, EXP07/H7,
EXP08/H5). Specifically:

- **EXP03 (the paper's central decision-layer experiment) is the largest complication.** The
  dominant real pathway (4/8 = 50%) is malformed-LLM-output-defaulting-safe, not the "LLM reasons,
  rule engine corrects a genuine miss" dynamic the paper's Narrative Arc was drafted to foreground
  — that textbook under-call-and-escalate pattern occurred in only 1/8 (12%) of scenarios. This
  was pre-registered in `research_goals.json`'s own risk table as a legitimate minimum-viable
  outcome (**"malformed-output fail-safe is the dominant observed pathway, not
  severity-correction"**), so it is not a violated prediction, but it is a materially different
  story than "rule catches LLM miss" implies to a reader. **A second, genuinely unplanned finding
  compounds this**: manual coding of all 8 reasoning strings found 6/8 contain fabricated,
  specific sensor values (e.g. claiming DO=6.0 mg/L when the actual reading was 5.7 or 7.8) —
  including inside the "parseable-and-agrees" bucket, the ostensibly cleanest outcome. Two
  scenarios (T05, T08) reach the *categorically correct* final status via an *entirely invented*
  causal narrative. This is direct, first-time empirical evidence for H2's enumerable/
  non-enumerable boundary — previously a theoretical scope statement corroborated only by
  cross-literature analogy (shielding requires a formally specifiable spec) — now has its own
  concrete, previously-undocumented in-system instance.
- **EXP07 requires a numeric correction to what "the" vision recall means for safety discussion.**
  The trace itself (vision recall → the one rule that consumes it, `fish_count==0`) holds and is
  even more reassuring than hypothesized (0/98 empirical full-frame misses at the deployed
  threshold). But the deployed operating point (conf=0.20) actually runs at P=0.720/R=0.782, not
  the headline academic-argmax P=0.858/R=0.719 the paper has been citing — production recall is
  *higher* than the cited figure, which is good news, but means the paper must stop treating 0.719
  as "the" number that governs real-world full-frame-miss risk.
- **EXP08 gets the direction of its own headline claim backwards at small severities.**
  Equal-width binning is *less* sensitive than quantile at small early shifts (the literal opposite
  of "equal-width jumps early"), becoming more explosive only at larger shifts once one large fixed
  bin empties. The underlying mechanism is confirmed; the qualitative shape of the claim needed
  correcting, and was corrected rather than smoothed over.
- **The layers confirmed by structural/mechanism checks alone held up cleanly or more strongly
  than hypothesized**: EXP02 (identity-level proof, not just matching output), EXP04 (negative
  result strengthened from 5/5 to 9/9 genuinely independent scenarios), EXP06 (near-bit-identical
  ONNX/TorchScript agreement, stronger than the design's own success bar), EXP09 (exactly the
  honestly-incomplete outcome pre-committed in advance — mechanism-tested, not live-validated).
- **EXP05 is a new, unplanned finding orthogonal to the override thesis**: 32 near-duplicate
  train/val frame pairs (14 adjacent-index), a real but milder-than-`ogretmen` leakage risk that
  bears on the integrity of the vision layer's own headline numbers, not on the cross-layer
  override argument itself.

## 3. Framing decision

**CT-3 (the hybrid framing: eval-harness-drift incident as narrative hook, cross-layer thesis
stated with an explicit medium-confidence caveat) remains the best-supported framing** — this
confirms, rather than overturns, the design doc's own prediction. But the real data earns one
further, non-optional refinement beyond generic hedging: **the specific mechanism-level claim
inside the cross-layer thesis must be restated to match what was actually measured, not what was
originally hoped for.**

The defensible version of the claim, given all nine results, is not "a deterministic layer
catches the probabilistic layer's mistakes" (CT-1's implicit framing, and the version EXP03's
headline number would falsify if stated that plainly) and is not "four unrelated engineering
choices, quietly report each" (CT-2, which would under-sell EXP04's and EXP06's genuinely strong,
strengthened results). It is closer to:

> **A deterministic, code-shared component was given sole, escalation-only authority at five
> architecturally distinct layers of one deployed system, and empirically, that authority's most
> common realized function is not sophisticated error-correction but unconditional fail-safe
> defaulting under malformed or uncertain probabilistic output — a real, working, and honestly
> weaker safety property than "the rule catches the model's mistakes," which held in only a
> minority of exercised cases, and which provides no protection at all against a categorically
> correct decision reached via fabricated reasoning.**

This is a **narrower, more precise claim than the original clean narrative, not a retreat from
the cross-layer thesis itself.** All five layers still show the same underlying discipline
(give the deterministic, testable, code-shared component final say; measure what that actually
buys and what it costs); what changes is that the paper must state plainly *which* of that
discipline's benefits was actually observed at what rate, rather than implying "escalation" means
"catches mistakes" as the typical case.

### Draft Abstract/Conclusion sentence (CT-3, medium-confidence-hedged, instantiating the refined claim)

> Across five architecturally distinct, independently probabilistic layers of a deployed
> aquaculture-welfare system — LLM severity reasoning, agentic tool routing, RAG retrieval, MLOps
> retrain-gating, and edge vision — we find consistent, empirically measured evidence for giving a
> deterministic, code-shared component sole escalation-only final authority, including one full
> disclosed negative result (an on-device LLM's near-total failure at agentic tool-calling,
> preserved and strengthened across nine independent scenarios); no closer prior instance of this
> specific five-layer, single-deployed-system composition was found in a systematic (though
> necessarily non-exhaustive) literature search. We report this claim precisely rather than
> cleanly: at the decision layer, the deterministic backstop's dominant observed behavior is
> fail-safe defaulting under malformed model output (50% of exercised scenarios), not
> sophisticated correction of a nuanced misjudgment (12%), and it offers no protection against a
> categorically correct verdict reached through fabricated reasoning — a genuine, previously
> undisclosed boundary of the architecture that this paper discloses rather than elides.

## 4. Confirmatory pass against `novelty_flags.json` — does anything change?

Walked all 11 claims (C1–C11) against the real EXP01–EXP09 findings:

| Claim | Status before | Changed by real data? | Note |
|---|---|---|---|
| C1 | EQUIVALENT_KNOWN | No | EXP02's identity-level proof strengthens the *evidentiary basis* for S.U.R.E.'s specific instance, but does not change the classification — still an application of known SIS/shielding doctrine. |
| **C2** | OPEN, medium | **No status change; framing refined (see §3)** | The confirmatory search (§1) fails to find a closer prior instance, so confidence stays medium (cannot be elevated by a negative search result), and EXP03's complication does not fall the claim to BLOCKING or KNOWN — it means the *instantiation* of the claim must be stated more precisely, which is a framing decision, not a novelty-status change. |
| C3 | EQUIVALENT_KNOWN (theoretical corroboration from shielding lit) | **Strengthened, not changed** | EXP03's fabricated-sensor-values finding is the first *concrete, in-system* empirical instance of the boundary shielding theory predicts in the abstract — recommend citing this as the paper's own worked example of C3, not just the shielding literature's theoretical claim. |
| C4 | PARTIAL | No | EXP04 reproduces and strengthens (9/9) exactly as hoped; no reclassification needed. |
| C5 | PARTIAL | No | EXP01's random-baseline addition strengthens confidence the specific instance is genuine retrieval skill, not corpus-size artifact; the underlying calibration-practice claim was already correctly scoped as PARTIAL. |
| C6 | PARTIAL | No | EXP06's near-bit-identical agreement strengthens the *quantification rigor* argument (the paper's actual claimed contribution per novelty_flags.json's own recommendation), not the novelty classification. |
| C7 | OPEN, medium | No | EXP07 both confirms the trace and supplies a sharper, more concrete instance of the "disclosed blind spot" (quantified extrapolated ~22–28% miss risk at untested k=1) — recommend this remain one of the more confidently stated OPEN claims, per novelty_flags.json's own existing recommendation, now with a stronger concrete number behind it. |
| C8 | PARTIAL/REFORMULATE | No | EXP08's directional correction makes the REFORMULATE recommendation (cite PSI/binning literature explicitly, don't present as a novel discovery) *more* clearly correct, not less — the paper's own contribution is the disciplined per-bin decomposition, which survived. |
| C9 | KNOWN | No | Unaffected; EXP08 confirms `gate()`'s three-way behavior matches spec exactly. |
| C10 | OPEN, medium | No | Not addressed by any of EXP01–EXP09 (it is a literature-landscape question about prior sturgeon-specific systems, not a codebase measurement) — unaffected, still OPEN as originally scoped. |
| C11 | PARTIAL, low confidence | No status change; evidentiary basis strengthened | EXP02 supplies exactly the "documented, real, caught-in-CI motivating incident" framing this claim's recommendation already called for — the underlying facts are now independently re-verified (identity check), not just narrated from the module docstring. |

**Bottom line: no claim moves to BLOCKING; no claim's confidence is upgraded to HIGH by this pass;
the recommended novelty framing from the literature review (foreground C2 as cross-layer
consistency composition, medium confidence, hedged) is confirmed as still correct.** The one
actionable change from this experiment is not to `novelty_flags.json` but to how C2 is
*instantiated* in prose — per §3 above.

## Success criteria assessment

- One additional targeted literature search (plus one variant beyond the minimum): done, logged
  in full in `exp10_literature_search.md`. **Strong criterion met**: confirms medium-to-high
  confidence no closer prior instance exists (medium, unchanged, per novelty_flags.json's own
  ceiling).
- Read back through EXP03/EXP04/EXP06/EXP07/EXP08/EXP09's real (not predicted) results to choose a
  framing: done, in full, in `exp10_cross_layer_synthesis.md` and §2 above.
- One-paragraph framing decision and justification: done (§3).
- Draft Abstract/Conclusion sentence, explicitly hedged to C2's OPEN/medium status: done (§3).
- Honest, non-forced reporting (no fitting the data to the original clean narrative where it does
  not fit): done — EXP03's complication and EXP07's/EXP08's corrections are stated plainly, not
  smoothed over, per this experiment's own guardrail instruction.

## Files
- `results.md` (this file)
- `exp10_literature_search.md` (search queries, full source list, relevance assessment)
- `exp10_cross_layer_synthesis.md` (per-experiment held-cleanly-vs-corrected table)

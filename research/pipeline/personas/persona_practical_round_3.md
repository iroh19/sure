# Practical Compass — Round 3 Evaluation

**Subject:** `research_proposal.md` ("Round 2 Synthesis")
**Round:** 3 of up to 5 (minimum required round; exit requires all three personas to ACCEPT)

---

## Assessment

I went back to the actual codebase rather than trusting the proposal's own citations, because Round 2's core complaint was that a status label ("COVERED") had been allowed to substitute for real substance. Verified directly against `/Users/batuhancitak/Desktop/sure-project`:

- `backend/rules.py` lines 69–77: `fish_count == 0` does escalate to `warning`, not `critical`, exactly as H7 claims, and the code comment even states the vision-failure/fish-at-bottom ambiguity the proposal attributes to it.
- `backend/main.py::apply_rule_override` (line 329) and `SEVERITY = rules.SEVERITY` (line 62) exist as described, and `backend/test_decision.py` contains all three named unit tests (`test_override_escalates_when_model_misses_critical`, `test_override_treats_missing_status_as_ok`, `test_override_treats_unknown_status_as_ok`).
- `llm-service/agent/bench_agent.py` line 159 confirms `--repeat` is a real, already-implemented flag (`ap.add_argument("--repeat", type=int, default=1)`), and lines 190–195 confirm the constant-answer detection logic is exactly `len(chosen) >= 3 and len(set(chosen)) == 1` as H3 states — not an invented statistic.
- `MODEL_RAPORU.md` confirms the epoch-77 correction narrative, the 0.719/0.695 discrepancy, and the M4 Pro / batch 8 / ~1.5–2 hour training-time figure the proposal now cites in the Empirical Plan and Known Limitations.
- `ras-digital-twin-main/` is genuinely gitignored (`git check-ignore` confirms), and `twin_bridge/compare.py` genuinely has no capture file matching the `--replay` schema anywhere in the tree — the "honestly rescoped" claim about Goal 2 is not a rhetorical hedge, it reflects the actual state of the repo.

On the two items I was specifically asked to re-examine: both are genuinely resolved, not re-labeled.

**Edge Vision Pipeline restoration is real.** H6 and H7 are written with the same mechanism/conditions/predicted-observable-consequence rigor as H1–H5, not a diluted version. H7 in particular is a substantive, non-obvious claim (the `fish_count==0` rule checks total-frame absence, not the per-instance recall the headline 0.719 measures — so a systematic per-instance undercount does not trip any current escalation) that I could not find pre-stated in Round 1 or Round 2 documents; it required someone to actually trace `rules.py`'s logic against the metric, which they did. Results 5.3 gives both H6 and H7 a single named subsection. This is the deepening this persona asked for, not padding.

**Known Limitations is now genuinely reader-facing.** Nine items, each written as a sentence a reviewer could lift into a Discussion section, not a risk-matrix row. It contains the hardware/compute detail (M4 Pro, ~1.5–2 hours, batch 8/640px) that was silently dropped in Round 1→2, correctly framed as "the same device benchmarks CoreML/ANE latency," which is exactly the confound-disclosure a practitioner needs to not mistake a single-device number for a hardware-independent claim.

That said, Round 3's mandate is to find what I missed, not to re-certify what's fixed. Two structural issues below are new, and one Round 2 ask was dropped a second time without acknowledgment.

## Scope vs. Vision

1. **Does the proposal address the full scope of the vision?** Yes, and by this round more completely than any prior draft — all four vision.md pillars have hypothesis-level and Results-level homes, plus two vision.md-absent items (agent negative result, `twin_bridge`) remain in scope with executable specificity.
2. **Justified deepening or unjustified retreat?** Net deepening. But see Critical Gaps below: the *mechanism* used to restore Edge Vision (a "sibling question" appended beside, not integrated into, the Central Research Question) reintroduces a milder version of the exact risk it was meant to close.
3. **Vision elements not yet covered:** None outright uncovered. The gap now is not coverage but *weighting durability* — whether the restored elements will survive the transition from this planning document into an actual page-budgeted manuscript (see Critical Gaps #1 and #3).

---

## Structural Recommendation

Re-ranked by practitioner-workflow impact, given the now-stable seven-hypothesis structure:

1. **Agentic tool-calling negative result (H3).** Still the strongest folklore-busting finding — a small on-device model benchmarked and failed at agentic routing, contradicting "more autonomy = more capability." Protected at Results 5.2. No change needed.
2. **Systematic export-format accuracy loss (H6).** The second-strongest practitioner-actionable finding ("measure the whole exported pipeline, not the trained weights"; "quantization isn't where you pay" directly contradicts widespread assumption). Now hypothesis-level and has a named subsection (5.3, shared with H7). This is correctly promoted, finally.
3. **Vision-recall-to-rule trace (H7).** Genuinely novel and load-bearing, but it is also the finding most likely to be *cut for length* precisely because it reads as a caveat ("here is a gap we haven't closed") rather than a positive result. A caveat-shaped finding needs an editor who protects it on principle, not just a hypothesis number — flag this explicitly to whoever drafts, or it disappears a third time under a different mechanism (see Critical Gap #1).
4. **Escalation-only override + eval-harness incident (H1/H2).** Correctly opens the paper. No change.
5. **RAG asymmetric threshold (H4) / PSI binning fix (H5).** Correctly promoted, unchanged from Round 2, no new concerns.
6. **`twin_bridge` cross-implementation status (5.6).** Given the Risk Assessment table's own "High" likelihood estimate that the live-session path fails, dedicating a fully numbered Results subsection to what will most likely be a single "designed, unit-tested, not exercised" sentence risks reading as padding to a reviewer scanning the table of contents for six substantive findings and finding one that isn't. Recommend making 5.6's promotion to a full subsection *conditional* on the go/no-go actually landing a live session; absent that, fold the honestly-scoped non-result into Known Limitations item 4 (where it already lives) rather than double-booking it as a Results subsection with little to report.

---

## Strengths

- Every load-bearing factual claim I spot-checked against the live codebase was accurate — code line numbers, test names, flag names, and file-existence claims all checked out. This proposal is not writing about the system from memory; it is being verified against it round over round, which is exactly the discipline the paper itself claims to have (a nice, and apparently earned, bit of self-consistency).
- H7 is a genuinely new insight, not a restatement: it correctly identifies that the *only* rule consuming vision output checks total-frame absence, and that the reported per-instance recall (0.719) therefore does not map cleanly onto the safety architecture's actual coverage. That distinction is not obvious and is exactly the kind of "so what" a practitioner needs before trusting a detector's headline metric.
- The Known Limitations section finally gives a skeptical reader something concrete to hold the manuscript to, including a specific, named data-integrity hazard (`TODOS.md`'s stale 0.695 vs. the corrected 0.719) that a less careful drafting pass could reintroduce.

---

## Critical Gaps

1. **The Central Research Question itself still frames the paper as four layers; Edge Vision was restored via an appended "sibling question," not by rewriting the sentence a reader is most likely to lift into the Abstract.** The single sentence labeled "Central Research Question" is the one most likely to become the paper's thesis statement verbatim or near-verbatim — that is standard practice, and this proposal's own Narrative Continuity Assessment treats it that way ("is the new story clearer to a practitioner reading the abstract?"). That sentence still says "four independently probabilistic subsystems" and does not mention vision at all; the vision material lives in a separately-labeled "sibling question" directly underneath, carrying the parenthetical **"(restored in Round 2 — do not treat as a footnote)"** — language addressed to this debate, not to a manuscript reader. If a future drafting pass (by a person or a model) does what drafting passes usually do — lifts the "Central Research Question" as the one-sentence thesis and treats the "sibling question" as exactly the secondary material its own label implies — Edge Vision falls out of the paper's single most important sentence for a second time, by a different mechanism than Round 2's demotion, and the internal review annotation risks leaking into a manuscript draft. **Fix:** rewrite the Central Research Question itself to name the sensing layer (e.g., "...five architecturally distinct layers, four probabilistic subsystems reasoning over sensor/vision data plus the vision layer's own operating point..."), and strip debate-internal annotations like "(restored in Round 2 — do not treat as a footnote)" from anything intended to survive into manuscript prose — or clearly quarantine such notes as `[PLANNING NOTE, not manuscript text]` the way the Known Limitations section's italic preamble already does correctly.

2. **The Round 1 "local-LLM cost/resource framing" ask (Round 2 Specific Suggestion #6) was silently dropped again.** Round 2 explicitly said: "if excluded, state that decision explicitly rather than leaving it unaddressed." This proposal does not mention memory/compute cost of running AQUA-1B/7B locally anywhere, including in Known Limitations, and does not state a decision to exclude it. This is a small, cheap ask (a single sentence: "on-device inference cost is out of scope; see [X] for deployment sizing") that has now been asked for twice and answered neither time. Not fatal, but it should not be allowed to disappear a third time by default.

3. **No length/venue budget exists anywhere in this proposal, despite the hypothesis and Results-subsection count having grown from 5→7 and 4→6 respectively across three rounds, entirely in the direction of addition.** Every round of this debate has correctly argued for restoring dropped material (agent negative result, Edge Vision, reader-facing limitations) — but no round has yet asked what gets *compressed* when this now-seven-hypothesis, ten-row-ablation, nine-item-limitations, six-subsection structure meets an actual page limit for a systems/applied-AI venue. This matters specifically for this persona's mandate: an overloaded paper dilutes exactly the findings that most need protected space (H3's negative result, H6's export finding) by forcing even treatment of items with very different practitioner value (compare "quantization isn't where you pay for edge speed," a genuinely surprising, actionable finding, against 5.6's likely single-sentence non-result). **Fix:** add an explicit target length/venue assumption and a stated compression order — which of H1–H7 and which Ablation rows survive first if the draft runs long — so the Structural Recommendation ranking in this and prior rounds actually constrains the draft rather than being read as a wish list applied only if space allows.

---

## Specific Suggestions

1. Rewrite the Central Research Question sentence to explicitly include the sensing/vision layer rather than carrying it only in an appended "sibling question" — this is the single highest-leverage fix in this round because it protects against the exact failure mode (silent demotion at drafting time) that took two rounds to catch and fix once already.
2. Remove or clearly quarantine debate-internal annotations (e.g., "(restored in Round 2 — do not treat as a footnote)") from any sentence that could be copy-pasted into manuscript prose; the Known Limitations section's italic framing note is the right model to follow everywhere else in the document.
3. State explicitly, even in one sentence, whether local-LLM compute/memory cost is in or out of scope for the manuscript (Round 2 ask, still unaddressed).
4. Add a target length/venue assumption and an explicit compression order (what gets cut first, second, third if the draft runs long), so the Structural Recommendation rankings across all three personas' reviews function as binding drafting guidance rather than an unenforced wish list.
5. Make Results 5.6 (`twin_bridge`) conditional: promote it to a full subsection only if the go/no-go actually lands a live session; otherwise fold its content into the Known Limitations item that already covers it, rather than giving an admittedly-likely non-result its own numbered slot in the table of contents.

---

## Verdict

ACCEPT — the two items I was asked to verify hardest (Edge Vision restoration, reader-facing Known Limitations) are genuinely resolved and independently verified against the live codebase, not just re-labeled. The new concerns raised this round (Central Research Question still excludes vision by construction, no length/venue budget governing what survives compression, the cost-framing ask dropped twice) are real but are refinements to a structurally sound proposal, not evidence of practical irrelevance — this system and its findings remain timely, specific, and strong enough to change practitioner behavior. These three items should be closed before drafting begins, not before this council can exit.

VERDICT: ACCEPT

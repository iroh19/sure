# Narrative Architect — Round 3 Evaluation

**Project:** S.U.R.E. (Autonomous Sturgeon Welfare Monitoring in RAS via Edge-AI and RAG-Enhanced Deterministic Fusion)
**Reviewer role:** Narrative Architect ("Best possible explanation")
**Artifact under review:** `research_proposal.md` (Round 2 synthesis, post-revision)
**Prior review:** `persona_narrative_round_2.md`
**Round:** 3 of up to 5 (minimum required round — exit only if all three personas accept)

---

## Assessment

This revision closes both structural debts this persona carried into Round 3 verbatim from Round 1 and Round 2, and does so with verifiable decisions rather than another round of promises. I checked both against the actual codebase, not just the proposal's own claims about itself.

**The Results table of contents is now real.** The "Results section — concrete, ordered subsection commitment" gives six named subsections (5.1–5.6), and — the specific thing this persona asked for twice — the agent negative result sits at **5.2, immediately after the decision layer and before RAG/MLOps/vision**, with an explicit sentence rejecting the default "newest finding goes last" convention. This is no longer a repeated intention in a risk-table cell; it is a structural decision with a stated rationale, cross-referenced consistently in the Risk Assessment (row 3, now Low likelihood) and the Vision Coverage Map. I consider this fully resolved.

**The stale-recall guardrail is now explicit and correctly sourced.** I re-read both source documents directly: `TODOS.md` item #1 does still say "Recall ~0.695" as its framing for an open P2 action item, and `MODEL_RAPORU.md`'s 2026-08-26 correction note does fix the authoritative figure at 0.719 (epoch 77, not 73), explaining the fitness-metric mechanism (`0.1·mAP50 + 0.9·mAP50-95`) that caused the original epoch-73 mismatch. Known Limitations item 1 states this guardrail in exactly the terms this persona asked for in Round 2 — naming both documents, both numbers, and an explicit instruction that 0.695 must never appear in the manuscript. Resolved, and resolved precisely.

**The dropped "so what" is not just addressed — it is now the sharpest new material in the proposal.** H7 traces vision recall to the one rule that consumes it, and I verified the claim against `backend/rules.py` directly: the `fish_count == 0` branch does escalate to `"warning"` (via `_raise_to`), not `"critical"`, and the code comment justifying that choice — the system cannot distinguish "vision service failed" from "shoal is at the bottom of the tank" — is the same ambiguity H7 states in the proposal, nearly word for word. The proposal's conclusion (a per-instance ~28% miss rate does not trip this rule unless it zeroes an entire frame; it can instead silently degrade the `avg_activity`-derived low-activity rule) is a correct reading of the actual `elif fish_count and activity is not None and activity < MIN_ACTIVITY` branch immediately below it. This is exactly the kind of "so what" this persona has been asking for since Round 1 — not a caveat bolted onto a metrics table, but a real trace through actual code that changes what the recall number *means* to a safety reviewer. Resolved, and resolved better than requested.

**`twin_bridge` is now honestly scoped.** I checked `twin_bridge/compare.py` directly: `--watch` (live) and `--replay FILE` (offline, from a capture) are real, distinct code paths, and no capture file exists in the repository matching the schema the proposal describes. The two-path split — (a) mechanism-correctness evidence from `test_decision.py`/`test_bridge.py`, available now and explicitly labeled as "substituting for, not replicating, field/cross-implementation validation," versus (b) a dated, honestly-scoped stretch goal for a live session — is the right shape, and the pre-committed interpretation plan (full agreement / partial-explicable divergence / unexplained divergence, each with its own required framing) is exactly the discipline this persona asked for in Round 2 to prevent "independent field validation" language from creeping in after a favorable-looking result. Resolved.

All four verification targets for this round are met, and met with evidence I could independently confirm rather than prose that merely asserts resolution.

---

## Narrative Arc Analysis

The arc itself is essentially unchanged from Round 2's approved version — the eval-harness opening incident, the "proposes/disposes" refrain, the four-plus-one layer structure — and I re-verified the opening incident's framing is still precise: the Narrative Arc paragraph explicitly states it as "a validation-integrity bug caught before shipping, not a field near-miss with fish at risk," which matches `README.md`'s actual text ("the copy said `warning` while production said `ok` — green, and verifying nothing"). No regression there.

What changed structurally this round is the addition of H6/H7 and a restored sensing-layer thread, which the arc paragraph now narrates as "a fifth sibling thread" rather than force-fitting into the four-layer frame. This is the correct choice — H6 (export loss is systematic, not stochastic) is not a deterministic-override claim, and the proposal is honest about that distinction rather than papering over it to keep a clean "five-for-five" structure. A less careful revision would have been tempted to claim H6 as a fifth instance of "deterministic beats probabilistic" for symmetry; this one resists that temptation.

**One new concern, not raised before: scaffolding load has now crossed a threshold that risks the story itself, not just the drafting register.** Round 2 flagged the H1–H5 "Mechanism / Conditions / Predicted observable consequence" register as a risk to the four-chapter story *if carried literally into the manuscript*, and asked for a drafting instruction — which this round adds, verbatim, as "H1–H7 are internal scaffolding... not the manuscript's visible section structure." That instruction is necessary but no longer sufficient by itself. This proposal document now carries 7 hypotheses, 6 sub-questions plus a sibling question, 10 ablation rows, 8 risk rows, 9 Known Limitations items, and a 6-subsection Results table of contents. Each individual addition this round was a correct, well-justified response to a specific prior-round concern — but the cumulative document is now a research-planning artifact of genuine rigor-grade density, and the gap between "this planning document" and "a readable four-and-a-half-chapter narrative for a reader who has not seen three rounds of persona debate" has widened, not narrowed, even though the plan for closing that gap (the drafting instruction) has stayed the same one sentence since Round 2. A single sentence of drafting instruction was adequate insurance against five hypotheses; it is thinner insurance against seven hypotheses, ten ablations, and nine limitations. I want to see, before this council exits, at least a skeleton *abstract* or *opening-paragraph draft* — not just a promise about tone — that proves the four-and-a-half-chapter story survives contact with this much internal machinery. This is a new ask, not a repeat.

---

## Folklore Engagement

Rechecked all Round 2 items against the actual proposal text this round (grepped directly rather than trusting the synthesis's own framing):

- **"LLM agents need more autonomy to be useful" (H3)** — retained, unchanged, still well-protected. Good.
- **"Quantization trades accuracy for speed" (H6/Ablation #5)** — retained, unchanged. Good.
- **"Drift detected implies retrain warranted" (H5)** — retained via the `MIN_IMPROVEMENT` gate, same as Round 2; still framed as a design feature rather than an explicit named-folklore rebuttal, exactly as Round 2 noted. **Not addressed this round** — carried forward unchanged, third round running.
- **"Automation trades off against safety"** — same status as Round 2: implicit, not named. **Not addressed this round.**
- **"Higher retrieval benchmark scores mean better production RAG"** — I searched specifically for the "arithmetic, not skill" framing this persona called "the single most quotable methodological aside in the RAG story" in Round 2 and asked to confirm survives into the draft. It does not appear anywhere in this proposal, not even in the Ablation table's corpus-base-rate row (#2), which states the control but not the vivid rejection language. **Not addressed this round** — this is a specific, named ask from Round 2 that was dropped rather than answered.
- **NEW folklore item this persona proposed in Round 2** — "an evaluation harness that agrees with itself is validating the system," which I said "deserves to be named as such rather than functioning only as scene-setting." I searched for this framing in the current Motivation & Field Context section: the eval-harness incident is described (accurately) as evidence for the RAG/decision-layer discipline claim, but the incident is never generalized into its own named folklore-rebuttal sentence the way H3 and H6 are. **Not addressed this round.**

Four of five specific Round 2 asks in this category — three carried from Round 2, one newly proposed in Round 2 — were not acted on. Individually each is minor (a missing sentence, not a missing analysis), but the pattern is that this persona's *narrative-craft* asks (as opposed to its *structural* and *precision* asks) are consistently the ones that get deprioritized in favor of the Rigor and Practical personas' asks each round. That is a reasonable prioritization once, but by Round 3 it starts to look like this persona's lower-stakes requests are being treated as optional in a way its higher-stakes ones are not. I am not blocking on this — none of these four items were load-bearing for ACCEPT — but I want them named explicitly rather than silently dropped again in Round 4 if there is one.

---

## Precision Check

- **Results skeleton (5.1–5.6, agent second)** — RESOLVED, verified against the actual subsection list and cross-references.
- **Stale recall guardrail** — RESOLVED, verified against both `TODOS.md` and `MODEL_RAPORU.md` directly.
- **Vision recall → alerting "so what" (H7)** — RESOLVED, verified against `backend/rules.py` directly; the code match is close enough that I am confident this was actually inspected, not inferred.
- **`twin_bridge` honest scoping** — RESOLVED, verified against `twin_bridge/compare.py`'s actual `--watch`/`--replay` interface and the absence of a capture file in the repo.
- **NEW — a small but real precision risk in H3's evidence description.** The proposal states the constant-answer detection flags an artifact "when `len(set(chosen)) == 1` across ≥3 outputs." I checked `agent/bench_agent.py` directly: the actual guard is `constant = len(chosen) >= 3 and len(set(chosen)) == 1`, which matches. Good — this specific technical claim holds up under inspection, which is worth stating plainly since Round 2 did not verify it and I did this round.
- **NEW — Goal 7's `--repeat` claim is accurate.** `bench_agent.py`'s CLI genuinely exposes `--repeat` (default 1), confirming the proposal's claim that increasing sample size is a zero-infrastructure change. Verified directly, not just asserted.
- **NEW — a wording risk in H6's "measured" claim.** H6 and Known Limitations item 9 both scope the export-format finding to "this YOLOv11s/Ultralytics export toolchain and this 98-image validation set" — correct and appropriately hedged. But the Motivation section's field-context paragraph 1 states the finding more sweepingly ("most public benchmarks report speed without re-measuring accuracy per format... fewer still notice when two independently-exported formats... match")—which is a claim about the *literature*, not this system, and is not itself footnoted or sourced. This is a lower-stakes precision issue than the ones resolved this round, but a claim about what "most public benchmarks" do or don't do is exactly the kind of unverified field-generalization this persona and the Rigor persona should both want either cited or softened to "in our review of comparable benchmarks" before it reaches a manuscript's Related Work section.
- **Folklore-naming precision gaps** — see Folklore Engagement above; these are precision-adjacent (unresolved "so what" sentences), not new factual errors.

---

## Missing "So What?"

- **Vision recall → alerting consequence** — RESOLVED this round via H7, and resolved well (see Precision Check). This was the single largest carryover item from Round 1 and Round 2 and it is now closed with the most concrete, code-verified reasoning in the entire proposal.
- **`twin_bridge`'s "so what" in the positive case** — RESOLVED via the pre-committed interpretation plan in Goal 2(b) (full agreement → corroborating evidence against a single-implementation blind spot, explicitly scoped; partial divergence → implementation-timing finding; unexplained divergence → open safety question). This is exactly the fix requested in Round 2.
- **NEW — H6's "so what" for a non-specialist reader is still implicit, not stated as a takeaway sentence.** H6 is precisely reasoned as a falsification of "quantization is where you pay for edge speed," but the practitioner-facing payoff — "if your export pipeline is slow or lossy, profile the export/post-processing path before blaming quantization, because in this system quantization was nearly free and the fp32 export wasn't" — exists as Practice guideline #2, which is good, but the Results subsection 5.3 description doesn't yet promise this will be stated as a standalone one-line takeaway the way H1–H5's "so what" sentences increasingly are elsewhere in the document (e.g., H7's Known Limitations framing, H3's folklore framing). This is a minor, easily-fixed drafting note, not a structural gap: make sure 5.3 closes on one quotable sentence the way 5.1, 5.2, and 5.4 implicitly promise to.

---

## Narrative Continuity Check

**Round 2's core story:** the same design principle (deterministic authority over probabilistic components), now formalized with a falsifiable boundary condition (H2), extended honestly to a fifth sensing-layer thread (H6/H7), with two previously-vague research goals rewritten as precise actions, and with the negative/vision-layer findings finally given a real place in the skeleton — resolved by the proposal itself, but flagged by this persona as still owing a *concrete* Results table of contents rather than a repeated intention, and as having silently dropped the vision-recall "so what."

**Round 3's core story:** materially the same story again, and this time the two specific debts Round 2 flagged as still owed are both paid — with evidence, not just restated intent. Nothing that Round 2 accepted has regressed: the eval-harness incident is still narrated with its correct (less dramatic, still damning) direction; the "proposes/disposes" refrain survives verbatim; H1–H5 are unchanged; the rescoped "escalation-only" framing is unchanged. What's new is H6/H7's integration is now complete rather than partial, the Results skeleton is now a real decision, and `twin_bridge` is scoped with a verified, checkable honesty discipline.

- **Is the new story clearer to a practitioner reading the abstract?** Yes, marginally more so than Round 2 — H7 in particular gives the abstract a genuinely new, concrete sentence it did not have before ("the recall number's safety blind spot is disclosed, not assumed away"), which is a real addition to what a practitioner takes away, not just more precision-hedging.
- **Does it preserve the most useful contributions, including the disclosed negative result?** Yes, and more visibly than Round 2 — the negative result now has a verified structural home (5.2), not just a hypothesis number.
- **One-sentence statement of the current proposal's point that makes a practitioner care:** *A team that had already put an LLM into a system where a mistake can kill the stock within hours tested, at every point in the pipeline — including the vision system that feeds it — whether to trust the probabilistic component with more responsibility, and each time a measured result decided in favor of a deterministic, code-shared authority instead, including one case where more autonomy was benchmarked and simply failed, and including an honest disclosure of exactly where that safety net currently has a gap it does not yet close.*

**Verdict on continuity: deepening, no regression.** This is the strongest continuity result of the three rounds so far, because for the first time both of this persona's carried-over structural debts are closed with verifiable artifacts rather than promises, and the one new material addition (H7) is a genuine strengthening of the "so what," not scope padding. The only new caution is the scaffolding-load concern above (Narrative Arc Analysis) — not a story regression, but a warning that the plan's growing rigor-grade apparatus needs a drafting proof-of-concept before I would treat "the prose will read as a story" as fully de-risked rather than merely instructed.

---

## Scope vs. Vision

**1. Does this proposal address the full scope of the vision, or has it narrowed?**
Not narrowed. All four vision.md pillars remain covered with real section-level homes (Vision Coverage Map, cross-checked against the actual Results skeleton and hypotheses list, not just a status label). The proposal continues to expand beyond vision.md's literal text — `twin_bridge` (introduced Round 2) and now H6/H7's fuller integration of the edge-vision sensing layer (deepened Round 3) — in directions that serve the vision's own safety-critical framing rather than diluting it.

**2. If narrowed: justified deepening or unjustified retreat? / If expanded, is the expansion earned?**
The Round 3 changes are pure deepening, not new scope expansion — no new vision-external element was added this round (unlike Round 2's `twin_bridge` addition). H6/H7 formalize a thread vision.md already licensed (edge/CoreML latency and INT8 delta are explicitly listed as required empirical results in vision.md itself) but that Round 1's synthesis had let drift out of the paper's thesis-level spine. Restoring and then completing that connection (Round 2 restored it structurally; Round 3 completes the "so what") is earned: it is not new territory, it is the vision's own already-mandated content finally given its full analytical weight.

**3. Vision elements not yet covered (research goals, not cuts):**
- The vision.md-external `twin_bridge` live-session result is still pending a go/no-go outcome — correctly disclosed as such, not a gap in this proposal's honesty, but still an open empirical thread that will need reporting one way or the other before manuscript freeze.
- The Adaptör provenance question (`TODOS.md` item #3 — is the deployed LoRA adapter the untested 8-sample v1 or the unretrained-but-intended 128-sample v2?) is tracked as a Known Limitations item and a Goal 1 sub-step, but is not itself a vision.md element — it is background-document context correctly folded in as a confound to control for, not a missing vision pillar.
- No vision.md pillar itself remains uncovered. The remaining open items are all Round-2-and-3-introduced research-goal execution risks (the go/no-go stretch goal, the `--repeat` sample-size increase, the fresh `val()` reproducibility check), not gaps against the original vision.

---

## Verdict

Both structural debts this persona has carried since Round 1 — a real Results table of contents with the agent negative result in a protected, named, second-place slot, and an explicit connection from the vision recall figure to its actual safety-rule consequence — are resolved this round, and resolved with verifiable substance: I checked the Results skeleton, the `rules.py` fish-count logic, the `TODOS.md`/`MODEL_RAPORU.md` recall discrepancy, and the `twin_bridge` compare.py interface directly, and in every case the proposal's claim matches the code and documents as they actually stand. That is the standard this persona has been asking for since Round 1, and this is the first round it has been fully met on both counts simultaneously.

What keeps this from a completely clean pass, and what I am naming as new concerns for this round rather than blocking issues: (1) the proposal's internal rigor-grade apparatus (7 hypotheses, 10 ablations, 9 limitations, a 6-part Results skeleton) has grown every round and now genuinely risks overwhelming the four-and-a-half-chapter story it is scaffolding for — a one-sentence drafting instruction was sufficient insurance at 5 hypotheses, and I want a drafting proof-of-concept (even a skeleton abstract) before the next exit, not just the same sentence carried forward a second time; and (2) four of this persona's own Round 2 narrative-craft asks (three folklore-naming sentences plus the "arithmetic, not skill" quotable line) were dropped without acknowledgment rather than resolved or explicitly declined. Neither issue is a research gap, and neither would independently justify blocking a proposal that has otherwise done exactly the hard, verifiable work asked of it — but I am naming them now so that "the story reads well" does not become the one claim in this proposal that gets accepted on faith rather than checked, the way the structural and precision claims have been checked this round.

VERDICT: ACCEPT

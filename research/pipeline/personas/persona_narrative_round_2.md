# Narrative Architect — Round 2 Evaluation

**Project:** S.U.R.E. (Autonomous Sturgeon Welfare Monitoring in RAS via Edge-AI and RAG-Enhanced Deterministic Fusion)
**Reviewer role:** Narrative Architect ("Best possible explanation")
**Artifact under review:** `research_proposal.md` (Round 1 synthesis, post-revision)
**Prior review:** `persona_narrative_round_1.md`

---

## Assessment

This revision is a genuine execution of the story this persona asked for, not a cosmetic pass. The four-layer "deterministic component disposes, probabilistic component proposes" thesis is now stated as the Central Research Question rather than left implicit; the agent-autonomy negative result has been promoted to a formal hypothesis (H3) with its own predicted observable consequence; and the "solves LLM unreliability" framing has been rescoped, consistently and repeatedly (Motivation, H2, Risk row 4, Vision Coverage Map), to "escalation-only deterministic override for enumerable safety thresholds." This is precisely the narrowing this persona demanded in Round 1, and it appears everywhere the claim is made, not just once as a hedge — that consistency is what separates a genuinely resolved concern from a token concession.

The weakest carry-over is the one this persona called "the single most important thing to flag" in Round 1: the mandated skeleton has no named slot for the Agent or MLOps findings. The proposal's response is a single sentence, repeated in two places (Risk Assessment row 3, Vision Coverage Map) in near-identical language: "add explicit named Results subsections... do not rely on the literal skeleton headings alone." That is a stated intention, not yet a structural commitment — there is no actual list of subsection headers, no indication of where in "Results" the agent finding sits relative to vision/RAG/MLOps, and no acknowledgment of the ordering question (does the negative result get top billing, as this persona argued, or does it default to last-because-newest?). A risk-table mitigation and a coverage-map status flag are the right instinct, but they are still promises about the next drafting step, not decisions this proposal itself has made. Given that this is the second round and the concern was flagged as the top risk in Round 1, this persona expected an actual proposed table of contents by now, not the same sentence restated in a different table.

The proposal also introduces one new element this round — `twin_bridge` PLC/CODESYS cross-validation as sub-question 2 — that is a genuine scope expansion beyond vision.md (a research goal properly, not a cut), but it carries a narrative risk the proposal only partly reckons with: the Risk Assessment itself rates "no usable captured session exists" as Medium-High likelihood, and its proposed mitigation is to "generate one from an existing recorded demo session" if none exists. If that is what happens, the paper must be very careful not to let the resulting comparison read as independent field validation when it would actually be a session assembled specifically to produce a result for the paper. This is a precision risk worth naming explicitly now, before drafting, not after a synthetic session has already been produced and the temptation to describe it generously has set in.

---

## Narrative Arc Analysis

**Current arc:** The Narrative Arc section adopts almost verbatim the structure this persona proposed in Round 1 — open on a concrete incident, state the thesis, walk four layers, close on disclosed limitations as a credibility argument. The specific opening hook chosen — the eval harness whose copied rule logic drifted from production and "reported green while validating nothing" — is a stronger and more concrete choice than the resonant-question framing this persona suggested in Round 1 ("can you trust an LLM with a decision that can kill your stock in hours"). A real, specific, previously-shipped bug is more persuasive than a rhetorical question, and it does real narrative work: it justifies the entire architecture's paranoia before a single metric appears. This is a strengthening of the arc, not a regression, and it is grounded — I verified the incident against `README.md` ("on `fish_count == 0` the copy said `warning` while production said `ok` — green, and verifying nothing").

**One precision note that affects the arc's honesty, not just its rigor:** the direction of the drift matters for how dramatically this can be told. The harness's stale copy was *more* conservative (`warning`) than production (`ok`) on that scenario — meaning the bug did not let a dangerous case slip past silently in the field; it let a *test* silently validate nothing, while production's actual behavior on that scenario has apparently never been independently checked either. The manuscript should tell this exactly as the README does — a caught, never-shipped-to-production measurement bug — and must not let the dramatic framing ("silently missing a safety-critical threshold") imply a field incident with fish at risk. The bug is about the *evaluation's* integrity, not a production near-miss; conflating the two in service of a punchier opening paragraph would be exactly the kind of overclaim this persona exists to catch. Tell it precisely and it is still the best opening line in the paper; oversell it and it becomes the first sentence a careful reviewer discounts.

**A drafting-register risk, new this round:** H1–H5 are now written in a rigor-grade "Mechanism / Conditions / Predicted observable consequence" register, which is exactly right for satisfying the Rigor persona and for methodological transparency. But if this structure is carried literally into the manuscript's prose — five numbered hypothesis blocks in sequence — the paper will read as a psychology-style hypothesis-confirmation report, not the four-chapter story this persona fought for. The proposal's own Narrative Arc paragraph shows the fix already exists in the same document (four chapters, one refrain, escalating tension) — the risk is losing that framing at the drafting stage by defaulting to "Section 4.1 tests H1..." headers. This should be flagged explicitly as a drafting instruction: hypotheses are the internal scaffolding: the visible prose is the four-layer story.

**Takeaway:** the arc is stronger and more concrete than Round 1's proposed version, provided the eval-harness incident is narrated with its actual (less dramatic, still damning) direction, and provided H1–H5 remain scaffolding rather than becoming the manuscript's visible section structure.

---

## Folklore Engagement

All five folklore items from Round 1 survive into this proposal and are now backed by named hypotheses and control rows, not just prose gestures:

- **"LLM agents need more autonomy to be useful"** — now H3, with a specific predicted observable (AQUA-1B 0%/0%, AQUA-7B's 50% exposed as a constant-answer artifact) and its own Ablation row (#3) bounding the claim to this model/prompt/scenario set. Good — the strongest folklore-busting material is now structurally protected against the skeleton compressing it, even if the *heading* commitment (see Assessment) is still pending.
- **"Automation trades off against safety"** — implicit in the cross-layer framing (Expected Contributions/Systems); could still use one explicit sentence in Related Work naming this as the dichotomy being rejected, rather than leaving readers to infer it from four examples.
- **"Higher retrieval benchmark scores mean better production RAG"** — retained via H4 and Ablation row #2 (corpus-size/base-rate check), though the specific `fixed-480w` "arithmetic, not skill" rejection that made this vivid in Round 1's source material is not named in the current proposal text. Worth confirming it survives into the draft, since it is the single most quotable methodological aside in the RAG story.
- **"Quantization trades accuracy for speed"** — retained via Ablation row #5 (explicitly refusing to overclaim the INT8 delta as a benefit). Good, unchanged discipline from Round 1.
- **"Drift detected implies retrain warranted"** — retained via H5 and the `MIN_IMPROVEMENT` gate in Expected Contributions/Practice #4, though again framed as a design feature more than a folklore rebuttal; one explicit sentence in Related Work or Discussion naming "drift alarm ≠ retrain mandate" as the assumption being tested would sharpen it.

**New folklore worth adding this round:** "an evaluation harness that agrees with itself is validating the system." The eval-harness drift incident is itself a rebuttal of this — a green eval can validate nothing if its logic has silently diverged from what it's supposed to check. This is arguably a sixth folklore engagement hiding in the proposal's own chosen opening anecdote and deserves to be named as such rather than functioning only as scene-setting.

---

## Precision Check

Round 1 items and their current status, plus new items found this round:

- **"Solves LLM unreliability" framing** — RESOLVED. Rescoped consistently to "escalation-only deterministic override for enumerable safety thresholds" across Motivation, H2, Risk row 4, and the Vision Coverage Map. This is the strongest single improvement in the revision.
- **Small-sample scoping (RAG, agent n=2, single-device latency)** — RESOLVED, and more thoroughly than requested: the Ablation & Control Strategy table gives each scoping risk a named control (repeat CoreML across sessions; report corpus/chunk/query ratios plus a baseline; report scenario-level outcomes rather than aggregates only). This is concrete methodology, not a promise.
- **Skeleton has no slot for Agent/MLOps findings** — PARTIALLY RESOLVED, see Assessment. Commitment exists; concrete section headers do not yet.
- **NEW — stale recall figure risk is now demonstrably live, not hypothetical.** Round 1 flagged this abstractly ("must not cite a stale number by accident"). Checking the actual source materials confirms the risk is real and specific: `TODOS.md` item #1 still states "Recall ~0.695" as the open weak point requiring action, while `MODEL_RAPORU.md`'s 2026-08-26 correction (the same correction this persona praised in Round 1) fixes the authoritative figure at 0.719 (epoch 77, not 73). The proposal's own Empirical Plan correctly cites 0.719, but TODOS.md — one of the four background documents feeding this pipeline — still carries the superseded 0.695 figure as its framing for an "open" action item. Anyone drafting from TODOS.md without cross-checking MODEL_RAPORU.md's correction note would silently reintroduce the exact error Round 1 warned about. This should be an explicit note in the proposal: "TODOS.md item #1 pre-dates the epoch correction; all recall references in the draft must resolve to 0.719 per MODEL_RAPORU.md, never to TODOS.md's 0.695."
- **NEW — the eval-harness incident's direction of drift, as above**, must be narrated precisely (a validation-integrity bug, not a field near-miss) to avoid an opening-paragraph overclaim.
- **NEW — `twin_bridge` cross-validation, if synthesized from a demo session rather than a genuinely captured independent run,** must not be described with language implying organic, field-collected independent validation. "Designed and exercised against a reconstructed replay session" is accurate; "independently validated by the PLC logic" is not, if the session was assembled to produce this comparison.
- **Vision operating-point caveat** — still correctly present (Empirical Plan Goal 6), unchanged from Round 1's resolution.

---

## Missing "So What?"

- **Vision recall (0.719) → alerting consequence** — STILL MISSING. Round 1 asked for an explicit statement connecting the ~28% miss rate in dense frames to the system's actual alert logic (e.g., does undercounting risk masking a legitimate `fish_count == 0` → `warning` condition?). This connection does not appear anywhere in the Round 2 proposal — not in Empirical Plan Goal 6, not in Expected Contributions. This is a carried-over gap, not a new one, but it is now the single most conspicuous unresolved "so what" from Round 1's list, since every other item on that list (RAG threshold, PSI binning, agent benchmark) now has an explicit home in a hypothesis or a Practice guideline.
- **RAG threshold, PSI binning, agent benchmark** — RESOLVED. Each now has a portable one-line takeaway as an Expected Contributions/Practice guideline (#5, #4, #3 respectively). This is exactly the fix this persona asked for.
- **Edge export findings** — RESOLVED via Practice guideline #2 ("measure fp32 export accuracy in isolation before attributing loss to quantization"), which is the crystallizing sentence this persona asked for in Round 1.
- **NEW — the `twin_bridge` sub-question has no "so what" yet even in the success case.** If `compare.py --replay` shows high agreement between `rules.py` and the PLC logic, what does that add beyond restating H1's self-consistency claim with a second implementation? The proposal should state up front what a positive result here would mean for the argument (independent corroboration against a single-implementation blind spot) so that the eventual result — whichever way it comes out — has a stated purpose rather than being run because it was available.

---

## Narrative Continuity Check

**Round 1's core story (as this persona articulated it, since no proposal existed to compare against):** S.U.R.E. is not four feature reports; it is one design principle — deterministic authority over probabilistic components — tested independently at four layers, with the agent-autonomy negative result as the strongest, most under-elevated piece of evidence, and the paper should open on a resonant question and close each layer on a restatable one-liner.

**Round 2's core story:** Materially the same story, now formalized: the Central Research Question states the four-layer test explicitly; H3 gives the agent finding named, protected standing; the "proposes/disposes" refrain survives verbatim in the Narrative Arc section; and the opening hook has been upgraded from a rhetorical question to a real, sourced incident (the eval-harness drift bug), which is a genuine improvement in concreteness.

- **Is the new story clearer to a practitioner reading the abstract?** Yes. The Central Research Question is more precise than Round 1's implicit framing, and the rescoped "escalation-only override for enumerable thresholds" language, while more hedged, is more honest and just as easy to state plainly in an abstract.
- **Does it preserve the most useful contributions, including the disclosed negative result?** Yes — the negative result is more protected structurally now (named hypothesis, dedicated ablation row, explicit risk-table commitment to a Results subsection) than it was in Round 1's raw materials, where it was a sub-clause of vision.md's item 3.
- **One-sentence statement of the paper's point that makes a practitioner care:** *A team that had already put an LLM into a system where a mistake can kill the stock within hours tested, at four separate points in the pipeline, whether to trust that LLM with more responsibility — and each time, a measured result, not caution, decided in favor of a deterministic, code-shared authority instead, including one case where giving the model more autonomy was benchmarked and simply failed.*

**Verdict on continuity: no narrative regression.** The story is more precise, not more abstract, and every element this persona fought to protect in Round 1 (the agent finding, the practitioner-facing framing, the refrain) is present and, in most cases, structurally reinforced rather than merely repeated. The one place continuity is still owed a concrete answer, rather than a repeated intention, is the Results table-of-contents question — that is unfinished business carried forward, not new damage.

---

## Scope vs. Vision

**1. Does this proposal address the full scope of the vision, or has it narrowed?**
It has not narrowed — it has expanded, in a justified direction. All four vision.md pillars (dual-layer decision, edge vision, RAG, MLOps) remain fully covered (per the Vision Coverage Map, all marked COVERED), and the proposal adds one genuinely new empirical thread not present in vision.md at all: the `twin_bridge` PLC/CODESYS independent cross-check (sub-question 2). This is scope growth in service of the vision's own safety-critical framing, not scope creep away from it.

**2. If narrowed: justified deepening or unjustified retreat? / If expanded, is the expansion earned?**
The `twin_bridge` addition is earned in principle — it is real, already-built code (`registers.py`, `client.py`, `compare.py`, `test_bridge.py` all exist and were verified) sitting unused in the source material, and using it to independently corroborate the decision-layer claim strengthens exactly the layer the whole thesis rests on. The one caveat, raised above, is that the Risk Assessment itself expects a Medium-High chance of having to *construct* rather than *find* a replayable session — the paper must describe whatever it ends up with precisely, or the "expansion" becomes an unjustified overclaim of independent validation dressed as new scope.

**3. Vision elements not yet covered (research goals, not cuts):**
- The Results section's actual structure (named subsections giving the Agent and MLOps findings top billing) is still an intention, not a decision — this remains the single largest open structural item carried from Round 1.
- The vision-recall → alerting-consequence connection (does the ~28% miss rate risk masking a legitimate `fish_count == 0` warning?) is still nowhere in the proposal and should be added as an explicit analysis goal, not left to be discovered during drafting.
- The stale-figure risk (TODOS.md's superseded recall 0.695 vs. the corrected 0.719) is a concrete, checkable hazard for the drafting stage that the proposal has not yet flagged by name, even though it flagged the abstract version of this risk in Round 1.
- The `twin_bridge` sub-question's "so what" in the positive case is not yet stated — a research goal to close before the result is in hand, so the eventual finding has a pre-committed interpretation rather than a post-hoc one.

---

## Verdict

This revision does the hard part correctly: it resolves the framing overclaim with real consistency across the document, and it resolves the small-sample scoping concerns with actual named controls rather than promises. It also strengthens the narrative arc with a better, sourced opening incident than this persona proposed in Round 1. What keeps this from a clean pass is that the proposal's single largest structural commitment from Round 1 — giving the Agent and MLOps negative results a named, protected home in the mandated skeleton — is still expressed as an intention restated in two tables, not as an actual decision about section headers and ordering, and one Round 1 "so what" (vision recall's alerting consequence) was dropped rather than answered. Both are fixable without new experiments — this is a drafting-discipline gap, not a research gap — but a story this persona is being asked to fight for should not still be asking "trust us, we'll structure it right later" on its second pass through the same reviewer who raised the concern.

VERDICT: ACCEPT

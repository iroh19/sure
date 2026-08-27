# Pre-Writeup Council — Practical Compass — Round 1

**Mandate:** Timely & compelling for practice.
**Inputs read:** `research_proposal.md` (Round 3 exit synthesis), `formalized_results.md` / `.json`, `resource_inventory.tex`, `vision.md`.

## Assessment

The proposal survived contact with the data better than most three-round syntheses do, and in one specific place it got *more* practitioner-valuable than it was designed to be. G3's four-bucket behavioral trace was proposed as a test of whether the escalate-only mechanism actually fires in practice; what it returned instead is a sharper, more useful finding than the one it was designed to confirm. The dominant real pathway is not "LLM proposes a slightly-wrong severity, rule engine corrects it" (12%, 1/8) — it's "LLM output doesn't parse, defaults to the safety floor, and the rule engine runs alone" (50%, 4/8). That is a better, more defensible practitioner principle than the one in the One-Paragraph Pitch: don't architect your safety net assuming the model usually works and occasionally needs a nudge; architect it assuming the model frequently produces nothing usable at all, and verify your fallback default is the conservative one. This is a stronger, more general claim than "rule catches miss," and it survived a second, uninvited scrutiny: 6/8 reasoning strings contain fabricated sensor values, including 2 cases *inside* the "agrees" bucket — meaning status-only validation would have called those two scenarios a clean success. That is the paper's single most surprising and most exportable result, and it is currently sitting inside a Methodology formalization paragraph and a Figure 1 caption footnote rather than being treated as the headline it is.

Two other things happened that change the story's shape. First, the agent-routing negative result got *stronger*, not weaker, under re-run (n=5→n=9, AQUA-1B holds at 0%/0%, AQUA-7B's constant-answer artifact holds on both n=5 and n=9) — good, that is exactly the kind of result a practitioner paper wants: a negative finding that survives someone trying to break it. Second, the vision layer produced a finding vision.md never asked for and the original H7 language undersells: the deployed system does not run at the headline recall (0.719) at all — it runs at conf=0.20, which is R=0.782, a materially different and *more reassuring* number governing the actual safety question. A practitioner reading only the headline metrics table would draw the wrong safety conclusion about this system. That is a genuinely timely, generalizable point (report the metric at your deployed operating point, not your academic argmax) and it is currently filed as "Emergent Finding #3," several rungs below where its practical weight warrants.

The resources are adequate in coverage but currently organized around the hypotheses' original billing, not the results' actual weight. Nothing here is fabricated or oversold — the reverse problem is closer to the truth: the audit trail (G1–G11, six emergent findings, an 11-item Known Limitations list, a self-audit that found a stale figure living in the system's *own* production RAG corpus) is honest to the point of being structurally unwieldy, and a practitioner-relevant paper lives or dies on whether the three or four sharpest findings are unmistakably in the reader's face by page 3, not distributed evenly across eleven equally-weighted goal writeups.

## Strengths

- **The EXP03 fabrication-inside-agreement finding is a genuinely new, exportable practitioner rule**: status-level correctness does not imply reasoning-level trustworthiness. This generalizes far beyond aquaculture and is citation-bait for anyone building LLM-plus-validator pipelines.
- **The agent-routing negative result replicated under adversarial re-run** (new scenarios, not `--repeat` padding — the team correctly retracted that shortcut in Round 3). A negative result that survives someone trying to strengthen the sample is rare and valuable.
- **The 0.719-vs-0.782 deployed-operating-point disclosure** is a crisp, immediately actionable principle for any team benchmarking a detector feeding a safety rule: report the number at the threshold you actually run, not the one that makes the results table look cleanest.
- **The self-audit finding its own knowledge base carrying a stale figure** is an unusually honest, almost self-demonstrating artifact — a hallucination-adjacent paper that caught a stale-fact leak inside its own RAG corpus is a gift to the narrative, not just a footnote.
- **The H6 export finding (INT8 losing less than fp32) is clean, well-replicated (3 independent sessions, per-image ONNX/TorchScript diff), and immediately actionable**: "measure the whole exported pipeline before blaming quantization."

## Critical Gaps

- **The paper's crispest new principle is currently undersold.** The four-bucket result plus the fabricated-value finding is treated as a Methodology footnote and a figure caption, not the headline. A reader skimming for "what should I do differently Monday morning" will find it, but only if they read Figure 1's full caption and the formalization prose — it should not require that much excavation.
- **The 0.782-vs-0.719 ambiguity has no assigned home yet** ("MEDIUM-HIGH... not yet disclosed" per the Evidence Gaps table) despite being one of the two or three most exportable findings in the whole project. Structurally it currently rides along inside a Methodology formalization item (#4) and Figure 2's caption, competing for attention with the H6 export table rather than getting its own beat.
- **Eleven roughly-equal-weight goals plus six emergent findings is too flat a structure for a practitioner reader.** Nothing signals, structurally, that G3/EXP03 and the agent negative result matter an order of magnitude more to a practitioner than, say, the twin_bridge mechanism-inventory (G9) or the PSI resampling-seed footnote.
- **twin_bridge (G9) is being given a full, named Results subsection (5.6) for a result that is, honestly, "we wrote unit tests and they mostly pass."** That is legitimate and should be disclosed, but at its current billing it risks reading as padding a section count rather than reporting a finding — practitioners will notice the gap between "named subsection" and "nothing was actually cross-validated live."
- **The Known Limitations list (11 items) and Evidence Gaps table (6 items) have no stated compression order for the writeup**, beyond the general note that practitioner-actionable material is "protected first." Given what actually happened in EXP03/EXP07, that protection order needs to be restated with the *actual* winners named, not the pre-registered H1–H7 winners.

## Specific Suggestions (for the writeup phase)

1. **Promote the EXP03 fabrication finding out of the Methodology footnote and into the opening beat of Results 5.1**, stated in one sentence before the four-bucket percentages: "In two of the eight scenarios where the model's final status agreed with the rule engine, the model's stated reasoning cited a sensor value that does not exist in the input" — lead with the surprise, then give the full distribution.
2. **Give the 0.719-vs-0.782 finding its own short, named callout** (a boxed paragraph or a one-paragraph subsection inside 5.3, not just a figure annotation) with the explicit practitioner rule stated in plain language: "report the metric at your deployed threshold, not your F1-argmax, when the metric feeds a safety decision."
3. **Reframe the "propose/dispose" refrain given what was found.** The data supports a stronger and more specific version: the system is safe not because the LLM's proposals are usually right and occasionally corrected, but because the dominant real pathway is silent/unparseable model output collapsing safely to the rule engine acting alone. State this version explicitly somewhere prominent (ideally the Abstract-adjacent framing) — it is more defensible and more surprising than the version in the current One-Paragraph Pitch.
4. **Use the stale-0.695-in-the-RAG-corpus finding as a narrative device, not just Table 3 row 0.** A single sentence in the Introduction or Discussion — "even this system's own production knowledge base was found, during this audit, to be serving a stale figure it had already corrected elsewhere" — does more rhetorical work for the paper's central hallucination-discipline argument than burying it in a data-integrity table.
5. **Compress twin_bridge (G9) to a short paragraph inside a combined "auxiliary evidence" subsection rather than a standalone numbered Results subsection**, explicitly to make room for the EXP03/EXP07 findings to breathe. State it plainly once ("designed and unit-tested, not exercised live") and move on.
6. **Restate the compression order for Known Limitations/Evidence Gaps explicitly in terms of what was actually found**, not the pre-registered hope: protect (a) the fabrication-inside-agreement finding, (b) the 0.719/0.782 distinction, (c) the agent negative result's replication, and (d) the INT8/export finding; compress or footnote the PSI resampling-seed inconsistency, the precision-rounding inconsistency, and the AQUA-7B step-count reproducibility gap.

## Structural Recommendation

Given what was **actually found** (not the pre-registered hope), main-body vs. appendix should be re-ranked as follows:

**Main body, high priority (promote above their current billing):**
1. **EXP03 four-bucket distribution + fabricated-sensor-value finding (G3)** — this is now THE central result, more valuable to a practitioner than the clean "rule catches miss" framing the proposal was built around. It should open Results and should not require reading a figure caption to find the fabrication finding.
2. **Agent tool-routing negative result, replicated at n=9 (G4)** — keep its protected second-position billing; if anything, foreground the replication ("we tried to break this finding and could not") more than the original proposal does.
3. **The 0.719-vs-0.782 deployed-operating-point disclosure (EF3/G7)** — currently under-billed as an emergent finding; promote to a named callout, not just a figure annotation.
4. **H6 export/INT8 finding (G6)** — keep in main body; it is clean, replicated, and immediately actionable.

**Main body, standard priority (keep roughly as scoped):**
5. RAG asymmetric-threshold calibration (G1/H4) — solid, keep as a subsection, Figure 5 remains optional.
6. G8's corrected PSI-binning mechanism story (quantile more sensitive early, equal-width more explosive late) — keep, but state the corrected finding plainly rather than the originally-hypothesized shape.
7. G5's corrected vision numbers — keep as a caveat sentence beside the headline table (as already planned), not its own subsection; the correction is real but modest.

**Compress toward appendix/footnote (currently over-billed relative to practitioner value):**
- **twin_bridge (G9)** — compress from a full named Results subsection to a short paragraph inside a combined "auxiliary/mechanism evidence" note. The honest content ("unit-tested, not live-exercised") does not carry six new edge-case tests' worth of manuscript real estate.
- Precision 0.858-vs-0.859 rounding inconsistency — footnote only.
- EXP08's internal PSI resampling-seed inconsistency — footnote only, if mentioned at all.
- AQUA-7B format%/step-count reproducibility drift — one footnote where the agent-benchmark table is cited; do not give it independent narrative weight beyond "noted, unexplained, does not change the conclusion."
- The stale-0.695-in-RAG-corpus finding stays in Table 3 for the record, but its *rhetorical* copy (one sentence) belongs in the Introduction/Discussion, not only the appendix-style data-integrity table.

VERDICT: ACCEPT

# Pre-Writeup Council — Narrative Architect (Round 1 of 2)

**Scope:** Evaluating `formalized_results.md`/`.json`, `resource_inventory.tex`, and `vision.md`
against `research_proposal.md`'s Round-3-exit framing, before any manuscript draft exists
(`state.json`: `current_phase: experiment_track`). This is advisory only.

## Assessment

The results are coherent with the proposal, and coherent in the way that actually matters: not
because every hypothesis landed clean, but because the two disclosed complications the proposal
pre-registered as *acceptable failure branches* (H2's non-enumerable-failure-mode limit, H5's
possible qualitative-shape reversal) are exactly the two goals (G3, G8) that came back scoped as
`achieved_minimum`. A council that pre-commits to what an honest miss looks like, and then gets
that miss, has more credibility than one that got everything it hoped for. G5's independent
`achieved_minimum` (dataset leakage, unrelated to any pre-registered hypothesis) is a different
kind of complication — a data-integrity finding, not a hypothesis-scope finding — and it is the one
place a first-time reader could confuse "the proposal predicted this" with "this just happened to
be caught." The writeup needs to keep those two flavors of `achieved_minimum` visibly distinct;
right now `formalized_results.md`'s own "Goal-by-Goal Results" section already does this well
(G3/G8 read as *confirmed scope boundaries*, G5 reads as *audit finding*), and that distinction
must survive into the manuscript's own framing, not get flattened into "three goals hit minimum."

The One-Paragraph Pitch in `research_proposal.md` already anticipates roughly 80% of the real
story — "a simple, fully-tested rule checker reviews everything the AI reports... it can never
lower one" and "in one case they tested giving the AI more independence, it simply failed the
test" both survive intact and are, if anything, *strengthened* by EXP03/EXP04. But the Pitch was
written before EXP03 ran, and it describes the LLM as something whose *status conclusions*
sometimes need correcting. The real finding is scarier and more interesting than that: the LLM's
prose is actively fabricating sensor readings it never received, including in cases where the
final status label is correct. That is not "the checker catches the AI's mistakes" — it is "the
AI's own explanation of *why* cannot be trusted at all, and the checker was never designed to look
at the explanation in the first place." This is a strictly stronger version of the pitch's own
thesis, and the writeup should say so explicitly rather than letting the pitch's pre-EXP03 framing
stand unrevised.

The resource inventory is adequate but thin in exactly one place that matters for this finding:
Figure 1's spec (the four-bucket bar chart) is a status-only visualization, and its own caption
sketch says so ("See Section~X for the fabricated-sensor-value finding, which is invisible to this
status-only bucketing"). That's the right instinct, but it means the paper's single most
narratively interesting result — fabrication *inside a correct answer* — currently has no figure
of its own, only a promised cross-reference and a prose callout. Given the emphasis this review and
the proposal's own H2 formalization place on it, that asymmetry (a whole figure for the boring
"do outputs parse" question, zero dedicated visual for "do the words lie even when the label is
right") is worth a deliberate resourcing decision at the writeup stage — even a simple annotated
table (scenario ID, final status, agreement bucket, fabrication-detected Y/N) would fix this more
cheaply than a new figure.

## Narrative Arc Analysis

The original proposal's arc is: *we built four probabilistic surfaces, we refused to trust any of
them with final authority, here is what that discipline cost and bought us.* That arc still holds
and does not need replacing. But the real data supports a sharper one-sentence version of it that
the writeup should adopt as the spine, not just a supporting detail:

> **The backstop isn't validated by catching wrong answers — it's validated by not needing the
> reasoning to be true at all.**

This reframes G3 as the paper's central empirical result (which `resource_inventory.tex` already
flags Figure 1 as, "THE central empirical result") in a way that upgrades rather than just restates
the proposal's H2. The proposal's H2 says the mechanism "does not extend to non-enumerable failure
modes" — true, but stated as a *limitation*. The sharper framing says: the dominant observed
pathway (50% unparseable-defaulted-to-ok) plus the fabrication finding (6/8 scenarios, including
2 inside the "agrees" bucket) together show that the architecture's actual safety property never
depended on the LLM's reasoning being sound — only on its final status label being extractable, and
when it isn't extractable, on defaulting safe. That is a *stronger*, more defensible claim than
"sophisticated correction happens sometimes," and it is also more publishable, because it is the
kind of finding a skeptical reviewer cannot easily poke a hole in by asking "but what if the model
gets smarter" — the architecture's safety property is explicitly independent of the model's
reasoning quality. The writeup should state this as the paper's thesis sentence, not bury it as an
emergent finding six items down a list.

A secondary arc worth naming explicitly in the Discussion: three of the six emergent findings
(fabricated sensor values, the RAG 0.695 leak, the AQUA-7B format drift) are all instances of the
same underlying phenomenon — a probabilistic or human-authored artifact silently degrading between
"measured once" and "used continuously in production" — while the other three (0.719-vs-0.782,
sparse-frame gap, INT8 counter-intuitive result) are all instances of "the headline number and the
operationally relevant number are different numbers." Grouping the six this way (two families, not
one flat list of six) would give the Discussion a organizing structure that the current flat
enumeration in `formalized_results.md` doesn't provide, and would make the paper's contribution
read as a *methodology* (measure continuously; distinguish the headline number from the operating
number) rather than a grab-bag of six unrelated gotchas.

## Folklore Engagement

The proposal explicitly targets two folklore claims: "more LLM autonomy is more capability" (H3)
and "quantization is where you pay for edge speed" (H6). Both are engaged well by the formalized
results and neither needs rework. But the emergent findings surface at least two *more* folklore
targets that the proposal's deferred folklore list (automation/safety tradeoff, RAG benchmark
scores, drift-implies-retrain, self-agreeing harness) doesn't quite capture, and the writeup should
consider naming them explicitly rather than leaving them implicit:

- **"A model that gives the right answer got the right answer."** EXP03's 2 fabrication-inside-
  agreement cases directly falsify this for free-text LLM reasoning under status-only grading —
  worth a named sentence, since it's a broader and more quotable claim than "hallucination exists,"
  and it's exactly the kind of folklore a status-only eval (the kind most benchmark papers run)
  would never surface.
- **"A production RAG system's accuracy is whatever its retrieval eval says."** The live 0.695 leak
  shows the corpus itself can silently carry a stale ground-truth claim that no retrieval-quality
  metric would ever catch (it's a content problem, not a retrieval problem) — this is a distinct
  folklore target from the four already deferred to lit review, and it's evidenced by this
  project's own artifact, not by citation, so it belongs in this paper rather than being deferred
  again.

## Precision Check

Four places where the writeup will be tempted to smooth a complication into a cleaner sentence
than the evidence supports:

1. **G3's 38% "parseable-and-agrees" bucket.** It will be very tempting to write "the model agreed
   with the rule engine in 38% of scenarios" as if that's a competence data point. It is not, per
   this audit's own math: 2 of those 3 agreeing cases contain fabricated sensor values in the
   reasoning field. The honest sentence is "the model reached the correct status label in 3/8
   cases, but its stated reasoning was fabricated in at least 2 of those 3" — a materially
   different claim, and the one the manuscript must use. Any table or figure that reports the
   38%/50%/12%/0% split without an adjacent fabrication-rate annotation is, by omission,
   overstating the "agrees" bucket's evidentiary value.
2. **G5's "resolved" language.** `formalized_results.md` correctly labels this an
   `achieved_minimum` "upgraded by this audit," but the phrase "resolved" in the section header
   ("G5 Resolution") risks reading, to a skimming reader or a co-author doing a final pass, as "the
   leakage problem is fixed." It is not — the flagged near-duplicate frames remain in the training
   set that produced the deployed checkpoint; only the *bias estimate* is resolved, not the
   leakage. The manuscript must never use "corrected vision numbers" as a standalone phrase without
   the adjacent "same-checkpoint re-evaluation, not a leakage-free retrain" caveat every single time
   the corrected P/R/mAP50 range is cited — not just once in a footnote.
3. **G8's "corrected, not confirmed" finding.** The literal reversal of H5's wording (quantile
   *more* sensitive at low δ, equal-width overtaking only at δ≥0.08) is mechanistically interesting
   and honestly reported in `formalized_results.md`. The risk is a copy-edit pass later compressing
   "H5 predicted X, we found the opposite of X at low severity and X only at high severity" down to
   "H5 was confirmed" for narrative convenience, because "PSI binning matters, use quantile" is the
   simpler sentence. It is also the wrong sentence — the paper's actual, more interesting
   contribution here is the crossover and its mechanism (one large equal-width bin emptying), not a
   confirmed monotonic claim. Any Abstract or Conclusion sentence about H5 must be checked against
   this specific risk.
4. **0.719 vs. 0.782 recall.** The Evidence Gaps table already flags this as MEDIUM-HIGH priority
   with required disambiguating language "wherever H7's safety discussion cites recall." The
   precision risk is narrower than "will this be disclosed" (it clearly will be) — it's whether the
   Abstract, which typically gets written and then frozen before the rest of the paper is finished,
   ends up citing only 0.719 (because that's the number in `vision.md`'s locked non-negotiable
   framing) while the body correctly uses 0.782 for the safety argument. That specific
   Abstract-vs-body split is the likeliest place this ambiguity leaks through unresolved, precisely
   because the Abstract is drafted from `vision.md`'s verbatim-required figures, not from
   `formalized_results.md`'s more complete picture.

## Missing "So What?"

Checking each emergent finding for a takeaway a reader would actually remember:

1. **Fabricated sensor values.** Clear and strong: *a correct answer is not evidence the model's
   reasoning was sound; only the status-extraction-plus-override architecture, not the model's
   narrative, is what's actually being trusted.* This is memorable and already load-bearing for the
   sharpened thesis above.
2. **Live 0.695 RAG leak.** Clear and strong, and unusually concrete for a "so what": *a paper can
   correct its own headline number and still ship the old number into production if the fix doesn't
   propagate to every ingested artifact* — a genuinely useful, transferable lesson about
   documentation-as-data pipelines, not just a fun bug.
3. **0.719 vs. 0.782.** The takeaway exists in the source material ("0.782...is the one that should
   govern the H7 safety discussion") but is not yet crisp enough to survive compression. Recommend
   sharpening to something quotable like: *the number a paper reports and the number a system
   actually runs on are not automatically the same number, and only one of them is the safety-
   relevant one.* Right now this reads as a rounding footnote; it should read as a methodological
   warning.
4. **Zero sparse-frame coverage.** Currently framed as "a gap, not a finding" — accurate, but risks
   landing as a shrug ("we don't know"). The so-what needs an explicit direction: *the reassuring
   0/98 full-frame-miss result is conditional on a val-set property (no sparse-fish frames) that was
   never designed in, meaning the safety claim's confidence interval is narrower than the headline
   number implies, specifically at the regime (low fish count) most likely to matter for a welfare
   check.* State the conditional explicitly or the finding reads as inconclusive filler.
5. **AQUA-7B format drift.** Currently a shrug ("no configuration difference found") — this is the
   weakest so-what of the six as written. Recommend the writeup commit to a stance rather than
   leaving it as an open mystery: even unexplained, the drift's own existence is the finding —
   *identical code, different measured behavior a few days apart, with no diff to point to, is
   itself evidence that "reproducible" claims about locally-hosted LLM stacks need a stated
   measurement date, not just a stated commit hash.* That's a usable methodological point even
   without knowing the root cause.
6. **INT8 counter-intuitive result.** Clear and strong, and already correctly framed in both
   `formalized_results.md` and the H6 formalization: *the loss is in the export/NMS path, not the
   numeric precision, so "quantize less aggressively" would not have bought back the accuracy this
   system is actually losing.* This is the one emergent finding that most directly falsifies a
   named folklore item and should be showcased, not buried in Table 1.

## Verdict

The results support a genuinely sharper story than the pre-registered proposal anticipated, the
council's own honest-failure-branch discipline (G3/G8) paid off narratively, and every emergent
finding has a recoverable so-what — none require new data, only sharper sentences at the writeup
stage. The identified risks (G3's agree-bucket, G5's "resolved" language, G8's crossover-not-
confirmation, and the Abstract-vs-body 0.719/0.782 split) are all writeup-craft risks, not
evidentiary gaps, and are exactly the kind of thing a Narrative Architect pass should flag before
drafting rather than after.

VERDICT: ACCEPT

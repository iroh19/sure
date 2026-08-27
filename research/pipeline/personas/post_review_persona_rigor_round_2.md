# Post-Review Assessment — Rigor & Novelty Persona (Round 2 of 2, FINAL)

**Scope:** Final read-through of `final_paper.tex` and every `sections/*.tex` it inputs (abstract,
introduction, related_work, background, system_architecture, experimental_setup, results,
discussion, known_limitations, conclusion, appendix), cross-checked against Round 1's findings
(`post_review_persona_rigor_round_1.md`, ACCEPT, one non-blocking item flagged). This round's
specific mandate: find anything that would flip the verdict to REJECT, with particular attention to
whether any claim anywhere — not just Abstract/Intro/Conclusion — lets $n=8$/$n=9$/$n=98$ support
more than it should, or lets a "may"/"suggests" harden into a "proves"/"shows conclusively."

## Targeted re-check: does any claim overstate what n=8/n=9/n=98 supports?

I re-traced every quantitative claim built on each of the paper's three small samples, in every
section, not only the ones a first pass would remember to check:

- **n=8 (EXP02/EXP03, dual-layer decision system).** Every invocation — Abstract ("one case in
  eight"), Introduction ("half the time... only one of eight"), Results §5.1 (explicit "$n=8$, the
  entire fixed scenario population; no confidence interval is implied," repeated in the
  Figure~1 caption), Discussion ("12\% of what actually happens," immediately contextualized as
  restating an already-scoped Results number), Known Limitations (a dedicated paragraph titled
  "Sample size of the central result" stating the census-not-sample framing explicitly), Conclusion
  ("half of the eight exercised scenarios"), and Appendix (the full 8-row per-scenario table) — is
  either a raw count, an explicit fraction-of-eight, or paired with the no-CI disclaimer. I found no
  new location this round where a percentage floats free of its $n=8$ tag.
- **n=9 (EXP04, agentic tool-routing).** Results §5.2 states "$n=9$ total" and "9 genuinely
  independent scenarios" for the constant-answer finding, and is explicit that the interesting
  claim is qualitative (constant-answer artifact) rather than a rate: "This is a constant answer,
  not evidence of discrimination between scenarios." The one place a raw percentage appears (50\%
  to 71.4\%) is immediately deflated in the same sentence as "an artifact of three of the four new
  scenarios happening to be sensor-trend-relevant by design," and the Appendix repeats this same
  deflation almost verbatim. Discussion explicitly refuses to extrapolate to a capability threshold
  ("neither result licenses a claim about where on the capability curve a model would need to sit").
  No overreach found.
- **n=98 (EXP06/EXP07, vision).** Every mAP50/precision/recall figure in Results §5.3, the
  headline-metrics table, and both vision figure captions is explicitly scoped to "$n=98$ images,
  single device," and the paper goes further than the minimum bar by naming the coverage gap this
  sample can't speak to (zero $k=1$/$k=2$ frames) in three separate places (Results, Discussion,
  Known Limitations) and by explicitly labeling the 22–28\% sparse-frame extrapolation as "untested
  extrapolation... not a measurement," each time it appears. This is the one place a paper could
  easily have let a reassuring 0/98 result imply more than it earns, and it consistently does not.

I also checked the two smaller sample counts that don't appear in the round's literal prompt but sit
next to the three above and are the same kind of risk: the RAG evaluation ($n=29$ queries / 44
chunks — Results §5.4, Figure caption, both explicit) and the PSI sweep ($n=1467$ per window,
16 points — Results §5.5, Appendix table, both explicit, and the paper's own footnote flags an
internal reproducibility wrinkle in that data rather than hiding it). Same discipline holds.

## Targeted re-check: has any "may"/"suggests" hardened into "proves"/"shows conclusively"?

A full-manuscript grep for `prove(s)?`, `conclusively`, `definitively`, `establishe(s|d)`,
`guarantee(s)?`, `always`, `never`, `certainly`, `shows that`, and `demonstrates that` turns up
nothing that applies an absolute verb to a statistical claim. Every hit resolves to one of three
safe categories: (1) a code-level invariant that is categorically, not statistically, true by
inspection of the source — e.g. `apply_rule_override` "never" reads the `reasoning` field, the
override is "escalate-only, never downgrade" (System Architecture, Background) — these are claims
about what a specific function does or doesn't read, verifiable by reading the function, not
inferences from a sample; (2) an explicit self-negation — Formalization 1 is introduced with "This
is not a proved theorem," and Related Work states "None of this establishes novelty" before
explaining what it does establish; (3) a hedge that was already conservative going in and stays
that way — "tool-selection reliability has not been established" (System Architecture), "these
results suggest, but do not demonstrate beyond this one system" (Discussion's "hedged conjecture"
subsection, which is the paper's one explicit generalization claim and is the most carefully hedged
paragraph in the entire manuscript). I found zero instances of a Results-section "suggests" being
restated as a Discussion- or Conclusion-section "proves," in either direction of the paper.

The one arguable near-miss, and it is the same one Round 1 flagged and it has not moved: Results
§5.1 calls the EXP02 module-identity check a "structural guarantee." I re-examined this specifically
because "guarantee" is exactly the kind of word this check is designed to catch. It survives
scrutiny — the claim is a Python `is`-identity check between two code paths, a categorical fact
about the codebase (either the harness and production resolve to the same object or they don't),
not a statistical inference from a sample size, and the sentence immediately narrows what the
guarantee does and doesn't cover ("only tells us the two paths compute the *same* severity given
the same inputs. It says nothing about what AQUA-1B's actual output looks like"). This is a correct
use of "guarantee," not statistical overreach wearing a stronger word.

## Anything new since Round 1 that would justify REJECT?

No. I re-verified Round 1's two non-blocking items are unchanged and not escalated:

1. The Abstract's closing sentence still doesn't pre-empt a reader conflating "safe against
   enumerable errors" with "safe against fabricated reasoning" — still true, still minor, still
   not a factual error (Formalization 2 and the EF1 fabrication finding police this distinction
   correctly everywhere it matters).
2. The live 0.695 RAG knowledge-base figure is still disclosed as unfixed (Known Limitations,
   Introduction, Results §5.6) rather than silently resolved or dropped between rounds — consistent
   handling, not a new problem.

I looked for, and did not find, any new claim introduced or altered between the two rounds that
would change this assessment — the sections read as textually identical to Round 1's pass on every
point this round re-checked line by line (abstract, results, discussion, known_limitations,
conclusion, appendix, plus the formalizations in system_architecture and the novelty framing in
related_work).

## Assessment

Nothing in this final read rises to a REJECT-level concern. The paper's defining discipline — every
small-$n$ claim travels with either its denominator, its no-CI disclaimer, or both, in every section
it appears, not only the ones under a reviewer's spotlight — holds under this round's adversarial
re-check as much as it held under Round 1's. The two items worth naming are the same two Round 1
already named as non-blocking, and neither has grown teeth on a second look. This is a paper that is
unusually careful about the exact failure mode this round was tasked with hunting for.

## Verdict

VERDICT: ACCEPT

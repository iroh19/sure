# Pre-Writeup Council — Practical Compass — Round 2 (Final)

**Mandate:** Timely & compelling for practice.
**Inputs read (this round):** `pre_writeup_persona_practical_round_1.md` (own prior),
`pre_writeup_persona_rigor_round_1.md`, `pre_writeup_persona_narrative_round_1.md`,
spot-checks against `formalized_results.md` and `resource_inventory.tex` to confirm no
underlying artifact changed since Round 1 (file mtimes precede all three Round 1 reviews —
this is a synthesis round on fixed evidence, not a re-audit).

## Assessment (updated)

Rigor's adapter-provenance finding does not perturb my Round 1 Structural Recommendation —
it validates and sharpens the single decision that recommendation was already built around
(promote EXP03/G3 to the lead), and it closes a loose end (an "unresolvable" limitation that
was actually resolvable for free) that was making the Known Limitations list flabbier than it
needed to be. I am not restructuring the billing order. I am strengthening the wording of the
#1 item and, for the first time, flagging a genuine framing risk that a well-meaning writeup
could introduce while trying to use this finding.

The practitioner logic, worked through explicitly: my Round 1 promotion of EXP03 rested on the
claim "architect your safety net assuming the model frequently produces nothing usable, not
assuming it usually works." That claim was already true and already strong with an
unspecified-quality adapter. It becomes a *categorically stronger* claim once the adapter's
own training pipeline is on record calling it insufficient ("el yazımı 8 örnek, yetersiz,
sadece duman testi" — 8 handwritten examples, insufficient, smoke-test only). The objection
a skeptical practitioner reader would otherwise have — "sure, but surely a properly-tuned
model wouldn't behave this badly, so how much of this generalizes to my (better-tuned) system?"
— is now pre-empted by the paper's own evidence rather than left as an unaddressed gap. The
architecture wasn't merely tested against an LLM component; it was tested against the worst
plausible version of that component that the codebase itself ships, and the safety property
held regardless. That is a more exportable, more defensible, harder-to-dismiss version of the
same practitioner rule I promoted in Round 1, not a different rule.

This also mechanically tidies the practitioner-readability problem I raised in Round 1 item 4
(the flat eleven-goal, six-emergent-finding structure). "Adapter provenance: unresolvable,
mtime-only" was one of the more prominent unresolved items competing for space in Known
Limitations. It is now a one-paragraph disclosed fact, not an open question — one fewer
un-closed loop for a practitioner reader to weigh, and it converts from a limitation into
evidence *for* the central claim. Net effect on manuscript real estate: negative (it shrinks
the limitations list) while the payload it delivers to the headline finding is positive. That
is a rare, clean trade in a pre-writeup review and the writeup should take it.

## Still-valid vs. resolved concerns from Round 1

**Resolved:**
- The adapter-provenance item that Round 1 implicitly treated as one more entry in the
  unwieldy Known Limitations pile is now a disclosed, favorable fact (per Rigor). This
  directly serves Round 1 Suggestion #6 (restate the compression order using actual
  winners) — one fewer item to triage, and it moves into the "protect" column rather than
  the "footnote" column, since it now *supports* the G3 headline rather than merely being an
  honesty checkbox.

**Still valid, unchanged:**
- The EXP03 fabrication finding is still sitting in a Methodology footnote and a figure
  caption rather than being the opening beat of Results — nothing in either other persona's
  Round 1 review reports this having moved, and no artifact timestamp shows post-Round-1
  edits. Suggestion #1 stands, now with slightly higher stakes (see below).
- The 0.719-vs-0.782 deployed-operating-point disclosure still has no assigned structural
  home ("not yet disclosed" per the Evidence Gaps table as of the files I re-checked).
  Suggestion #2 stands unchanged.
- twin_bridge (G9) is still scoped as a full named Results subsection (5.6) for content that
  is, on the record, "18 test cases pass, unit-tested, never exercised live." Suggestion #5
  (compress to a paragraph inside an auxiliary-evidence subsection) stands, and if anything
  the case for it is slightly stronger now: the adapter-provenance paragraph needs a small
  amount of the same real estate the G9 subsection is currently occupying, and G9 is the
  cheaper thing to compress of the two.
- The flat eleven-goal structure and the uncompressed Known Limitations/Evidence Gaps lists
  are still the main practitioner-readability risk. Suggestion #6's compression order is
  still the right instrument; it just gets one line easier to execute (see Resolved, above).

## New concerns

1. **Framing risk introduced by the adapter finding itself.** There is a plausible-sounding
   but wrong way to write this up: "the LLM component was undertrained, so this result is a
   strawman / doesn't tell us much." A drafter under space pressure, looking for a tidy
   caveat sentence, could reach for exactly that phrasing because it sounds appropriately
   humble. It is the wrong sentence and it would gut the paper's strongest practitioner
   point. The correct framing — which the writeup needs to commit to explicitly, not leave
   to a copy-edit pass — is the inverse: *because* the adapter is self-documented as
   inadequate, the fact that the system's safety property never depended on it is stronger
   evidence for the architecture, not weaker evidence for the study. This needs one
   explicit sentence in the manuscript stating the direction of the inference, not just the
   fact of the adapter's provenance.
2. **Untested generalization edge should be named once, plainly, and then closed.** A
   practitioner reader will immediately ask "what happens with the 128-sample v2 adapter?"
   The honest answer is "unknown, future work" — that is fine, but it needs to be a single
   explicit sentence in Discussion/Limitations, not silence. Recommend: "Whether a
   better-tuned adapter would reduce the 50% unparseable rate is untested; what would not
   change is the architecture's independence from the model's free-text reasoning, since the
   rule engine never reads it regardless of adapter quality." That sentence also does double
   duty reinforcing Narrative's proposed thesis (safety comes from reading only the
   enumerable field) — Practical and Narrative converge on the same sentence doing two jobs,
   which is an efficient use of scarce main-body space.
3. **Placement, not new content.** The adapter-provenance paragraph should not become its
   own subsection or callout box — that would repeat the exact over-structuring mistake I
   flagged for twin_bridge in Round 1. It belongs as a two-to-three-sentence addition
   *inside* the same Results 5.1 opening beat that Suggestion #1 already promotes the
   fabrication finding into, immediately after the "in two of eight scenarios the model
   cited a sensor value that does not exist" sentence. One combined headline beat, not two
   separate ones competing for the reader's attention.

## Updated Structural Recommendation

Unchanged in ranking from Round 1, with one content addition to the #1 item and no other
reordering:

**Main body, high priority (promote above original billing):**
1. **EXP03 four-bucket distribution + fabricated-sensor-value finding, now with adapter
   provenance folded in (G3)** — still THE central result and still opens Results. Add to
   the existing Round 1 wording: after stating the fabrication finding, add the one-sentence
   disclosure that the deployed adapter is the 8-example smoke-test dataset its own training
   pipeline calls insufficient, followed immediately by the explicit direction-of-inference
   sentence ("this makes the architecture's safety property stronger evidence, not weaker,
   since it was demonstrated against a self-documented-inadequate model component"). This is
   an addition to Suggestion #1's existing text, not a new subsection.
2. **Agent tool-routing negative result, replicated at n=9 (G4)** — unchanged from Round 1.
3. **The 0.719-vs-0.782 deployed-operating-point disclosure (EF3/G7)** — unchanged from
   Round 1; still needs its named callout.
4. **H6 export/INT8 finding (G6)** — unchanged from Round 1.

**Main body, standard priority:** unchanged from Round 1 (RAG asymmetric-threshold
calibration, G8's corrected PSI-binning story, G5's corrected vision numbers as a caveat
sentence).

**Compress toward appendix/footnote:** unchanged from Round 1, with the adapter-provenance
item now removed from this list entirely (it graduates to the #1 item's content, per above,
rather than sitting here as a limitations footnote). twin_bridge (G9), the 0.858/0.859
rounding inconsistency, the PSI resampling-seed inconsistency, and the AQUA-7B drift footnote
all remain as scoped in Round 1 — if anything, G9's compression is now marginally more
important, since the #1 item's beat has grown by two sentences and something has to make
room.

## Verdict

The Rigor finding is good news that requires careful handling, not restructuring. It
strengthens the practitioner takeaway I already promoted to the top of the manuscript in
Round 1 ("an inadequately-tuned local LLM is safe to deploy if the safety-critical decision
reads only an enumerable field" is indeed a stronger, more falsifiable claim than the
well-tuned-model version would have been), it shrinks rather than grows the Known
Limitations burden, and it converges cleanly with Narrative's proposed thesis sentence about
reading only the status field. The one real risk is a framing mistake at the writeup stage
(reaching for "undertrained, so discount this result" instead of "undertrained, so this
result is stronger") — that risk is now flagged explicitly and should be treated as a
required editorial check before freeze, alongside the 0.719/0.782 Abstract-vs-body check
Narrative already flagged.

VERDICT: ACCEPT

# Pre-Writeup Council — Narrative Architect (Round 2 of 2, FINAL)

**Scope:** Re-evaluating the Round 1 narrative assessment in light of Practical's billing
promotions (EXP03 fabrication + 0.719-vs-0.782 to lead position) and Rigor's new finding that the
deployed AQUA-1B adapter is the 8-record smoke-test artifact (`sure_finetune_data.jsonl`, self-
described by `finetune.py` as "yetersiz, sadece duman testi" — insufficient, smoke-test only), not
the 128-example v2. This is advisory only; final round.

## Assessment (updated)

Rigor's adapter-provenance finding does not complicate the story I proposed in Round 1 — it
completes it, and it closes the one gap Round 1 left open. My Round 1 sharper thesis was: *the
backstop's safety property never depended on the LLM's reasoning being sound, only on the status
label being extractable and defaulting safe when it isn't.* That thesis was already fully supported
by the fabrication-inside-agreement data (6/8 reasoning strings inaccurate, 2 of 3 "agrees" cases
included). What it lacked was an answer to the obvious skeptical follow-up: *sure, but maybe a
better-trained model wouldn't fabricate as much — so how strong is this claim really?* Round 1 had
no good answer to that beyond "future work." Rigor's finding **is** the answer: the model that
produced this evidence was not a fairly-tuned model that happened to fail, it was an
under-provisioned, self-documented-as-inadequate 8-example adapter. That reframes the entire
experiment from "we tested the architecture against a model" to "we tested the architecture against
close to the worst plausible model on the shelf, and it still held." The skeptical follow-up is now
answered *inside the paper*, not deferred to future work — which is a materially stronger position
to publish from.

This also resolves the tension I flagged in Round 1 between the "propose/dispose" framing and the
harsher EXP03 data: the reason the LLM's contribution reads as "triggerable, ignorable severity-
format emitter" (Rigor's Round 1 phrase) rather than "occasionally-useful advisor" is now
explicable, not just observable. It is not a mysterious property of small on-device LLMs in this
role in general — it is a directly attributable property of shipping a smoke-test-scale adapter to
production evaluation. That distinction matters enormously for how reviewers will read the paper's
generalizability claims, and it is a distinction the paper can now make explicitly instead of
leaving implicit.

## Still-valid vs. resolved concerns from Round 1

**Resolved / strengthened by Rigor's finding:**
- The tension between "the architecture is vindicated" and "the model component's usefulness is
  unclear" (my Round 1 note on the pitch needing revision) is resolved: the model's poor showing is
  now attributable to a specific, checkable provenance fact rather than left as an unexplained
  weakness in the LLM layer generically. This makes the paper's honesty read as *diagnosis*, not
  *shrug*.
- The Folklore Engagement item "a model that gives the right answer got the right answer" (Round 1)
  is now falsified by an even more startling instance: the model was not just imperfect, it was
  running on 1/16th of its own documented minimum viable training set, and *still* produced
  fabrications precise enough to be graded "agrees" by a status-only check. That is a better,
  scarier version of the same folklore target and should replace the softer framing in the writeup.

**Still fully valid, unchanged by this finding:**
- G3's 38% agree-bucket precision risk (Precision Check #1) — still the single most tempting
  place for the manuscript to smooth a complication into a cleaner sentence than the evidence
  supports. If anything, this risk is now *higher* stakes: "the model agreed 38% of the time" read
  next to an undisclosed adapter provenance would look like an indictment of small LLMs generally;
  read next to the disclosed provenance, it correctly narrows to an indictment of this one
  under-trained checkpoint. The manuscript must carry both facts in the same breath or the finding
  will be misread in the more damaging direction (against the field) rather than the more precise
  one (against this specific artifact).
- G5's "resolved" language caveat (Precision Check #2) — untouched by this finding, still needs
  enforcement.
- G8's crossover-not-confirmation caveat (Precision Check #3) — untouched, still needs enforcement.
- The 0.719-vs-0.782 Abstract-vs-body split risk (Precision Check #4) — untouched by this finding;
  Practical's Round 1 promotion of this to a named callout is independently correct and should
  proceed regardless of the adapter finding.
- Figure 1's status-only blind spot to the fabrication finding (Round 1's resourcing note) — still
  needs the annotated table or dedicated figure; if anything, now needs a third column noting
  adapter identity, since "fabrication rate" and "which adapter produced it" are now both
  first-class facts the figure's caption must carry.

**New concern surfaced by re-reading, not present in Round 1:**
- The manuscript needs one explicit, early sentence establishing *when* the reader learns the
  adapter is the smoke-test v1, not the documented-default v2. If this fact arrives only in
  Discussion or a footnote after Results has already narrated the 50%-unparseable/6-of-8-fabricated
  findings, a reader will form the (wrong, more damaging) impression that this is a claim about
  small on-device LLMs generally before being corrected. The provenance fact should be disclosed at
  first mention of the adapter/model in Methods, not held for a caveat later — sequencing risk, not
  a content risk, but a real one given how compression usually happens under space pressure.

## Updated Narrative Arc (final recommended framing for the writeup)

Keep the Round 1 thesis sentence as the spine, but extend it with the adapter fact as its second
half — the two clauses now form a single, tighter argument rather than a thesis plus a caveat:

> **The backstop's safety property never depended on the LLM's reasoning being sound, only on the
> status label being extractable and defaulting safe when it isn't — and this was demonstrated
> against a model given close to no fair chance to reason well in the first place, which makes the
> demonstration a stress-test of the architecture, not a character reference for the model.**

Recommend the writeup state the second clause explicitly and early, using close to the Round 1
phrasing suggested in this council's brief: *"we did not give the LLM a fair chance, and the
architecture still held."* This sentence does real work for three separate audiences at once:

1. **For the skeptical reviewer** ("but a better model would fix this"): the paper preempts the
   objection by showing it already knows the model was underpowered and is making a point that is
   robust to that fact, not blind to it — a stress-test framing survives the "just use a better
   model" objection that a "here's an interesting failure we can't explain" framing would not.
2. **For the practitioner reader** (Practical's audience): it sharpens the actionable takeaway from
   "small LLMs may hallucinate, design around it" (generic, already-known advice) to "verify what
   you actually shipped before you draw conclusions about what a component class can do" — a more
   specific, more exportable methodological point about auditing your own deployed artifacts.
3. **For the paper's own honesty argument** (the thread Practical's Round 1 review calls "citation-
   bait for anyone building LLM-plus-validator pipelines" and this review's Round 1 called the
   architecture's real thesis): a system whose central hallucination-discipline claim was
   nearly undermined by an unaudited adapter path, caught by the same kind of internal audit
   discipline that caught the 0.695 RAG leak, is a paper practicing its own thesis at the meta
   level. That parallel (self-audit catches a stale RAG figure; self-audit catches a
   mis-provenanced adapter) is worth one explicit sentence in the Discussion tying the two
   self-audit findings together as the same phenomenon at two different layers of the stack.

This does not replace the two-family Discussion structure I proposed in Round 1 (measurement-decay
findings vs. headline-vs-operating-number findings) — it adds the adapter-provenance finding as a
clean third instance of the *first* family (fabricated sensor values / 0.695 RAG leak / AQUA-7B
format drift / now: undisclosed adapter identity are all cases of "an artifact silently drifted or
was mis-identified between being produced and being used to draw a conclusion"). Recommend making
that a family of **four**, not three, in the final Discussion structure.

## New concerns

Beyond the sequencing risk noted above, one additional item: the Round 1 "Missing So-What" analysis
for the fabricated-sensor-values finding should be extended by one clause. The original so-what
("a correct answer is not evidence the model's reasoning was sound") is still correct but now
incomplete on its own — it should read: *a correct answer is not evidence the model's reasoning was
sound, and this was true even before considering that the model itself was operating with a
fraction of its intended training data; only the status-extraction-plus-override architecture, not
the model's narrative, is what's actually being trusted.* This is a wording fix, not a new gap, and
does not change the verdict.

No finding from this round, Practical's Round 1 review, or Rigor's Round 1 review introduces
anything that undermines the architecture claim, contradicts a previously verified number, or
requires new data collection. Every open item remaining across all three personas at this point is
a disclosure-sequencing or billing decision to be made during drafting, not an evidentiary gap. The
story is ready to write.

## Narrative Continuity — final assessment

Nothing in the current set of findings would make me reject the writeup direction. If anything, the
Rigor finding removes what was, going into this round, the single largest latent risk to the
narrative's durability: an unexamined "why does the model do so poorly" question that a hostile
reviewer could have used to reframe the whole paper as "an interesting anecdote about one weak
model" rather than "a validated architectural pattern." That question now has an on-the-record,
cheaply-verified answer, and the answer makes the paper's central claim stronger. The story is fully
ready to write, provided the writeup enforces (a) early, plain disclosure of adapter provenance at
first mention rather than as a late caveat, and (b) the four Precision Check items from Round 1,
none of which this round's new finding weakens or removes.

VERDICT: ACCEPT

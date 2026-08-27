# Rigor & Novelty — Pre-Writeup Council, Round 2 (Final)

**Reviewer posture:** skepticism by default. **Scope:** re-read `pre_writeup_persona_rigor_round_1.md`
against the current state of `formalized_results.md`/`.json`, `resource_inventory.tex`, and
`vision.md`; cross-checked Narrative's four flagged "smoothing" risks against
`experiment_workspace/experiment_runs/EXP03/results.md` and `EXP04/results.md` directly; and
independently re-derived the LoRA adapter provenance claim from the raw files on disk (record
counts, mtimes, `docker-compose.yml`, `inference.py`'s env-var resolution) rather than trusting
Round 1's own arithmetic. No code was executed against `sure-project`; every check below is a file
read, `grep`, `wc`, `stat`, or a trivial line-count script — no `model.val()`, no training, no
writes anywhere under `sure-project`.

## Assessment (updated)

Nothing has moved since Round 1 in a way that weakens the central claim, and one thing I flagged as
"resolved during this review" in Round 1 (adapter provenance) has **not actually been written back
into the paper trail** — it is still sitting as an open action item, not yet a correction. That is
the one concrete state change this round needs to register: Round 1 said "this should be corrected
before freeze, not carried forward as an open limitation," and as of this pass it has been carried
forward unchanged. `formalized_results.json`'s G3 `gaps[1]` still reads verbatim: *"Adapter
provenance ... is mtime-only; the adapter directory is gitignored, so no commit-hash provenance is
possible"* — the same framing Round 1 argued understates what's cheaply checkable. `EXP03/results.md`
line 76 still logs the same "mtime-only" characterization with no record-count cross-check appended
anywhere in that file. This is not a new problem and not a validity defect — it's a Round 1
recommendation that hasn't yet been actioned, which the writeup-freeze gate should catch before it
becomes a missed correction rather than a pending one.

I re-derived the adapter finding independently rather than re-reading Round 1's numbers, and it
holds up and actually strengthens on a detail Round 1 didn't check: **mtimes show the 128-example
`sure_finetune_data_v2.jsonl` already existed (Jun 5 00:06:33) before the deployed adapter's
`_mlx_data/{train,valid}.jsonl` were written (Jun 5 00:42:58)**. That rules out the innocent
explanation "v2 didn't exist yet when the adapter was trained" — v2 was available and was not used.
The training-data folder behind the live `adapters.safetensors` (mtime 00:43:26) contains exactly 7
train + 1 valid records, matching `sure_finetune_data.jsonl`'s 8 lines record-for-record, and
`finetune.py`'s own docstring (lines 12–16) calls that exact file "el yazımı 8 örnek (yetersiz,
sadece duman testi)" — "8 handwritten examples, insufficient, smoke-test only" — while stating "8
örnek underfitting üretir" (8 examples produces underfitting) as the reason v2 is the documented
default. `EXP03/results.md` line 10 independently confirms via `docker-compose.yml` and a
`grep -rn test-adapter` sweep that `sure-aqua-adapter` (not `sure-aqua-adapter-test` or the separate
`test-adapter/` directory) is the one path wired to `AQUA_ADAPTER_PATH` in the deployed
configuration, and line 5 confirms EXP03 itself ran with that exact path exported. So the chain is:
deployed config → `sure-aqua-adapter` → its `_mlx_data` → 8 records → same file the project's own
training script calls insufficient, and v2 was sitting on disk, unused, the whole time. This is now
a record-count-plus-mtime-ordering argument, not record-count alone, and it is stronger than what I
wrote in Round 1.

## Still-valid vs. resolved concerns from Round 1

**Resolved / no longer a concern:**
- Logical Gap #4 (Abstract/Conclusion hedge-erosion risk) — no manuscript draft exists yet
  (`state.json: current_phase: experiment_track`), so there is nothing to check yet; this remains a
  standing writeup-stage risk to watch, not a currently-existing defect, and I have no new
  information changing that status either direction.
- Novelty Analysis items (interface-design framing, EXP04/EXP06 methodology contributions, C2's
  correctly-open status) — unchanged, still hold, no new evidence surfaced against them this round.

**Still valid, unchanged:**
- Logical Gap #1 ("override" language risk) and #2 (the "agrees" bucket's epistemic cleanliness) —
  both re-verified directly against `EXP03/results.md`'s raw scenario table this round (T01/T05/T08
  are the three "agrees" cases; T05 and T08 are independently marked "inaccurate, right label" at
  lines 58 and 61, T01 "accurate" at line 54). The underlying data hasn't changed; the writeup still
  hasn't been written, so the risk these gaps describe is exactly as live as it was in Round 1.
- Logical Gap #3 / Required Ablation #1 (adapter provenance correction) — **downgraded from "resolved
  during this review" to "correctly diagnosed in Round 1, still not written back to the paper trail."**
  See Assessment above. This is the one item that changed status, and it changed in the direction of
  "still needs doing," not "done." I'm restating it here as a still-open action rather than double
  counting it as new.
- Required Ablation #2 (optional second rater on the 8 reasoning strings) — still optional, still not
  blocking; no new information this round.

**No concerns from Round 1 have been invalidated or found overstated on reflection.**

## Cross-check of Narrative's 4 flagged "smoothing" risks

I read `EXP03/results.md` and `formalized_results.md` directly for each rather than taking
Narrative's characterization on faith.

1. **G3's 38%-agrees bucket masking 2/3 fabrication — GENUINE, and already correctly guarded in the
   current source documents.** `EXP03/results.md` line 29 already states the 4-bucket table
   "complicates ... rather than confirming" the rule-catches-misses narrative, and lines 54/58/61
   plus the summary line 67 already document, in the primary evidence file itself, that 2 of the 3
   agrees cases (T05, T08) reach the correct label via fabricated sensor values. `formalized_results.md`
   (G3 section) explicitly carries this forward: "H2's non-enumerable-failure-mode requirement is
   exceeded: 6/8 ... reasoning strings contain fabricated sensor values." So the risk is real —
   Narrative is right that a skimmed "38% agrees" without this context would overstate the model —
   but it is a **future-compression risk**, not a defect in any document that exists today. Every
   source-of-truth file I checked already states the fabrication rate adjacent to the bucket
   percentage. The risk is that a later editing pass drops the adjacent sentence for space, not that
   anyone has done so yet.

2. **G5's "resolved" language implying leakage is fixed, not just quantified — GENUINE but already
   defused in the source text; risk is about the section header, not the content.**
   `formalized_results.md`'s "G5 Resolution" section (lines 144–196) is scrupulous: it states plainly
   under "Honest limit of this resolution" that "the flagged near-duplicate training frames remain in
   the training set that produced `best.pt`'s weights" and that "a fully clean number would require
   retraining after re-splitting by whole video/clip." The recommended caveat sentence itself (lines
   179–185) never uses the word "fixed" or "resolved" — it says "a modest, quantified optimistic
   bias." The only place the word "resolved" appears prominently is the section header itself and the
   Executive Summary line "is resolved in this pass" (line 23). Narrative's risk is specifically that
   a skimming co-author reads the header/Executive-Summary framing and stops there without reaching
   the "Honest limit" paragraph three screens down — that is a real structural risk (the caveat is
   present but not load-bearing at the point where "resolved" first appears), not a fabricated one.
   I'd go further than Narrative here: the fix is cheap and specific — rename the header from "G5
   Resolution" to something like "G5 — Corrected Bias Estimate (Leakage Not Removed)" before this
   becomes manuscript-section language, since headers get copied into paper section titles more
   readily than body prose does.

3. **G8's crossover-not-confirmation compressed into "H5 confirmed" — GENUINE, and the underlying
   result is exactly as easy to over-simplify as Narrative describes.** `formalized_results.md`'s G8
   section is precise: quantile is *more* sensitive at δ≤0.06 (the literal opposite of H5's stated
   direction) with equal-width only overtaking at δ≥0.08, and the text explicitly says "corrected,
   not confirmed." The risk is entirely that a later pass reaches for the punchier, wrong sentence
   ("quantile binning is more sensitive, use quantile") because it's simpler than the true crossover
   story. Nothing in the current documents says the wrong thing yet; the risk is prospective and
   correctly identified.

4. **Abstract-vs-body split on 0.719 vs 0.782 — GENUINE, and I can confirm the mechanism that would
   cause it, not just the risk in the abstract.** `vision.md` (the immutable, orchestrator-cannot-edit
   vision lock) states under "User Directives Captured During Setup": *"Empirical results that MUST
   be included and correctly attributed (do not alter, round differently, or drop): ... recall =
   0.719"* — this is a verbatim, non-negotiable figure the Abstract is contractually required to cite.
   `vision.md` was written before EXP07 ran and has no knowledge of 0.782 at all — it cannot, by
   construction, mandate disambiguating language it doesn't know is needed. Meanwhile
   `formalized_results.md`'s Evidence Gaps table already carries "0.719 vs. 0.782 recall ambiguity"
   at MEDIUM-HIGH priority with the required action "Add explicit disambiguating language wherever
   H7's safety discussion cites recall." Narrative's specific concern — that the Abstract gets
   drafted first from `vision.md`'s locked figure and frozen before the body's 0.782 correction
   propagates back up — is structurally the single most likely failure mode in this entire paper
   trail, precisely because `vision.md` is immutable by design and 0.719 is textually mandated there
   with no adjacent instruction to also state 0.782. This is not a case of the evidence not supporting
   the concern; it's a case where the concern is baked into the input constraints themselves. My
   addition: this needs to be resolved as "cite 0.719 as the trained/reported headline recall AND
   0.782 as the deployed-operating-point recall, both required, in the same Abstract sentence" — not
   resolved by choosing one number, since `vision.md` forbids dropping 0.719 and the safety argument
   requires 0.782.

**Summary: all four of Narrative's flagged risks are genuine, and none are overstated.** Three of the
four (G3, G5, G8) are risks about a future compression step degrading language that is currently
correct; none reflect an existing overclaim in any file on disk today. The fourth (0.719/0.782) is
the sharpest of the four because it is not merely a risk of careless editing — it is a structural
consequence of `vision.md`'s immutability plus a required figure that predates the finding that
complicates it. That one deserves the highest priority of the four at the writeup stage.

## New concerns

**The adapter-caveat scoping question, answered directly:** No — not every AQUA-1B claim in the
paper should carry the "admittedly under-trained adapter" caveat, and applying it uniformly would
itself introduce a new precision error rather than close one. There are exactly two AQUA-1B result
sites in `formalized_results.md` (verified by grep — lines 54 and 67, plus the emergent-finding
restatement of G3 at line 234), and they are not interchangeable:

- **G3/EXP03** (the decision-support behavioral measurement, and by extension the "fabricated sensor
  values" emergent finding and the round-1-identified "narrow interface" novelty claim) **is run with
  `sure-aqua-adapter` loaded** — confirmed both by `EXP03/results.md` line 5 (`AQUA_ADAPTER_PATH`
  exported) and independently by this round's own re-derivation of what that adapter was trained on.
  **This is the one site that needs the caveat**, and the honest form of it is not generic
  hand-waving ("results may not generalize") but the specific, falsifiable sentence Round 1 already
  drafted: the deployed adapter is the 8-example smoke-test dataset the project's own `finetune.py`
  docstring calls insufficient, not the 128-example v2 that existed on disk, unused, before the
  adapter was trained. Omitting this — stating the G3 findings as if they characterize "AQUA-1B" or
  "a fine-tuned domain LLM" without naming which adapter — would be an overclaim in the sense Round 1
  already argued: it invites a generalization about sub-2B on-device LLMs as decision-support
  components that the evidence doesn't support; it's evidence about one specific, self-documented-as-
  undertrained artifact.
- **G4/EXP04** (the agentic tool-routing negative result) **explicitly runs the base model with no
  adapter at all** — `EXP04/results.md` line 10 states this in so many words: "`AQUA_ADAPTER_PATH`:
  left unset (base model) ... No shell history, run log, or comment anywhere in the repo indicates the
  adapter was set for the original benchmark." Attaching an "under-trained adapter" caveat to G4's
  0%/0% tool-routing result would be **factually wrong** — there is no adapter in that result to be
  under-trained. G4's negative result is about the base instruction-following/tool-selection
  capability of AQUA-1B itself, adapter-independent, and already carries its own correct caveat (base
  model, unset adapter, disclosed).

So the scoping answer is precise rather than blanket: **G3 and anything derived from it (the
fabrication emergent finding, the "narrow interface" novelty claim, any Discussion sentence that
uses EXP03 to characterize what the LLM component contributes) needs the adapter caveat; G4 needs its
own distinct existing caveat (base model, no adapter) and must not receive the same one.** A writeup
that mechanically stamped "using an admittedly under-trained adapter" onto every AQUA-1B mention,
including G4's, would be trading one precision error (an unscoped generalization from G3) for another
(misattributing G4's base-model result to an adapter that was never loaded for that experiment). The
correct fix is targeted: add the caveat once, at G3's first mention and again at the "fabricated
sensor values" emergent finding, using the record-count-plus-mtime-ordering evidence above; leave
G4's existing "base model, adapter unset" framing untouched.

One more scoping note worth naming explicitly for the writeup: the caveat, once added to G3, actually
**strengthens** rather than weakens the paper's central safety argument — this is the same point
Round 1 made and it survives this round's re-derivation intact. "The architecture held up against a
component its own training pipeline warns is undertrained" is a better sentence than "the
architecture held up against AQUA-1B" precisely because it pre-empts the obvious reviewer objection
("well, of course it degenerates to fail-safe defaulting — the adapter is undertrained, try it with
v2"). Naming the adapter's provenance turns a potential weakness (why is the model so bad?) into a
disclosed, favorable framing (the safety property doesn't depend on the model being good, and here is
the independently-checkable receipt that it wasn't).

No other new concerns. I did not find any new discrepancy between `formalized_results.md`/`.json`
and the underlying `EXP0*/results.md` files beyond what Round 1 and this round's targeted checks
already cover, and I found no instance of a claim anywhere in the current paper-trail files that
outruns its cited evidence.

## Verdict rationale

The evidence chain is exactly as sound as Round 1 found it, with one correction to my own Round 1
text: the adapter-provenance finding was correctly derived in Round 1 but has not yet been written
back into `formalized_results.json`/`EXP03/results.md` — that is a pending action item for
pre-freeze, not a resolved one, and I'm flagging the status change explicitly rather than letting
Round 1's "resolved during this review" stand uncorrected. Narrative's four smoothing risks are all
genuine and none are overstated; three are prospective compression risks against currently-correct
source text, and the fourth (0.719/0.782) is a structural consequence of `vision.md`'s immutable,
pre-EXP07 figure mandate that the writeup must resolve by stating both numbers together, not by
picking one. The adapter caveat belongs on G3 and its derivatives only, not on G4 — applying it
uniformly would introduce a new, avoidable factual error into the paper (misattributing an
adapter-free base-model result to an adapter). None of this blocks freeze; all of it is
writeup-craft discipline the manuscript needs to carry through, consistent with Round 1's own
finding that the results survive in their precisely-scoped form and that the honest version is the
more compelling one.

VERDICT: ACCEPT

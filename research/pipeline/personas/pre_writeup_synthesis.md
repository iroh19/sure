# Pre-Writeup Council — Synthesis (Phase 7b, Advisory)

**Status:** All 3 personas (Practical, Rigor, Narrative) returned **ACCEPT** in both Round 1 and
Round 2. This phase is advisory and does not block the pipeline. One flagged unresolved item
(adapter-provenance write-back) was fixed as part of closing this phase — see below.

**Inputs synthesized:** `pre_writeup_persona_practical_round_{1,2}.md`,
`pre_writeup_persona_rigor_round_{1,2}.md`, `pre_writeup_persona_narrative_round_{1,2}.md`,
`formalized_results.json`, `experiment_workspace/experiment_runs/EXP03/results.md`,
`experiment_workspace/experiment_runs/EXP04/results.md`.

---

## 0. Pre-freeze correction applied in this pass

Rigor's Round 2 review found that the Round 1 adapter-provenance correction was derived but never
written back into the paper trail. This is now fixed:

- **`paper_workspace/formalized_results.json`** — G3's `gaps[1]` entry, which previously read
  "Adapter provenance ... is mtime-only ... no commit-hash provenance is possible," now states the
  full corrected finding (see below) with an explicit scope note.
- **`experiment_workspace/experiment_runs/EXP03/results.md`** — open decision #3 and the "Success
  criteria assessment" adapter-provenance line now carry the same corrected finding.

**The corrected fact (verified directly against the live codebase, read-only):**
The deployed adapter's training data — `llm-service/sure-aqua-adapter/_mlx_data/train.jsonl`
(7 records) + `valid.jsonl` (1 record), 8 total — content-matches
`llm-service/sure_finetune_data.jsonl` (8 lines) record-for-record. `llm-service/finetune.py`'s own
docstring names that exact file "el yazımı 8 örnek (yetersiz, sadece duman testi)" — "8 handwritten
examples, insufficient, smoke-test only" — and states the 128-example `sure_finetune_data_v2.jsonl`
is the documented default. Mtimes confirm v2 existed on disk *before* the deployed adapter's
`_mlx_data` files and `adapters.safetensors` were produced, ruling out "v2 didn't exist yet" as an
innocent explanation. `docker-compose.yml` mounts `sure-aqua-adapter` at `AQUA_ADAPTER_PATH`, and
`EXP03/results.md` confirms this exact path was exported for the G3 run. This is a record-count +
content-match + mtime-ordering argument (not a commit-hash proof — the adapter directory is
gitignored, so that remains unavailable), but it is strong, free, already-available evidence.

**Scope — verified narrow:** this applies to **G3/EXP03 only** (and anything derived from it: the
EF1 fabrication finding, any Discussion sentence that uses EXP03 to characterize "the LLM
component"). It does **not** apply to **G4/EXP04**, which ran with `AQUA_ADAPTER_PATH` left unset —
confirmed directly in `EXP04/results.md` open decision #2 ("base model," no adapter loaded at all).
Applying the caveat to G4 would be a factual error, not added precision.

---

## 1. Consensus points (all 3 personas, both rounds)

1. **Sharper central thesis for the writeup:** the backstop's safety property never depended on the
   LLM's reasoning being sound, only on the status label being extractable and defaulting safe when
   it isn't — and this held even against an admittedly under-trained, 8-record smoke-test LoRA
   adapter (not the 128-sample v2). This is a **stronger** stress-test result, not a weaker one:
   frame it as *"we did not even give the LLM a fair chance, and the architecture still held."*
2. **Results billing:** EXP03's fabrication finding (6/8 reasoning strings contain fabricated
   sensor values, including 2 inside the "agrees" bucket) plus the 0.719-vs-0.782 recall disclosure
   should lead Results. twin_bridge (G9) and minor data-integrity nits (0.858/0.859 rounding,
   EXP08's PSI resampling-seed inconsistency, AQUA-7B format-drift) compress to footnotes/short
   notes, not named subsections.
3. **Adapter caveat scope:** applies narrowly to results that used the adapter (G3/EXP03), **not**
   to G4/EXP04 (base model, no adapter) — do not overgeneralize into a blanket "AQUA-1B" or
   "sub-2B on-device LLM" caveat.
4. **Disclosure sequencing:** adapter provenance disclosure must come **early** (first mention of
   AQUA-1B/G3 results in Methods or the opening Results beat), not as a late caveat or footnote.

---

## 2. Updated Structural Recommendation (final, for writeup)

**Main body, high priority (promoted above original/pre-registered billing):**
1. **EXP03 four-bucket distribution + fabricated-sensor-value finding + adapter provenance (G3)**
   — opens Results. One combined beat, not separate call-outs: state the 50/38/12/0 split, then
   immediately the fabrication finding ("in 2 of 3 'agrees' cases the correct label was reached via
   a fabricated causal story"), then the adapter provenance sentence, then the explicit
   direction-of-inference sentence ("this makes the architecture's safety property stronger
   evidence, not weaker, since it was demonstrated against a self-documented-inadequate model
   component"). Do not split this into a subsection plus a separate footnote — it is one beat.
2. **Agent tool-routing negative result, replicated at n=9 (G4)** — keep protected second position;
   foreground the replication ("we tried to break this finding and could not").
3. **The 0.719-vs-0.782 deployed-operating-point disclosure (EF3/G7)** — promote from a figure
   annotation to a named callout/boxed paragraph with the explicit rule: "report the metric at your
   deployed threshold, not your F1-argmax, when the metric feeds a safety decision." Both numbers
   must appear together in the Abstract (see checklist below) — `vision.md` mandates 0.719
   verbatim and cannot be edited to also mandate 0.782, so the writeup must add it explicitly.
4. **H6 export/INT8 finding (G6)** — keep in main body; clean, replicated, actionable ("measure the
   whole exported pipeline before blaming quantization").

**Main body, standard priority (roughly as scoped):**
5. RAG asymmetric-threshold calibration (G1/H4).
6. G8's corrected PSI-binning story (quantile more sensitive at low δ, equal-width overtakes only
   at δ≥0.08) — state the crossover, not "H5 confirmed."
7. G5's corrected vision numbers as a caveat sentence beside the headline table, not its own
   subsection — always paired with "same-checkpoint re-evaluation, not a leakage-free retrain."

**Compress to appendix/footnote:**
- **twin_bridge (G9)** — one paragraph inside a combined "auxiliary evidence" subsection: "designed
  and unit-tested, not exercised against a live twin session." Not a standalone numbered subsection.
- 0.858-vs-0.859 rounding inconsistency — footnote, normalize to one value before freeze.
- EXP08's PSI resampling-seed inconsistency — footnote only.
- AQUA-7B format%/step-count reproducibility drift — one footnote where the agent-benchmark table
  is cited; state as "noted, unexplained, non-conclusion-changing," no independent narrative weight.
- The stale-0.695-in-RAG-corpus finding stays in the data-integrity table for the record; its
  rhetorical copy (one sentence) belongs in Introduction/Discussion.

---

## 3. Final recommended central-claim framing (for Introduction/Conclusion)

> This paper's central finding is that a deterministic safety backstop's soundness never depended
> on its LLM component reasoning correctly — only on a single enumerable status field being
> extractable from the model's output, and on the system defaulting to the safe state when it
> isn't. In the dominant observed pathway (50% of scenarios), the model's output was unparseable
> and the rule engine acted alone on a safe default; and even where the model's final status label
> was correct, its stated reasoning fabricated sensor readings that were never in the input in two
> of three such cases — a failure mode invisible to any evaluation that checks only the output
> label. Critically, this was demonstrated not against a fairly-tuned model but against an
> 8-example LoRA adapter that the project's own training pipeline documents as an insufficient,
> smoke-test-only artifact, with a properly-sized 128-example alternative sitting unused on disk.
> That is a stronger, not weaker, stress test of the architecture: the safety property held while
> the model was given close to no fair chance to reason well in the first place, which pre-empts
> rather than defers the obvious reviewer objection that a better-tuned model would change the
> conclusion. The practitioner rule this supports is correspondingly general and falsifiable —
> architect a safety-critical LLM-plus-validator pipeline assuming the model will frequently
> produce nothing usable, verify that your fallback default is the conservative one, and never let
> your validator read anything from the model beyond the one enumerable field it is designed to
> certify.

---

## 4. Must-disclose-early checklist

| Item | Must first appear in | Notes |
|---|---|---|
| **Adapter provenance** (deployed adapter = 8-example smoke-test dataset, not 128-example v2) | **Methods**, at first mention of AQUA-1B/G3's setup — repeated as the opening clause of the Results 5.1 beat | Scope: G3/EXP03 derivatives only. Never attach to G4/EXP04 (base model, no adapter). State the direction-of-inference explicitly ("stronger, not weaker") at the same place — do not let it read as a hedge. |
| **0.719 vs. 0.782 recall** | **Abstract** (both numbers, same sentence — `vision.md` mandates 0.719 verbatim and cannot be edited, so 0.782 must be added alongside it, not substituted) and **Results** (named callout, not a figure caption) | Highest-priority disclosure item per Rigor Round 2 — the single most likely failure mode is an Abstract frozen on 0.719 alone before the body's 0.782 correction propagates up. |
| **Live RAG 0.695 leak** | **Introduction or Discussion** (one rhetorical sentence: "even this system's own production knowledge base was found, during this audit, to be serving a stale figure it had already corrected elsewhere") + **data-integrity table** for the record | Do not bury as only a table row — it is a strong self-demonstrating artifact for the paper's hallucination-discipline argument. |
| **Sparse-frame coverage gap** (val set has zero k=1/k=2 frames; 0/98 full-frame-miss result doesn't cover the sparse regime) | **Results** (immediately beside the 0/98 headline number) and **Limitations** | State the conditional explicitly: "this result is conditional on a val-set property that was never designed in, at exactly the regime most likely to matter for a welfare check" — do not let it read as a shrug. |

---

## 5. Remaining concerns raised by any persona (for completeness — all non-blocking, all ACCEPT)

See `paper_workspace/review_1/pre_writeup_concerns.md` for the full itemized list with sourcing.
Summary: four writeup-craft "smoothing" risks (Narrative, cross-checked and confirmed genuine by
Rigor Round 2) where a compression pass could flatten a correct-but-complex finding into a
punchier-but-wrong sentence; one framing risk specific to the adapter finding (reaching for
"undertrained, so discount this" instead of "undertrained, so this is stronger"); one sequencing
risk (adapter provenance arriving too late); one structural-billing risk (twin_bridge / flat
eleven-goal structure); and two low-priority footnote-level data-integrity nits. None require new
experiments or re-runs; all are disclosure, sequencing, or billing decisions for the writeup phase.

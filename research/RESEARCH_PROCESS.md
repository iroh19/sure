# How the S.U.R.E. Manuscript Was Researched and Written

### A record of an agentic research run with pAI/MSc, human on the loop

**Project:** S.U.R.E. (Aquaculture Welfare Integration) — Autonomous Sturgeon Welfare Monitoring in
Recirculating Aquaculture Systems via Edge-AI and RAG-Enhanced Deterministic Fusion
**Authors of the manuscript:** Batuhan Çıtak, Erdem Sabri Veli
**Run window:** 26–27 August 2026
**Artifacts:** [`research/`](.) in this repository

---

## 1. Why this document exists

The manuscript in [`SURE-paper.pdf`](SURE-paper.pdf) was not written by hand. It was produced by an
agentic research pipeline — **pAI/MSc**, a research agent from MIT — driven by us as humans on the
loop. Every intermediate artifact that pipeline produced is committed alongside the paper in
[`pipeline/`](pipeline/) and [`experiments/`](experiments/).

We are publishing the process, not just the product, for three reasons:

1. **Disclosure.** A reader who finds a machine-assisted paper deserves to know how it was made and
   where the human judgment entered. The manuscript itself carries this in its acknowledgements and
   in a page watermark; this document is the long form of that same statement.
2. **Auditability.** The pipeline's most useful output was not prose. It was a set of eleven
   executed experiments that contradicted several things we believed about our own system. Those
   contradictions are in [`experiments/`](experiments/) with raw logs, and anyone can recheck them.
3. **Method.** Running a research agent over an already-built system turned out to be a genuinely
   different activity from "asking an AI to write a paper." This document describes what actually
   happened, including where it was uncomfortable.

---

## 2. What pAI/MSc is

pAI/MSc is a research pipeline described in the MIT technical report *"pAI/MSc: ML Theory Research
with Humans on the Loop"* by Mahmoud Abdelmoneum, Pierfrancesco Beneventano, and Tomaso Poggio
(MIT, Technical Report v0, 2026) — <https://dspace.mit.edu/handle/1721.1/165377>.

Its design premise is that a research agent should not be a single long prompt. It is a staged
pipeline in which distinct agents argue with each other, a literature pass is run adversarially
against the researcher's own novelty claims, experiments are designed and *verified independently
of the agent that ran them*, and the human is asked for a decision only at a small number of
checkpoints — the "humans on the loop" framing, as opposed to humans in every step.

The manuscript cites the report as `pAIMSc_2026` and states in its acknowledgements: *"We partially
used pAI/MSc for this manuscript."* The compiled PDF also carries a low-contrast background
watermark on every page reading *"Generated with a research agent created by Pierfrancesco
Beneventano."* That watermark is intentional and is part of the tool's attribution requirement — it
is not a rendering defect.

**What "partially" means here, precisely:** the system being written about — the code, the models,
the training runs, the vision dataset — is our own work and predates the paper. The pipeline did
literature grounding, experiment design, experiment execution against our existing codebase,
independent verification, and drafting. The final factual corrections in §6 were ours.

---

## 3. The input we gave it

The single input was [`pipeline/research_task.md`](pipeline/research_task.md) — a one-page brief
naming the system, the architecture, the empirical numbers we had on hand, and the framing we
wanted. Alongside it we supplied the repository's own `README.md`, `MODEL_RAPORU.md`, `PLAN.md`, and
`TODOS.md` as grounding context, so the agent would write about the system that exists rather than
an idealized one.

That brief was then frozen into [`pipeline/vision.md`](pipeline/vision.md) — a read-only "vision
lock" the pipeline is not allowed to overwrite. Every persona in every later stage reads the
original brief before evaluating any proposal, so the run cannot quietly drift away from what we
actually asked for. This mattered: by the end, the pipeline was arguing *against* the framing in
that brief, and the lock is what makes that disagreement legible rather than invisible.

---

## 4. The pipeline, stage by stage

The full machine-readable record is [`pipeline/state.json`](pipeline/state.json); the phase timeline
with timestamps is [`pipeline/token_summary.json`](pipeline/token_summary.json). Forty-four agent
invocations across roughly twenty-six hours of wall time.

### 4.1 Persona council (3 rounds)

Three adversarial reviewer personas — **practical**, **rigor**, and **narrative** — independently
critiqued the proposal, followed by a synthesis pass, repeated for three rounds until all three
returned `ACCEPT`. Their full write-ups are in [`pipeline/personas/`](pipeline/personas/).

The rigor persona is the one that does damage. It is the reason the central claim of the paper is
narrower than the claim in our original brief.

### 4.2 Adversarial literature review

One pass, 31 citations, and — the number that matters — **11 of our claims falsified or downgraded**.

The headline result was uncomfortable and correct: our "novel" dual-layer architecture, in which a
deterministic rule engine holds final authority over an LLM's severity judgment, was classified
`EQUIVALENT_KNOWN`. It is the Safety Instrumented Systems pattern (IEC 61508 / 61511), it is RL
shielding, and it is the standard industry LLM-guardrail arrangement. We had independently arrived
at a well-established idea and were about to present it as new.

The review's recommendation was not "drop the paper." It was to reframe the contribution as
**cross-layer consistency composition** — which is what the manuscript now argues. See
[`pipeline/literature_review.md`](pipeline/literature_review.md) and
[`pipeline/novelty_flags.json`](pipeline/novelty_flags.json).

### 4.3 Brainstorm and goal formalization

48 candidate approaches were generated ([`pipeline/brainstorm.md`](pipeline/brainstorm.md)) and
distilled into **11 formal research goals** with pre-registered success criteria, including
pre-registered *fallback* findings — what to report if the strong version of a hypothesis failed
([`pipeline/research_goals.json`](pipeline/research_goals.json)). The track decomposition gate
determined the work was empirical, not theoretical, so no theory track ran.

**Human checkpoint #1.** The pipeline stopped here and asked us to approve the goals before
spending compute on experiments. We approved the empirical track.

Pre-registration is the part that gives the next section its teeth: because the fallback findings
were written down *before* the experiments ran, the pipeline could not retroactively decide that a
disappointing result was the result it had been looking for all along.

### 4.4 Eleven experiments

Designed in [`experiments/experiment_design.json`](experiments/experiment_design.json), executed in
three parallel groups against our real codebase, with EXP10 and EXP11 run last as a
finalization pass. Raw scripts, stdout logs, and result JSON for each are in
`experiments/EXP01/` … `experiments/EXP11/`.

### 4.5 Independent verification

A separate verifier agent recomputed every headline metric from the raw output files on disk rather
than trusting the summaries — **8 PASS, 3 PARTIAL, 0 FAIL**
([`experiments/verification_report.md`](experiments/verification_report.md)). Where sample sizes
were small (n=8, n=9, n=98), the verifier says so in line rather than letting the number stand
unqualified.

Completion was scored at **0.95** with a recommendation of `COMPLETE`
([`pipeline/verify_completion.json`](pipeline/verify_completion.json)).

### 4.6 Writing, review, and revision

A second persona council ran *before* drafting, a narrative-voice pass set the register, then two
full write-up cycles, proofreading, and a simulated peer review. The review scored the manuscript
**8/10 overall** — soundness 3, presentation 4, contribution 3, clarity 4, concision 3 — with
`ai_voice_risk: low`, **zero hard blockers**, and one must-fix
([`pipeline/review_verdict.json`](pipeline/review_verdict.json), full report in
[`pipeline/review_report.pdf`](pipeline/review_report.pdf)).

The single must-fix is a good illustration of the verifier's usefulness: the introduction claimed a
stale figure had been discovered "weeks after the correction," while §6.6 and Known Limitations both
said "43 minutes' worth of commits." The reviewer checked the actual git log, found commits
`0e8b414` and `9a260af` 43 minutes apart on the same day, and flagged the introduction as not merely
inconsistent but factually wrong. It was corrected.

A final post-review persona council returned `ACCEPT` from all three personas across two rounds,
with zero narrative vetoes. All five pipeline gates — feasibility, track decomposition, duality,
review quality, post-review personas — passed.

---

## 5. What the experiments actually found

This is the part worth reading. Several results contradict what we believed when we wrote the brief.

| # | Question | Finding |
|---|---|---|
| **EXP01** | Is the RAG retrieval real, or an artifact of a tiny 8-document corpus? | Real. `e5-small` beats a random baseline by **hit@1 +0.586** (0.793 vs 0.207) and **MRR +0.438**. The configured threshold 0.85 is confirmed precision-favouring against the F1-argmax of 0.84. |
| **EXP02** | Do the eval harness and the runtime path evaluate the *same* rules? | Yes — proven by module-identity check, not by output comparison. 8/8 scenario agreement. |
| **EXP03** | **How does the dual-layer system actually behave?** | **The central result, and not the one we expected.** In 8 scenarios: the rule engine genuinely caught an LLM under-call in **1 case (12%)**; it defaulted safe because the model's output was **unparseable in 4 cases (50%)**. The dominant safety mechanism is not error correction — it is fail-safe defaulting on malformed output. Worse: **6 of 8 reasoning strings contained fabricated sensor values** that were never in the input, including inside the bucket where the model's final verdict *agreed* with the rules. Output-only evaluation cannot see this. |
| **EXP04** | Does the larger AQUA-7B model route tools better? | No. It selects the same first tool constantly, across **9/9 independent scenarios** after an adversarial re-run. A preserved negative result. |
| **EXP05** | Is there train/val leakage in the vision dataset? | **32 near-duplicate frame pairs** (14 of them adjacent-index) found by perceptual hash. Flagged `PARTIAL` — enumerated but not yet folded into a corrected headline metric. |
| **EXP06** | Do ONNX/TorchScript exports lose accuracy? | No. The apparent loss is a **shared post-processing artifact** — 0 of 98 detections meaningfully differed. |

| # | Question | Finding |
|---|---|---|
| **EXP07** | Is the headline recall the recall we actually run at? | **No.** The configured operating point (conf=0.20) has **recall 0.782**; the widely-quoted 0.719 is the F1-argmax optimum. Both are correct; they answer different questions, and the manuscript now reports them distinctly. The validation set also contains **zero sparse (k=1, k=2) frames** — an entirely untested regime. |
| **EXP08** | Is equal-width PSI binning strictly better? | **No — our claim needed correcting.** It is *less* sensitive at small distribution shifts and *more* explosive at larger ones, because a specific bin empties. Not monotonic. |
| **EXP09** | Does `twin_bridge` hold up? | 18/19 pre-existing tests pass; the one failure is a bug in a test helper. It was untracked in git with no commit history. |
| **EXP10** | Is the paper's central claim defensible as stated? | Recommended narrowing it. The escalation function is unconditional fail-safe defaulting, not sophisticated error correction, and there is **zero protection against fabricated-but-correct-verdict reasoning**. |
| **EXP11** | Are the numbers in the system consistent with the numbers in the paper? | **A live data-integrity bug.** `llm-service/knowledge/06-davranis-ve-refah-gostergeleri.md:58` still states recall ≈ 0.695 — a superseded figure — and that file **is ingested into the production RAG vector store**, so the retrieval layer can serve a stale number. Six stale or inconsistent figures were catalogued in total. |

The manuscript's abstract now reflects EXP03 and EXP10 rather than our original framing. The claim
it makes is deliberately narrow and falsifiable: such a pipeline can be made safe against an
unreliable model *provided its validator reads nothing beyond one enumerable field and always
defaults conservatively* — a claim about interface design, not a claim that the model was made
trustworthy.

---

## 6. What we corrected ourselves, after the pipeline finished

The pipeline completed and passed all its gates. We then reopened the manuscript and made
corrections it could not have made on its own, because they depend on facts only we knew. These are
logged in [`pipeline/state.json`](pipeline/state.json) under `post_completion_human_revision`.

**A paper-wide factual overclaim.** The draft implied S.U.R.E. is a live, field-deployed system.
It is not, and the following is now stated prominently in the Introduction, the Experimental Setup,
and as the first item in Known Limitations:

- **No test used real physical sensors or an operating RAS facility.** No such sensor hardware
  exists. Every sensor reading in every experiment is **synthetically generated**, not recorded.
- **The 510-image vision dataset is real** — camera footage of the physical rig, hand-labeled — but
  intentionally small, with expansion planned.
- **We did not enter TEKNOFEST**, the competition S.U.R.E. was built for, and did not pass its
  preliminary evaluation round.
- **The actual contribution is a feasibility and resource-management demonstration** — testing
  whether a multi-component pipeline of this shape fits in the memory and compute budget of edge
  hardware — **not a field validation of decision accuracy.**

Every use of "deployed," "production," and "real-world" was re-read across all eleven sections.
Legitimate references to a *configured parameter value* were kept; anything implying live field
operation was corrected to "implemented" or "offline, bench-level evaluation."

**Three figure rendering bugs.** Colliding annotations in Figure 2, an out-of-range annotation
distorting the y-axis and overdrawing a tick label in Figure 3, and PSI curves riding over their
threshold labels in Figure 4 — all fixed in
[`paper/figures/make_figures.py`](paper/figures/make_figures.py) with explicit axis limits, white
text bounding boxes, and leader-line arrows for near-coincident points, then verified by rendering
and visually inspecting each figure before and after.

The corrected manuscript recompiles to 32 pages with zero errors.

---

## 7. An honest assessment of the method

**Where it clearly helped.** The adversarial literature review stopped us from publishing a known
pattern as a novel one. Pre-registered fallback findings meant EXP03's disappointing result got
reported as the finding instead of being quietly reframed. Independent verification — a second agent
recomputing from raw files rather than reading summaries — caught the "weeks" versus "43 minutes"
error that a self-consistent draft would have carried to publication. And EXP11 found a real,
unfixed bug in the live codebase that had nothing to do with writing a paper.

**Where the human was indispensable.** Every correction in §6 came from us. The pipeline had no way
to know that our sensors were synthetic, that the hardware did not exist, or that we never entered
the competition, because nothing in the repository said so — and it wrote a confident,
well-cited, internally consistent manuscript around that gap. A research agent will faithfully
extend whatever premises you hand it. Checking the premises is not a step you can delegate.

**Where it is limited.** Sample sizes are small in the places that carry the most weight: the
central behavioral result is n=8. Three experiments are `PARTIAL`, and EXP05's leakage finding is
enumerated but not yet propagated into a corrected headline vision metric — an open task, stated as
such in the paper rather than papered over.

---

## 8. Reproducing and re-checking

```bash
# Rebuild the manuscript from source (requires a TeX distribution)
cd research/paper
pdflatex final_paper.tex && bibtex final_paper && pdflatex final_paper.tex && pdflatex final_paper.tex

# Regenerate the five figures
cd research/paper/figures && python make_figures.py
```

Each experiment directory under [`experiments/`](experiments/) contains the script that was run, its
stdout log, and its result files. The verifier's independent recomputation of every headline number
is in [`experiments/verification_report.md`](experiments/verification_report.md).

One file was omitted for size: `EXP05/near_duplicate_pairs_full.json` (2.4 MB, the full perceptual-hash
pair dump). Its aggregates are in `EXP05/exp05_summary.json` and the audit script that produced it,
`EXP05/exp05_leakage_audit.py`, is committed.

---

## 9. Attribution

The S.U.R.E. system — backend, vision service, LLM service, MLOps, and digital-twin bridge — is the
authors' own work and predates this manuscript.

The manuscript was produced with **pAI/MSc**, a research agent developed at MIT by Mahmoud
Abdelmoneum, Pierfrancesco Beneventano, and Tomaso Poggio, and is cited as such in the paper's
references and acknowledgements. The background watermark on every page of the compiled PDF is part
of that tool's attribution requirement.

> Abdelmoneum, M., Beneventano, P., & Poggio, T. (2026). *pAI/MSc: ML Theory Research with Humans on
> the Loop.* MIT Technical Report v0. <https://dspace.mit.edu/handle/1721.1/165377>

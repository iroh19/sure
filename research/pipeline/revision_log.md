# Revision Log — S.U.R.E. Applied-Systems Paper (project_000, Phase 8 Writeup)

## Cycle 1, Pass 1 — Planning (no .tex content)

Read in full, in order: `formalized_results.md`/`.json`, `structure_analysis.txt`,
`resource_inventory.tex`, `track_merge_summary.md`, `research_proposal.md` (via prior passes'
extraction into `resource_inventory.tex`/`formalized_results.md` — the Key Formalizations,
Citation Inventory, and Writing Resources sections were consumed directly), `literature_review.md`
and `literature_review_matrix.md`, `references.bib` (55 entries confirmed via grep),
`narrative_brief.md` (full, all voice/structure guidance binding), `pre_writeup_synthesis.md`
(central-claim framing and Updated Structural Recommendation), all 11
`experiment_workspace/experiment_runs/EXP01`-`EXP11/results.md` files in full, `vision.md` (the
immutable original vision — confirmed locked figures: mAP50 0.840, precision 0.858, recall 0.719,
MRR 0.856, hit@1 0.793, CoreML p50 9.0ms/p95 9.5ms, INT8 delta -0.0082), and
`initial_context/README.md`/`MODEL_RAPORU.md` for system background. No `*style*`/`*voice*`/
`*writing*` file exists in `initial_context/`, confirmed by listing — used the bundled default
style guide as instructed.

**Produced this pass:**
- `paper_workspace/author_style_guide.md` — merges the bundled default (Part A, reinterpreted:
  "theorem" -> "Formalization", "proved" -> "measured/observed") with `narrative_brief.md`'s
  paper-specific voice section (Part B: central-claim framing, 3 surprise markers at exact
  locations, must-disclose-early table, Related Work cluster structure, anti-AI voice table,
  Discussion blueprint) and a Formalization-specific reinterpretation (Part C).
- `paper_workspace/paper_outline.md` — full section plan per `vision.md`'s mandated skeleton plus
  the council's Discussion/Known Limitations/Appendix additions; Results structured 5.1-5.6 with
  the agentic negative result (G4) promoted second, not last, per the Practical persona's
  structural recommendation; twin_bridge (G9) compressed to one paragraph inside a combined
  auxiliary-evidence subsection, per unanimous persona consensus.
- `paper_workspace/intro_skeleton.tex` — paragraph-by-paragraph plan for the Introduction (written
  last, in Pass 4), with explicit RQ1-RQ3, explicit takeaways each pointing to a specific
  figure/section, and an explicit non-claim paragraph guarding against "solves LLM unreliability"
  overclaiming.
- `paper_workspace/style_macros.tex` — `\formalization{}` environment (not `\theorem{}`),
  `\question{}`, `\takeaway{}` (via a `takeawaybox` tcolorbox), `\sourceclaim{}` (inline raw-file
  provenance marker), `\disclosure{}` (named callout box for must-disclose-early items like the
  0.719-vs-0.782 distinction, so it does not end up buried in a figure caption).
- `paper_workspace/reader_contract.json` — one-sentence claim, evidence priority ranking (matches
  `pre_writeup_synthesis.md`'s Updated Structural Recommendation exactly), a `must_never_claim`
  list (the 6 overclaiming traps this project's own reviews flagged), and a
  `must_disclose_and_where` table.
- `paper_workspace/editorial_contract.md` — a binding checklist (data-integrity gate, voice gate,
  citation gate, structural gate, compilation gate) to be re-applied at the end of every subsequent
  pass.
- `paper_workspace/theorem_map.json` — the 4 Key Formalizations from `resource_inventory.tex`,
  each with its statement, source line, empirical grounding, and manuscript placement; labeled
  "Formalization," never "Theorem."
- This file (`revision_log.md`), started with this entry.

**Key decisions locked in this pass (binding for Passes 2-6):**
1. Results section structure is 5.1 (dual-layer, G2+G3, central result) / 5.2 (agentic negative
   result, G4, promoted second) / 5.3 (edge vision, G5/G6/G7, includes both surprise-marker-3 and
   the 0.719-vs-0.782 disclosure) / 5.4 (RAG, G1) / 5.5 (MLOps/PSI, G8) / 5.6 (auxiliary evidence:
   twin_bridge G9 + data-integrity Table 3 callout, compressed).
2. Exactly 3 surprise markers, at the exact locations and near-verbatim phrasing specified in
   `narrative_brief.md` §v. No fourth.
3. Adapter-provenance disclosure is scoped strictly to G3/EXP03; a hard rule (not a style
   preference) that it must never be attached to G4/EXP04.
4. Writing order for Pass 4 is Discussion+Known Limitations -> Introduction -> Abstract, per the
   prompt's explicit sequencing (write framing sections last, once the body's actual findings are
   fixed in prose).
5. `vision.md`'s locked headline figures (0.858/0.719/0.840/0.856/0.793/9.0ms/9.5ms/-0.0082) are
   treated as immutable citation targets; any raw-reproduction discrepancy (e.g. 0.859 vs. 0.858)
   is footnoted per Table 3, never silently reconciled by picking one value and deleting the other.

---

## Cycle 2, Passes 7-12 — Review and Improve

**Pass 7 (critical re-read):** Read all 12 section files plus final_paper.tex in full as a skeptical
reviewer, checked against `author_style_guide.md`, `narrative_brief.md`, `pre_writeup_synthesis.md`,
and `review_1/pre_writeup_concerns.md`, and spot-checked 15+ headline numbers directly against
`experiment_workspace/experiment_runs/EXPnn/results.md` and raw JSON files (EXP01, EXP03, EXP04,
EXP05, EXP06, EXP07, EXP08, EXP09, EXP11 — all matched exactly bar one). Findings appended to
`paper_outline.md`. Two genuine issues found:
1. **Overstated fabrication count.** `results.tex` §6.1 and `system_architecture.tex`'s
   Formalization 2 SOURCE_CLAIM comment both said "6 of 8 [scenarios] contain a fabricated numeric
   value." `EXP03/results.md`'s own synthesis paragraph (line 67) supports this claim for only 3 of
   8 scenarios (T02, T05, T08) — the model is shown fabricating a specific number not in the input.
   The other 3 "inaccurate" scenarios (T03, T06, T07) are inaccurate for a different reason: an
   unsupported blanket claim with no invented number, or an internally incoherent reading of a
   plausibly real value. The Abstract/Introduction's "two of three" framing (the agrees-bucket
   fabrication rate) was independently re-verified as exactly correct — only the broader "6 of 8"
   claim was overstated.
2. **Conclusion restates the Abstract.** The Conclusion's opening paragraph closely paraphrased the
   Abstract's central-finding sentences almost 1:1 in the same order, contrary to the anti-AI-voice
   table's explicit "Conclusion restates abstract" anti-pattern.

Everything else checked — Abstract voice rules, the 3 surprise markers' placement and phrasing, the
LoRA adapter caveat's G3-only scoping, the live RAG 0.695 leak's disclosure prominence, the Results
5.1-5.6 ordering against `pre_writeup_synthesis.md`'s Structural Recommendation, the 4
Formalizations' labeling, Related Work's non-catalogue structure, citation resolution, and
cross-reference integrity — was found already compliant with no changes needed. This is a genuine
testament to how disciplined Cycle 1's execution already was.

**Pass 8 (Related Work / Background):** No content changes required. Verified the Cluster-A/pivot/
Cluster-B/Cluster-C/what's-new structure `narrative_brief.md` mandates is implemented exactly, and
the SIS/IEC-61508–61511 and RL-shielding positioning matches `novelty_flags.json`'s own
INTEGRATION/MEASUREMENT/CROSS-LAYER framing. Grepped `references.bib` and confirmed zero missing
citations — no WebSearch-and-add was needed for a genuinely absent citation. This pass did surface,
via later visual inspection (folded into Pass 11-12), a different and more serious bibliography
defect: 26 of 56 `references.bib` entries carried the literal placeholder author `{{Unconfirmed}}`.

**Pass 9 (main technical sections):** Fixed the Pass 7 fabrication-count overstatement in
`results.tex` (now: "6 of 8 materially misrepresent the true sensor snapshot — of those, 3 (T02,
T05, T08) fabricate a specific numeric sensor value never present in the input... the remaining 3
are inaccurate in a different way") and in `system_architecture.tex`'s Formalization 2 SOURCE_CLAIM
comment. Updated `appendix.tex`'s EXP03 full-record table (Table 4) to bold and explicitly label the
3 fabricated-value cases versus the 3 not-fabricated-but-inaccurate cases, and rewrote the tally
sentence to state this distinction. Fixed a pre-existing minor bucket-naming inconsistency
(appendix said "under-calls-escalated", body said "under-calls-and-escalated" — normalized).
Re-verified notation consistency and the 5.1-5.6 ordering — no further changes needed.

**Pass 10 (Discussion/Conclusion/Abstract/Introduction):** Rewrote the Conclusion's opening
paragraph to lead with interpretive judgment rather than re-narrating the Abstract's findings in the
same sentence order — all facts preserved, only the framing and sentence shapes changed. Re-verified
Discussion's one hedged conjecture still uses "suggest"/"do not demonstrate beyond this one system"
with no "proves" anywhere, and re-confirmed the Abstract is still clean of citations/refs/formulas
and states 0.719-vs-0.782 in one sentence after the Pass 9 edits.

**Pass 11 (re-assemble and recompile):** Ran the full compile sequence. Compilation itself was
clean (0 errors) after Passes 9-10, but a full-page visual render check — going beyond Cycle 1's
`pdfinfo`/grep-only verification — surfaced real rendering defects Cycle 1 had not caught:
- `known_limitations.tex` had a long file-path citation inside `\texttt{}` that overflowed 242pt
  (3.36in) past the page's right margin, clipping content off the physical page entirely. Fixed by
  switching to `\url{}` (from the already-loaded `url` package), which breaks at slashes.
- Four tables (`results.tex`'s Table 1 goal-summary and Table 2 headline-metrics; `appendix.tex`'s
  Table 4 EXP03-full-record and Table 6 EXP04-full-record) were overflowing 23-61pt past the margin
  because their widest columns used plain non-wrapping types. Fixed by converting to `p{}` columns
  with explicit widths.

Separately, while inspecting the References pages for the table fixes, discovered that 26 of 56
`references.bib` entries carried the literal placeholder author `{{Unconfirmed}}` — inherited from
Cycle 1's literature-review pass — including two cited via `\citet{}` where "Unconfirmed" rendered
as the grammatical subject of a sentence (e.g. "Unconfirmed [2024e]'s cross-modal stress classifier
is the closest"). Resolved via `WebFetch`/`WebSearch` against each entry's own already-cited URL:
25 entries now carry real, source-verified author names; the one entry that could not be resolved
to a named author despite multiple search attempts (a ResearchGate MLOps preprint) is now labeled
`Anonymous` with a disclosing note, rather than left as the placeholder string. Re-ran the full
compile sequence after each fix. Final state re-verified: `grep -c 'thebibliography' final_paper.tex`
== 0; the pAI acknowledgement sentence and `pAIMSc_2026` bib entry present verbatim in
`references.bib` and `final_paper.bbl`; the watermark re-confirmed present via a pixel-isolation
render check (isolated the gray-240 pixel band and visually confirmed the diagonal watermark text is
legible); zero occurrences of the string "Unconfirmed" anywhere in the compiled PDF text.

**Pass 12 (final polish):** Read the fully compiled 31-page PDF end to end (every page rendered and
visually inspected, not only grep-checked). No leftover TODO/FIXME/XXX/placeholder text found. No
repeated-word typos found (script-verified). All 78 `\ref` usages still resolve against the 36
defined `\label{}`s (0 orphans). Final compile sequence (pdflatex, bibtex, pdflatex, pdflatex): 0
LaTeX errors, 31 pages, `thebibliography` count 0, pAI acknowledgement + `pAIMSc_2026` + watermark
all reconfirmed intact.

**Net effect of Cycle 2:** page count grew from 30 to 31 pages (entirely due to the table-wrapping
fixes taking more vertical space, not new content). No claim's substance changed — only overstated
precision in one fabrication-count claim was corrected, one section's opening was rephrased to add
distinct judgment rather than restate the Abstract, four tables and one citation were fixed so their
content no longer runs off the printed page, and 26 placeholder bibliography author fields were
resolved to real names. Every non-negotiable (pAI acknowledgement, `pAIMSc_2026` citation, the
watermark, the modular `\input{}` structure, bibliography-in-`references.bib`-only) survived the
cycle unchanged.

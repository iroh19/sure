# Editorial Contract — S.U.R.E. Applied-Systems Paper (Cycle 1)

Binding checklist applied at the end of every pass and again before Pass 5's compilation. Failing
any item here is a defect to fix before moving to the next pass, not a note for "later."

## Data-integrity gate (every numeric claim)
- [ ] Every number in the manuscript traces to a specific `experiment_workspace/experiment_runs/EXPnn/results.md`
      or a named raw JSON/log file inside that directory, or to `formalized_results.md/json`, or to
      `vision.md`'s explicitly locked figures. No number is invented, rounded differently than its
      source, or dropped.
- [ ] `vision.md`'s locked figures (mAP50 0.840, precision 0.858, recall 0.719, MRR 0.856, hit@1
      0.793, CoreML p50 9.0ms/p95 9.5ms, INT8 delta -0.0082) appear verbatim wherever cited as the
      headline/reported numbers; any re-derived value that differs in the last digit (e.g. 0.859
      raw-val()-output vs. 0.858 reported) is footnoted, not silently substituted.
- [ ] The 0.719-vs-0.782 recall distinction appears in the Abstract (both numbers, same sentence)
      and as a named Results callout — never only in a figure caption.
- [ ] The G5-corrected vision range (0.846-0.852 / 0.712 / 0.8335-0.8345) is never cited without
      "same-checkpoint re-evaluation, not a leakage-free retrain" in the same sentence.
- [ ] The adapter-provenance caveat is scoped to G3/EXP03 and its derivatives; it is never applied
      to G4/EXP04 anywhere in the manuscript.
- [ ] The live RAG 0.695 knowledge-base leak is stated as still unfixed, not implied to have been
      corrected by this paper.

## Voice gate (`author_style_guide.md` Part B)
- [ ] Exactly 3 surprise markers exist in the manuscript, at their specified locations; no fourth
      "surprisingly" has crept in elsewhere.
- [ ] The adapter-provenance sentence is never hedged or apologetic.
- [ ] No "Furthermore/Moreover/Additionally" chains; no "It is important to note that."
- [ ] Related Work is the cluster-A/pivot/cluster-B/cluster-C/novelty-locus structure, not a flat
      per-theme list.
- [ ] G9/twin_bridge is one paragraph inside a combined auxiliary-evidence subsection, not a named
      numbered subsection.

## Citation gate (Pass 5, before compiling)
- [ ] Every `\cite{key}` key exists in `references.bib` (grep-verified).
- [ ] Zero remaining `[cite: ...]` placeholders anywhere in `sections/*.tex`.
- [ ] `pAIMSc_2026` bib entry present verbatim; acknowledgements sentence present verbatim.

## Structural gate
- [ ] Section order matches `vision.md`'s mandated skeleton plus the council's additions
      (Discussion, Known Limitations, Appendix), assembled via modular `\input{}`, never a
      monolithic `final_paper.tex`.
- [ ] No inline `\begin{thebibliography}` anywhere.
- [ ] Watermark present and verified in the compiled PDF, not just in the source.

## Compilation gate (Pass 5/6)
- [ ] `pdflatex` + `bibtex` + `pdflatex` x2 all exit cleanly (or every remaining warning is
      triaged and judged non-blocking in `compilation_fix_plan.md`).
- [ ] `final_paper.pdf` exists with a page count consistent with an applied-systems conference/
      workshop paper (not 1 page, not 200 pages).

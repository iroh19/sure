# Research

[🇹🇷 Türkçe](README.tr.md)

The academic manuscript for S.U.R.E., and the complete record of how it was produced.

The paper was written with **pAI/MSc**, an agentic research pipeline from MIT
([Abdelmoneum, Beneventano & Poggio, 2026](https://dspace.mit.edu/handle/1721.1/165377)), with us as
humans on the loop. Every intermediate artifact that pipeline generated is committed here — not just
the finished paper.

## Start here

| | |
|---|---|
| 📄 **[SURE-paper.pdf](SURE-paper.pdf)** | The manuscript. 32 pages, 56 references, 5 figures. |
| 📘 **[SURE-research-process.pdf](SURE-research-process.pdf)** · [markdown](RESEARCH_PROCESS.md) | **How the research was actually done** — the pipeline, what the experiments found, and what we had to correct afterwards. |
| 📘 [SURE-arastirma-sureci.pdf](SURE-arastirma-sureci.pdf) · [markdown](RESEARCH_PROCESS.tr.md) | Turkish version of the above. |

## What's in here

```
research/
├── SURE-paper.pdf              the manuscript
├── SURE-research-process.pdf   how it was made (EN) — source: RESEARCH_PROCESS.md
├── SURE-arastirma-sureci.pdf   how it was made (TR) — source: RESEARCH_PROCESS.tr.md
├── paper/                      LaTeX source, section files, references.bib, figures
├── pipeline/                   the pAI/MSc run record
│   ├── research_task.md        the one-page brief we gave it
│   ├── vision.md               the frozen, read-only "vision lock"
│   ├── state.json              full phase history, gates, verdicts
│   ├── literature_review.md    31 citations, 11 of our claims falsified
│   ├── research_goals.json     11 pre-registered goals with fallback findings
│   ├── review_report.pdf       simulated peer review — scored 8/10
│   └── personas/               adversarial reviewer critiques, every round
└── experiments/                EXP01–EXP11: scripts, raw logs, results
    └── verification_report.md  independent recomputation — 8 PASS, 3 PARTIAL, 0 FAIL
```

## Three things worth knowing before you read the paper

**The scope is narrower than the system's name suggests.** S.U.R.E. has never run in a live
aquaculture facility. No physical sensor hardware exists; every sensor reading in every experiment is
synthetically generated. The 510-image vision dataset is real camera footage of the physical rig,
hand-labeled, but intentionally small. The contribution is a feasibility and resource-management
demonstration, not a field validation. This is stated in the paper's Introduction, Experimental
Setup, and Known Limitations.

**The central finding contradicts our original hypothesis.** We expected the deterministic rule
engine's value to come from catching the LLM's wrong calls. Measured (EXP03), it caught a genuine
under-call in 1 case out of 8 — while defaulting safe on unparseable model output in 4 of 8. The
dominant safety mechanism is fail-safe defaulting, not error correction. And 6 of 8 reasoning strings
contained fabricated sensor values that output-only evaluation cannot see.

**The pipeline found a real bug in this repository.** EXP11 flagged
`llm-service/knowledge/06-davranis-ve-refah-gostergeleri.md:58`, which still carries a superseded
recall figure (≈0.695) and *is* ingested into the RAG vector store — meaning retrieval can serve a
stale number. It is documented rather than silently fixed, because the audit ran under a read-only
guardrail.

## Rebuilding

```bash
cd research/paper
pdflatex final_paper.tex && bibtex final_paper && pdflatex final_paper.tex && pdflatex final_paper.tex
```

One artifact was omitted for size: `experiments/EXP05/near_duplicate_pairs_full.json` (2.4 MB). Its
aggregates and the script that produced it are committed.

## Attribution

The S.U.R.E. system is the authors' own work and predates the manuscript. The manuscript was produced
with pAI/MSc and cites it accordingly; the background watermark on each page of the PDF is part of
that tool's attribution requirement.

> Abdelmoneum, M., Beneventano, P., & Poggio, T. (2026). *pAI/MSc: ML Theory Research with Humans on
> the Loop.* MIT Technical Report v0. <https://dspace.mit.edu/handle/1721.1/165377>

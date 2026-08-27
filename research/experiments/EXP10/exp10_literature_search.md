# EXP10 — Supporting Artifact: Confirmatory Literature Search Log

Two searches run via WebSearch on 2026-08-26, per experiment_design.json step (1)'s suggested
query and its first named variant. (The second named variant, "deterministic safety layer
probabilistic AI industrial deployment," was folded into search 2 below alongside "cross-component
guardrail architecture empirical evaluation," since both target the same evidentiary question and
splitting them produced heavily overlapping result sets in a preliminary check.)

## Search 1

**Query:** `multi-layer AI governance case study deployed system deterministic override probabilistic components`

Top results and relevance assessment:

| Source | What it is | Relevance to C2 |
|---|---|---|
| [Deterministic governance for generative systems (Springer, *AI and Ethics*, 2026)](https://link.springer.com/article/10.1007/s43681-026-01172-6) | A "bounded deterministic arbitration kernel" that translates versioned policy constraints into machine-executable logic to make probabilistic-classifier moderation verdicts replayable. | **Closest single hit found in this search.** Same core mechanism class as C1 (deterministic arbitration over a probabilistic classifier) but scoped to *content-moderation verdicts*, singular-layer, and framed as a runtime/kernel proposal — no evidence in the abstract/summary that it is (a) applied across multiple architecturally distinct layers of one deployed system, or (b) empirically measured against a real production deployment with a disclosed negative result. Narrows C1 further (another equivalent-known instance) but does not touch C2's cross-layer claim. |
| [The CASE Framework (arXiv:2608.10153)](https://arxiv.org/html/2608.10153) | A "multi-disciplinary control architecture" for governing enterprise agentic AI, assigning four *different theoretical lenses* (control theory / complex adaptive systems / supervisory cybernetics / engineering ops) to four *organizational scales* (single agent / agent collective / human-agent team / fleet). | Superficially the closest "multi-layer" match by title, but the axis of decomposition is organizational scale and governance discipline, not architecturally distinct AI surfaces (LLM reasoning vs. retrieval vs. vision vs. MLOps) within one deployed system. No evidence of an empirical, single-deployed-system measurement with a disclosed negative result. Does not narrow C2. |
| [Governed Capability Evolution (arXiv:2604.08059)](https://arxiv.org/pdf/2604.08059) | Lifecycle-time compatibility checking / rollback for AI-component-based systems, embodied-agents case study. | Addresses a different problem (component version compatibility over time), not concurrent cross-layer override authority. Not a close match. |
| Elementum/Stonebranch/Mneme HQ blog posts | Practitioner content on deterministic-vs-probabilistic workflow design. | Reinforces that the *general pattern* (wrap probabilistic components in deterministic guardrails) is now common industry discourse — consistent with, not narrowing, novelty_flags.json's existing C1/EQUIVALENT_KNOWN finding. No cross-layer, single-deployed-system, multi-surface measurement claim in any of these. |

## Search 2

**Query:** `deterministic safety layer probabilistic AI industrial deployment cross-component guardrail empirical evaluation case study`

| Source | What it is | Relevance to C2 |
|---|---|---|
| [Position: A Three-Layer Probabilistic Assume-Guarantee Architecture (arXiv:2605.18672)](https://arxiv.org/pdf/2605.18672) | A position paper arguing a three-layer assume-guarantee architecture is *structurally required* for safe LLM agent deployment. | Closest architectural analogue found across both searches — three layers, LLM-agent-specific. But it is a **position/proposal paper**, not a measured deployed system, and its three layers are internal to one agent's control loop (not five architecturally distinct system surfaces spanning retrieval, MLOps, and vision as well as decision/agent layers). Does not report an empirical cross-layer measurement or a disclosed negative result. |
| [LLM-Guided Safety Agent for Edge Robotics, ISO-Compliant Perception-Compute-Control Architecture (arXiv:2604.20193)](https://arxiv.org/pdf/2604.20193) | A perception/compute/control layered safety agent for edge robotics, ISO-standard-aligned. | Domain-adjacent (edge deployment, vision-in-the-loop, layered architecture) but robotics-specific, and presented as a proposed architecture rather than a multi-layer empirical measurement study with a disclosed negative result across five distinct probabilistic surfaces. |
| Kong Inc. ("5 Layers for Reliability"), Galileo, DataCamp, Obsidian Security | Vendor/practitioner content on layered AI guardrail stacks. | Confirms defense-in-depth guardrail stacking is now conventional industry framing (further corroborates C1's EQUIVALENT_KNOWN status) but none present a measured, single-deployed-system, cross-architecturally-distinct-layer empirical study with a disclosed negative result. |
| [Robotics-Inspired Guardrails for Foundation Models (arXiv:2605.19940)](https://arxiv.org/pdf/2605.19940) | Applies robotics safety-envelope concepts to foundation-model guardrails in socially sensitive domains. | Conceptual transfer paper, not an empirical multi-layer deployed-system measurement. |

## Conclusion of the confirmatory search

**No source in either search is closer to C2 (the cross-layer claim) than literature_review_matrix.md's existing Theme 3 entries (11, 26, 12, 13, 14.1).** The single closest new hit for the *general* deterministic-override-of-probabilistic-component pattern (the Springer "Deterministic governance for generative systems" paper) narrows C1 further (yet another equivalent-known instance, in content moderation) but says nothing about cross-layer consistency across five architecturally distinct system surfaces within one deployed production system, nor about a disclosed negative result used as design evidence. The CASE framework and the assume-guarantee position paper are the closest "multi-layer" hits by keyword, but decompose the problem along different axes (organizational scale; single-agent internal control loop) than S.U.R.E.'s five-surface decomposition (LLM severity reasoning, agentic tool routing, RAG retrieval, MLOps retrain-gating, edge vision), and none are measured, deployed-system studies.

**Per experiment_design.json's own success criteria: this is the "Strong" outcome** — the search confirms medium-to-high confidence that no closer prior instance exists. novelty_flags.json's own caveat (confidence marked "medium," not "high," because web search cannot exhaustively rule out an unindexed or non-English prior system) still applies unchanged; this confirmatory pass does not have the power to elevate that to "high" confidence, only to fail to falsify it. **Recommendation: retain C2's novelty status as OPEN, confidence medium, exactly as novelty_flags.json already states — no narrowing forced by this search, no confidence upgrade earned by it either.**

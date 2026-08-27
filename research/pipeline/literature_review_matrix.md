# S.U.R.E. — Literature Review Citation Matrix

Maps each of the 6 themed literatures to the research_proposal.md question set (Central RQ, H1–H7), the papers found, their key findings, and the gap this S.U.R.E. paper's contribution addresses. Source IDs refer to `literature_review_sources.json`.

## Theme 1 — Precision aquaculture / RAS monitoring

| Question/Theme | Papers (id) | Key finding | Gap S.U.R.E. addresses |
|---|---|---|---|
| Central RQ (vision surface); H7 | 1 (Cui survey), 4 (YOLO-LD) | Fish CV is a mature taxonomy (FDR/FBE/FBC/FHA); RAS-specific YOLO variants report mAP50 up to 0.903, above S.U.R.E.'s 0.840 | S.U.R.E. is not a vision-accuracy contribution; must state honestly it is below at least one contemporaneous RAS-YOLO baseline, and position novelty in the decision-integration layer instead |
| Central RQ; H7 | 2 (Fitzgerald welfare review) | Field's own review states most vision systems never close the loop to an actionable, safety-graded decision | S.U.R.E.'s explicit trace from detection operating point to a consuming safety rule (`fish_count==0`) is exactly the closure this review says is missing |
| Sturgeon/RAS specificity (novelty check) | 6 (sturgeon CM-SCN) | Closest sturgeon-specific prior work is a lab stress-classification study, not a deployed decision system | Supports S.U.R.E. as a rare sturgeon-specific *deployed* welfare decision-support system |
| Motivation (DO-crash claim) | 29 (RAS DO threshold lit) | DO thresholds of 4.1–7.0 mg/L across species/temperature; rapid stock loss below threshold documented | Substantiates the "<6 mg/L kills within hours" motivating claim with independent literature; note species/temperature dependence |
| Related Work welfare-indicator framing | 30 (SWIM/FISHWELL/MyFishCheck) | Formal input-vs-outcome welfare-indicator taxonomy exists (SWIM, FISHWELL, MyFishCheck), none automated/real-time, none sturgeon-specific | S.U.R.E. can map its own sensor/vision signals onto this established taxonomy rather than inventing new terminology |
| Introduction economic framing | 27 (market reports) | Labor scarcity and automation ROI documented as adoption drivers (industry-report tier) | Supports but should be labeled as market-research, not academic, evidence |

**Unresolved gap this paper addresses:** no source integrates edge vision + LLM reasoning + deterministic safety authority in an aquaculture/RAS system, and none is sturgeon-specific at deployment scale; the field's own welfare-monitoring reviews explicitly flag the vision-to-decision closure gap S.U.R.E. fills.

## Theme 2 — Edge AI deployment for vision models

| Question/Theme | Papers (id) | Key finding | Gap S.U.R.E. addresses |
|---|---|---|---|
| H6 (export-format loss mechanism) | 8 (GitHub issues), 25 (ByteTrack) | NMS/post-processing does not export cleanly from PyTorch to ONNX/TensorRT — independently, informally documented by practitioners; ByteTrack recovers but does not eliminate occlusion-driven misses | H6's contribution is *quantifying and formally attributing* a mechanism the community already suspected, via a controlled same-validation-set, six-configuration sweep — methodological, not discovery-level, novelty |
| H6 (INT8 accuracy band) | 9 (TensorRT/INT8 quantization lit) | Typical calibrated INT8 costs 0.5–2.0pp (TensorRT) up to 3–7% (mAP50-95, less calibrated) | S.U.R.E.'s −0.0082 ΔmAP50 sits within/below this normal band — useful external reference point for Experimental Setup section |
| H6 / CoreML baseline | 7 (Ultralytics CoreML docs) | Vendor-reported YOLO-on-ANE reaches 60+ FPS on iPhone; establishes CoreML/ANE-YOLO as mainstream, not novel | S.U.R.E.'s 111 FPS/9.0ms on M4 Pro is plausible and consistent with, not anomalous relative to, vendor-reported order of magnitude |
| Architecture justification (on-prem/edge choice) | 10 (cloud vs edge inference) | Edge favored under sub-100ms latency or unreliable connectivity requirements; field agri-latency ~347-383ms (full round trip) | S.U.R.E.'s on-device figures measure only model inference, not network round-trip — must not be compared apples-to-oranges to field cloud-latency numbers |

**Unresolved gap this paper addresses:** holding the *entire* validation methodology constant across every export target in one controlled sweep, and separating fp32-export-path loss from quantization-added loss, is rarely done explicitly in the reviewed literature — this is H6's defensible methodological contribution.

## Theme 3 — LLM safety/guardrails in safety-critical & industrial systems (+ prior-art check)

| Question/Theme | Papers (id) | Key finding | Gap S.U.R.E. addresses / Novelty status |
|---|---|---|---|
| Central RQ; H1/H2 (deterministic final authority) | 11 (SIS), 26 (IEC 61508/61511) | SIS/interlock doctrine is a decades-old, industry-standard formalization of "deterministic layer has final override authority over an upstream layer" | **EQUIVALENT_KNOWN.** Must cite explicitly; S.U.R.E. is a software-only, LLM-mediated instantiation in a new domain, not an invented pattern. Independence is code-level (shared import), not IEC 61511's physical-independence criterion — a real architectural difference to state |
| H1/H2 boundary condition | 12 (RL shielding, Watchdogs & Oracles) | Shielding = runtime veto/correction of a probabilistic agent's proposed action before execution; shielding literature independently states it requires an enumerable/formal safety spec | **EQUIVALENT_KNOWN**, and independently corroborates H2's own scope limit (works for enumerable thresholds, not open-ended judgment) — cite as theoretical corroboration |
| Central RQ framing ("model proposes, rule disposes") | 13 (guardrail industry blogs) | 2025-2026 practitioner writing already uses near-identical framing/mechanism ("LLM generates → rules engine validates → deliver") | The refrain is *already circulating*; S.U.R.E.'s claim should be "a rare measured, deployed instance in a physical safety-critical domain," not "coined this pattern" |
| Central RQ; closest same-domain prior art | 14.1 (LLM industrial process control agents) | 2024-2025 academic work already proposes "every LLM proposal checked by an external validator before actuation" for industrial control | Closest same-domain-class prior art found; these are simulation/framework papers, not deployed+measured systems with a documented near-miss — S.U.R.E.'s empirical, deployed status is the differentiator |
| H2 contrast pattern | 14 (clinical HITL) | Clinical LLM safety dominantly uses human-in-the-loop, not deterministic code, as the backstop; residual hallucination rates remain non-trivial (~44% even with mitigation) | S.U.R.E. substitutes an always-available, code-tested deterministic backstop for the human-availability-constrained HITL pattern — relevant for 24/7 unattended deployment framing |

**Unresolved gap / honest novelty framing:** the override-authority *concept* is well-established (SIS, shielding, guardrail industry writing, nascent LLM-industrial-control academic work). S.U.R.E.'s defensible contribution is a **measured, deployed** instance of this pattern, applied to a local LLM, in a new domain (aquaculture RAS), with a documented near-miss (eval-harness drift) as motivating evidence — not the invention of deterministic override itself. This must be stated explicitly in Related Work and Introduction.

## Theme 4 — RAG systems and retrieval thresholding

| Question/Theme | Papers (id) | Key finding | Gap S.U.R.E. addresses |
|---|---|---|---|
| H4 (e5 vs tr-bert mechanism) | 15 (E5 paper) | Asymmetric query/passage-prefix training explains why e5-family models outperform symmetric sentence-similarity models as passage length grows | Explains, rather than merely reports, S.U.R.E.'s own e5-vs-tr-bert MRR gap (0.833→0.614) — cite as mechanism, not present as a novel discovery |
| H4 (threshold calibration) | 16 (threshold calibration lit) | No universal similarity threshold; must calibrate per-corpus against precision/recall or coverage target | Confirms S.U.R.E.'s explicit per-corpus scoping of its 0.85 threshold is the correct discipline, not an arbitrary choice |
| H4 (honest scope limit) | 17 (Semantic Illusion, HALT-RAG) | Formal limits exist on how much embedding-similarity thresholding alone can prevent hallucination | S.U.R.E. must not claim the 0.85 threshold eliminates hallucination risk — only reduces one specific failure mode (fabricated-context citation), consistent with H2's scope boundary |
| Chunking design choice | 18 (chunking strategy studies) | Structure-aware chunking reported to outperform naive fixed-width chunking in at least one comparative study | Supports heading-chunking choice as consistent with, not contrary to, emerging cross-domain findings |
| Metric choice grounding | 28 (RAG eval surveys) | MRR/hit@k are standard, established retrieval-evaluation metrics | S.U.R.E.'s contribution in this theme is entirely the calibration/thresholding step (H4), not the metric choice |

**Unresolved gap this paper addresses:** an explicit, disclosed asymmetric-cost threshold selection (hard-negative sweep + stated cost asymmetry, accepting F1 0.906 over the F1-optimal 0.951) for a specific high-stakes, small, single-language corpus — most cited threshold-calibration literature reports a chosen threshold without the same explicit cost-asymmetry justification.

## Theme 5 — LLM agentic tool-calling reliability

| Question/Theme | Papers (id) | Key finding | Gap S.U.R.E. addresses |
|---|---|---|---|
| H3 (field context) | 19 (SLM agentic survey) | SLM-agent tool-calling reliability is an active, contested, unresolved research area with mixed findings across studies | Positions AQUA-1B's 0%/0% result as a plausible, literature-consistent data point, not an outlier |
| H3 (direct corroboration) | 20 (Llama 3B benchmark, tool-environment unreliability paper) | Independent 2025-2026 benchmarks report comparably severe small-model (~1-3B) tool-calling failure | Materially strengthens H3's negative result as consistent with, not contradicted by, contemporaneous small-model benchmarks — but literature also contains counter-examples (schema-validated SLMs matching larger models), so claim must stay scoped to "AQUA-1B, this prompt, this scenario set" |
| H3 secondary claim (constant-answer artifact detection) | 21 (Artifacts or Abduction) | Majority-class/constant-answer benchmark artifacts are an established, named concern in NLP-benchmark literature (choices-only baselines, larger models exploiting artifacts more) | **PARTIAL, not OPEN**: the general principle is known; S.U.R.E.'s narrow instantiation (`len(set(chosen))==1` flag in an agentic tool-selection benchmark) is a novel application of a known principle to a new task type, not the invention of artifact-aware evaluation |

**Unresolved gap this paper addresses:** an evidence-driven (not precautionary) *abandonment* of LLM-based tool routing in a live production system, backed by a disclosed negative benchmark result and an artifact-aware evaluation check — most cited literature proposes evaluation frameworks or reports benchmark numbers without documenting a real system's design decision to switch to deterministic routing as a direct consequence.

## Theme 6 — MLOps drift detection (PSI)

| Question/Theme | Papers (id) | Key finding | Gap S.U.R.E. addresses / Novelty status |
|---|---|---|---|
| H5 (binning pitfall + fix) | 23 (PSI/binning literature) | Equal-width vs. quantile/equal-frequency binning distinction, and the warning that PSI is "sensitive to binning choices" and can be "inaccurate or misleading" under poor binning, is **already documented, standard PSI/credit-scoring practice** | **PARTIAL-to-KNOWN, not OPEN.** S.U.R.E.'s contribution is documenting this known failure mode concretely occurring in a new signal type (YOLO detection-confidence distributions, narrow-banded for different structural reasons than credit scores) and wiring the fix into an automated 3-way retrain-gate for a vision pipeline — narrower than "discovering" the binning pitfall |
| MIN_IMPROVEMENT retrain gate | 22 (champion-challenger MLOps) | Champion-challenger with a minimum-improvement promotion margin is standard, widely-documented MLOps practice (commonly ≥5% in industry sources vs. S.U.R.E.'s 0.005 mAP50 absolute) | **KNOWN.** Must cite champion-challenger explicitly; S.U.R.E. applies the standard pattern with a small, decision-theoretically justified margin to a vision-model registry, rather than inventing the gate concept |
| Drift-gated vs scheduled retraining | 24 (drift-triggered retraining lit) | Actively-discussed MLOps trade-off; hybrid (scheduled baseline + drift-triggered urgent path) is the converging recommendation; drift-triggered retraining's own limitation (fires only after degradation is detectable) is already documented | S.U.R.E.'s specific PSI-over-confidence-deciles + MIN_IMPROVEMENT combined pipeline for a vision-detection model is the concrete instantiation contributed, not the general drift-triggered-retraining concept |

**Unresolved gap this paper addresses:** despite the binning pitfall and champion-challenger gate both being individually known, no source found combines PSI-over-detection-confidence-deciles drift detection with a champion-challenger MIN_IMPROVEMENT gate specifically for a computer-vision detection model's MLOps registry — this specific combination, in this specific application (vision detector, not credit scorecard or tabular classifier), is the paper's honestly-scoped MLOps contribution.

---

## Cross-cutting summary for novelty framing

Three of the paper's four "deterministic authority" layer claims (H1/H2 core mechanism, H5 binning/gate, and the general override-authority concept) have **direct or equivalent prior art** once searched adversarially (SIS/IEC 61511, RL shielding, champion-challenger MLOps, PSI credit-scoring binning conventions). This is consistent with — and does not undermine — the proposal's own non-negotiable framing (vision.md; research_proposal.md Expected Contributions) that novelty is claimed at the level of **integration, measurement, and cross-layer consistency of a known design discipline applied to a new domain**, not invention of any individual mechanism. The literature review's role is to make sure the manuscript's Related Work section states this explicitly and cites the relevant prior art (SIS, shielding, champion-challenger, PSI-binning-best-practice, NLP-artifact-detection) rather than allowing the paper to read as if it invented "deterministic override of an LLM" as a concept.

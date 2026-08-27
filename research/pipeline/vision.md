# Vision Lock — project_000

> READ-ONLY. This file is the immutable reference for the researcher's original intent.
> The orchestrator must never overwrite or modify it after creation.
> Every persona reads this file before evaluating any proposal.

## Source

Captured from `/Users/batuhancitak/Desktop/sure-project/research_task.md` on 2026-08-26.

## Original Research Task (verbatim)

Project Title: S.U.R.E. (Aquaculture Welfare Integration): Autonomous Sturgeon Welfare Monitoring in Recirculating Aquaculture Systems via Edge-AI and RAG-Enhanced Deterministic Fusion

Authors: Batuhan Çıtak, Osman Enes Topcuoğlu, Halil İbrahim Şimşek, Erdem Sabri Veli, Ömer Sütçü, Zekeriya Ar, and Çağatay Oktay

Objective:
Act as a Principal Investigator and Research Writer. We have completely developed, deployed, and tested a real-time welfare monitoring system for sturgeons in Recirculating Aquaculture Systems (RAS). Your task is to write a comprehensive, publication-ready academic manuscript based on our implemented architecture, design decisions, and empirical results. You must contextualize our dual-layer AI safety approach (LLM + Deterministic Rule Engine) within the broader precision aquaculture literature.

System Architecture & Novel Contributions:
1. Dual-Layer Decision System (Safety Critical): Dissolved oxygen drops can kill stock within hours. Therefore, while we use a locally hosted LLM (AQUA-1B with a LoRA domain adapter) to reason over sensor data and behavior, the model never has the final word. A deterministic rule engine is the single source of truth. If the LLM misses a threshold, the rule engine escalates the severity.
2. Edge Vision Pipeline: The system runs YOLOv11s + ByteTrack for sturgeon detection and tracking.
3. Optimized Retrieval-Augmented Generation (RAG): We use pgvector and the `e5-small` embedding model with a heading-chunking strategy (MRR: 0.856, hit@1: 0.793) over 8 domain-specific documents. Tool routing is done via deterministic code rather than LLM reasoning to ensure reliability.
4. MLOps & Drift Detection: Built-in drift detection uses Population Stability Index (PSI) over detection confidence deciles to mathematically gate retraining phases rather than relying on arbitrary schedules.

Empirical Results to include and analyze:
- Vision Accuracy: YOLOv11s achieved an mAP50 of 0.840, precision of 0.858, and recall of 0.719 (trained on 510 labeled images, single class: sturgeon).
- Edge Performance: When exported to CoreML and run on Apple Neural Engine (ANE), the model achieved a p50 latency of 9.0 ms (111 FPS) and a p95 of 9.5 ms, vastly outperforming PyTorch/ONNX CPU exports and proving its viability for real-time edge deployment. INT8 quantization showed minimal mAP loss (-0.0082).
- RAG Efficiency: RAG thresholding optimized for an F1 score of 0.84, with production threshold set at 0.85 to favor precision over recall (preventing hallucinated citations).

Instructions for pAI:
- Structure the paper: Abstract, Introduction, Related Work, System Architecture (emphasizing the LLM vs. Rule Engine paradigm), Experimental Setup & Edge Metrics, Results, and Conclusion.
- Literature Review: Ground the paper in recent studies regarding precision aquaculture, RAS, edge AI deployment, and LLM safety/hallucination mitigation in critical industrial systems.
- Tone: Highly formal and analytical. Focus heavily on how the architecture explicitly solves the "LLM unreliability" problem in safety-critical agricultural deployments.

## User Directives Captured During Setup

- Mode: default (standard pipeline, no `--explore`).
- Workspace: `~/Desktop/Experiments/PoggioAI-results/project_000/` (created fresh; no prior PoggioAI pipeline run existed for this task).
- Initial context supplied: the SURE codebase's `README.md`, `MODEL_RAPORU.md`, `PLAN.md`, `TODOS.md`, and `research_task.md`, copied from `/Users/batuhancitak/Desktop/sure-project` into `initial_context/`. These describe the implemented system (backend, frontend, llm-service, vision-service, mlops, twin_bridge digital-twin bridge) that the paper must be grounded in — the manuscript must reflect this already-built and already-tested system, not a proposed one.
- Required paper structure (explicit skeleton, must be honored): Abstract, Introduction, Related Work, System Architecture (emphasizing the LLM vs. Rule Engine paradigm), Experimental Setup & Edge Metrics, Results, Conclusion.
- Required tone: highly formal and analytical, academic manuscript register.
- Central thesis to argue throughout: the dual-layer (LLM + deterministic rule engine) architecture explicitly solves the "LLM unreliability / hallucination" problem in safety-critical agricultural/industrial deployments — this framing should anchor Introduction, System Architecture, and Conclusion.
- Empirical results that MUST be included and correctly attributed (do not alter, round differently, or drop):
  - Vision: YOLOv11s, mAP50 = 0.840, precision = 0.858, recall = 0.719, trained on 510 labeled images, single class (sturgeon).
  - Edge/CoreML on Apple Neural Engine: p50 latency 9.0 ms (111 FPS), p95 latency 9.5 ms; INT8 quantization mAP loss of only -0.0082; CoreML/ANE vastly outperforms PyTorch/ONNX CPU exports.
  - RAG: pgvector + `e5-small` embeddings, heading-chunking strategy, MRR 0.856, hit@1 0.793, over 8 domain-specific documents; F1 optimized at 0.84; production similarity threshold set at 0.85 (favors precision over recall to prevent hallucinated citations).
  - MLOps: drift detection via Population Stability Index (PSI) over detection-confidence deciles, used to mathematically gate retraining rather than running on a fixed schedule.

## Non-negotiable framing

This is a systems/applied-AI paper about an already-deployed system, not a purely theoretical contribution. Novelty claims should center on the *integration pattern* (deterministic-final-authority safety gating around a local LLM, PSI-gated retraining, precision-tuned RAG for a safety-critical domain) rather than claiming invention of YOLOv11, ByteTrack, e5-small, or pgvector themselves.

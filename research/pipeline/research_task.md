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
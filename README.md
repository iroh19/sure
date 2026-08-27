# S.U.R.E. — Autonomous Sturgeon Welfare Monitoring

Real-time welfare monitoring for recirculating aquaculture (RAS): computer
vision, water-quality sensors and a locally hosted LLM behind a deterministic
safety net.

_Türkçe: [README.tr.md](README.tr.md)_

[![CI](https://github.com/iroh19/sure/actions/workflows/ci.yml/badge.svg)](https://github.com/iroh19/sure/actions/workflows/ci.yml)

**[Live demo →](https://iroh19.github.io/sure/)** — the dashboard replaying a
recorded session. GitHub Pages serves static files only, so nothing is inferred
in the browser; the sensors, detections, decisions and citations were all
produced by the real components and the page says so on its face. To run the
system for real: [![Open in Codespaces](https://img.shields.io/badge/Codespaces-open-24292e?logo=github)](https://codespaces.new/iroh19/sure)

**[Read the paper →](research/SURE-paper.pdf)** — 32 pages on the dual-layer
architecture, and [how it was researched](research/SURE-research-process.pdf)
_([Türkçe](research/SURE-arastirma-sureci.pdf))_. Everything behind it — eleven
experiments, raw logs, independent verification — is in [`research/`](research/).

| | |
|---|---|
| Detection | YOLOv11s · mAP50 **0.840** |
| Operating point | `conf=0.20` → precision **0.720** · recall **0.782** · F1 **0.750** |
| Dataset | 510 labelled images (412 train / 98 val), single class `sturgeon` |
| Tests | 18 unit + 22 knowledge-base + 48 agent + 32 MLOps + 19 twin-bridge + 8-scenario eval — all gate CI |
| Retrieval | pgvector · 8 docs / 44 chunks · MRR **0.856** · hit@1 **0.793** |
| LLM | AQUA-1B (Gemma 3 1B) · LoRA domain adapter · fully on-prem |

---

## The paper

[**`research/SURE-paper.pdf`**](research/SURE-paper.pdf) · 32 pages · 56 references · 5 figures

The architecture below is written up as an academic manuscript, produced with
[pAI/MSc](https://dspace.mit.edu/handle/1721.1/165377) — an agentic research
pipeline from MIT — with us on the loop. The long-form account of how that
worked is [`SURE-research-process.pdf`](research/SURE-research-process.pdf).

Writing it meant running eleven experiments against this codebase, and three of
them contradicted what this README used to say:

- **The rule engine rarely corrects the model.** It caught a genuine LLM
  under-call in 1 case out of 8. In 4 of 8 it defaulted safe because the model's
  output would not parse at all. The dominant safety mechanism is fail-safe
  defaulting, not error correction — and 6 of 8 reasoning strings fabricated
  sensor values that were never in the input, invisible to output-only checks.
- **The dual-layer design is not novel.** The adversarial literature pass
  classified it as the Safety Instrumented Systems pattern (IEC 61508/61511).
  The paper reframes the contribution around cross-layer consistency instead.
- **The recall we quoted is not the recall we run at.** The `conf=0.20` we
  actually ship gives recall 0.782 / precision 0.720. The 0.859 / 0.719 pair in
  `MODEL_RAPORU.md` is the F1-argmax optimum — correct, but a different question.

The whole trail is committed in [`research/`](research/): LaTeX source, the
eleven experiments with raw logs and scripts, the independent verification that
recomputed every headline number, and the full pipeline record.

> **Scope.** S.U.R.E. has never run in a live aquaculture facility. No physical
> sensor hardware exists, and every sensor reading in every experiment is
> synthetically generated. The 510-image dataset is real footage of the rig,
> hand-labelled, but intentionally small. The contribution is a feasibility and
> resource-management demonstration, not a field validation.

---

## The problem

Dissolved oxygen below 6 mg/L kills stock within hours. An LLM is genuinely
useful here — it reasons over sensor data and fish behaviour together and
explains itself in plain language — but **an LLM silently missing a
safety-critical threshold is not acceptable**.

So the model proposes and a deterministic rule engine disposes. When the model
says `ok` while `backend/rules.py` sees `critical`, severity is escalated and the
rule engine's reason is appended. Malformed output fails safe. If the LLM service
is down entirely, the decision still comes out of the rule engine.

## Design decisions

**The model never has the last word.** `rules.py` is the single source of truth
and imports no FastAPI, pydantic or httpx, so the backend and the eval harness
run the same code. Severity is only escalated, never lowered. The dashboard's
critical-DO banner is computed straight from the sensor and never touches the LLM.

**The eval measures production.** It used to carry its own copy of the rule
logic, and the copy had drifted: on `fish_count == 0` the copy said `warning`
while production said `ok` — green, and verifying nothing. The copy is gone.

**Thresholds have one source.** They lived in three places (rule engine,
knowledge base, system prompt), and hand-typed copies drift. The chain is now
`SYSTEM_PROMPT <- knowledge/*.md <- backend/rules.py`, held by 22 tests that were
mutation-checked: they fail on a changed bound, a changed severity and a deleted
document.

**Retrieval favours precision over recall**, and **tool routing is code rather
than the model** — both measured, both below.

---

## Architecture

```
vision-service ──POST /api/vision/ingest (~15 fps)──┐
  (YOLOv11 + ByteTrack)  ──POST /api/vision/frame───┤
                                                    ▼
sensor (mock CSV) ──2 s──────────► backend (FastAPI :8000)
                                     │  Store(deque 300) + SQLite
                                     │  GET /api/decision ─► llm-service :8001
                                     ▼                       (AQUA-1B, mlx/HF)
                                 frontend :5173 (React + Recharts)
```

| Service | Responsibility | Stack |
|---|---|---|
| `backend` | API, state fusion, rule engine, history | FastAPI |
| `llm-service` | Decision + chat (SSE), RAG, agent tools | AQUA-1B, mlx-lm / transformers |
| `vision-service` | Detection and tracking | YOLOv11, ByteTrack, OpenCV |
| `frontend` | Live dashboard | React 19, Vite, Tailwind, Recharts |
| `pgvector` | Knowledge-base vector store | PostgreSQL 17 + pgvector 0.8 |

On a `v*.*.*` tag the CD pipeline runs the quality gate first, and only then
builds and pushes to GHCR.

---

## Retrieval

Eight documents under `llm-service/knowledge/` (oxygen, temperature,
pH/alkalinity, nitrogen cycle, TDS, behaviour, emergency procedures, decision
logic) are indexed in pgvector. Evidence enters the prompt selected by whichever
parameter deviates, the model cites `[K1]`, `[K2]`, and sources are attached to
the decision so the UI can link back.

`rag/bench.py` compares 2 embedding models × 4 chunking strategies over 29
labelled queries. Metrics are document-level.

| Model | Strategy | Chunks | hit@1 | hit@3 | MRR | Context words | |
|---|---|--:|--:|--:|--:|--:|---|
| e5-small | fixed-480w | 8 | 0.862 | 0.897 | 0.900 | 1646 | narrow space, over budget |
| e5-small | fixed-240w | 16 | 0.759 | 1.000 | 0.868 | 922 | over budget |
| **e5-small** | **heading** | **44** | **0.793** | **0.931** | **0.856** | **317** | **chosen** |
| tr-bert | heading | 44 | 0.724 | 0.931 | 0.833 | 317 | |
| tr-bert | fixed-480w | 8 | 0.414 | 0.828 | 0.614 | 1646 | narrow space |

The top row was not chosen. `fixed-480w` produces one chunk per document, so at
k=5 it returns 62% of the corpus and hit@5 = 1.000 is arithmetic, not skill. It
also wants ~1646 words against a ~380-word prompt budget, so the measured score
is unreachable in production. `bench.py` flags both traps.

`e5-small` beats `tr-bert` under every strategy and the gap widens as chunks grow
(MRR 0.833 → 0.614): e5 is trained for asymmetric retrieval with
`query:`/`passage:` prefixes, while `tr-bert` is a sentence-similarity model and
long passages fall outside its training distribution.

**Threshold.** Bi-encoders return a nearest chunk for every query, including ones
the corpus cannot answer. `rag/calibrate.py` compares 29 positives against 12
hard negatives: positives score 0.841–0.892, negatives 0.813–0.847 — overlapping.

| Threshold | Positives kept | Negatives passed | F1 |
|---|--:|--:|--:|
| 0.84 | 29/29 | 3/12 | 0.951 |
| **0.85** | 24/29 | **0/12** | 0.906 |

F1 picks 0.84; we ship 0.85. The errors are not symmetric — a missed document
only weakens the reasoning and the rule engine still decides, while fabricated
context presents wrong information with a citation attached.

Retrieval is an enhancement, not a dependency: if pgvector is unreachable,
`retrieve()` returns nothing and the system carries on.

```bash
cd llm-service
python -m rag.ingest        # index the corpus
python -m rag.bench         # model × strategy
python -m rag.calibrate     # similarity threshold
```

---

## Agent

`agent/tools.py` defines three read-only tools (sensor trend, fish activity,
knowledge base) with JSON Schema validation and injected data access. No write
tools — the model gathers evidence, the rule engine decides and alarms.

`agent/loop.py` is a hand-written loop with a step budget, repetition detection,
tool errors fed back as observations, and a wall clock independent of the step
count. `generate` is injected, so 48 tests drive it with a scripted model and no
LLM at all.

`agent/bench_agent.py` then asked whether a real model can drive it:

| Model | Format | Selection | Steps | Time |
|---|--:|--:|--:|--:|
| AQUA-1B (Gemma 3 1B) | 0% | 0% | 0.0 | 2.7 s |
| AQUA-7B (Mistral, 4-bit) | 60% | 50% | 3.6 | 11.9 s |

AQUA-1B never emits a parseable action — it echoes the instruction or copies the
JSON template, and a prefill test produced identical output across four different
scenarios. The 7B model holds the format more often but chose `get_sensor_trend`
in **all five** scenarios: a constant answer, so its 50% is incidental.
`bench_agent.py` reports that as `CONSTANT ANSWER` rather than letting the
percentage flatter it.

`agent/router.py` ships instead: routing is deterministic code, the model only
narrates. Tools, validation and execution are shared with the loop; only the
planner differs. `loop.py` stays in the tree — if a tool-capable model appears,
the benchmark decides whether it earns its place.

---

## Edge export

`vision-service/export_bench.py` exports the detector to every format available
on the machine and runs each one through **the same 98-image validation split**
that produced the baseline. A speed number alone is not a result: every format
trades accuracy somewhere, and the trade is invisible unless both are measured.

Latency is p50/p95 over 40 real validation frames **decoded into memory first**,
with 8 warm-up runs discarded. Percentiles rather than a mean, because a
real-time pipeline is judged by its worst frames.

| Format | Device | mAP50 | ΔmAP50 | mAP50-95 | p50 ms | p95 ms | FPS | Size MB |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| pt | mps | 0.8395 | baseline | 0.5952 | 31.4 | 36.7 | 31.8 | 54.5 |
| pt | cpu | 0.8395 | +0.0000 | 0.5952 | 39.2 | 41.0 | 25.5 | 54.5 |
| onnx | cpu | 0.8291 | −0.0104 | 0.5867 | 53.5 | 66.1 | 18.7 | 36.2 |
| onnx-int8 | cpu | 0.8313 | −0.0082 | 0.5863 | 36.2 | 39.2 | 27.6 | **9.4** |
| **coreml** | ANE | 0.8298 | −0.0097 | 0.5840 | **9.0** | **9.5** | **111.2** | 18.2 |
| torchscript | cpu | 0.8291 | −0.0104 | 0.5867 | 52.8 | 54.8 | 18.9 | 36.4 |

**Export itself costs accuracy, before any quantisation.** fp32 ONNX and
TorchScript lose the same −0.0104 mAP50 and land on an identical mAP50-95 to four
decimals. Two different runtimes agreeing exactly means the loss is systematic,
not numerical noise — it comes from the post-processing path exported models
take, not from weight precision. "fp32 export is free" is wrong here.

**INT8 is nearly free, and beats fp32 ONNX.** 5.8× smaller at 9.4 MB, faster
(36.2 ms vs 53.5 ms) and with *less* loss (−0.0082 vs −0.0104). That does not
mean quantisation improves accuracy; read with the finding above, the loss lives
in the export path and INT8 noise happened to shift the operating point slightly
favourably. The difference is within noise.

**CoreML wins decisively on Apple Silicon.** 9.0 ms p50 (111 FPS), 3.5× faster
than PyTorch on MPS, 3× smaller, and the tightest p95 tail of any format (6% over
p50). ONNX has the worst tail at 24% — a gap the mean would hide.

**TensorRT is not measured.** It needs CUDA and cannot run on Apple Silicon.
`export_bench.py --emit-jetson` writes `jetson_bench.py`, which produces the FP16
and INT8 rows on the target device using identical methodology. No invented
TensorRT numbers are in the table.

```bash
cd vision-service
python export_bench.py                  # export and measure everything available
python export_bench.py --skip-export    # re-measure existing exports
python export_bench.py --emit-jetson    # write the Jetson-side script
```

---

## MLOps

Weights used to live in git and be told apart by filename. That held until the
report claimed epoch 73 while the shipped `best.pt` was epoch 77 — Ultralytics
selects by fitness (`0.1*mAP50 + 0.9*mAP50-95`), not by the headline metric. A
registry exists so that class of question is answerable rather than
archaeological.

`mlops/tracking.py --backfill` reads `results.csv` from the completed runs, so
the store holds real history from the first command instead of starting empty:

| run | metrics valid | best epoch | mAP50 | precision | recall |
|---|---|--:|--:|--:|--:|
| sure_v1 | yes | 77 | 0.8395 | 0.8583 | 0.7188 |
| ogretmen | **no** | 74 | 0.9254 | 0.8829 | 0.9073 |

The teacher run is logged *and* tagged invalid — it was trained and validated on
the same 20 frames, so its 0.925 measures memorisation. A registry that only
keeps the good runs cannot answer "why did we not ship that one".

### Drift

Labels do not exist in production, so drift is inferred from the model's own
output: **Population Stability Index** over the detection-confidence
distribution, against a reference captured on the validation set. Confidence
rather than fish count, because count is confounded — fewer detections may mean a
worse model or fewer fish.

The first implementation used ten equal-width bins over [0,1] and was useless
here. The detector's confidences sit in roughly 0.5–0.9, so six bins were empty
in the reference and any shift into one of them hit the empty-bin floor: PSI
jumped from 0.06 straight to 1.05 with nothing between, a binary alarm dressed as
a gradient. **Quantile edges** taken from the reference's own deciles give every
bin ~10% of the mass, and the signal grades:

| window | PSI | verdict |
|---|--:|---|
| two halves of the reference itself | 0.039 | none |
| 200 / 500 / 1000 real subsamples | 0.029 / 0.014 / 0.002 | none |
| 10% of detections degraded | 0.098 | none |
| 20% degraded | 0.265 | significant |
| confidence collapses to 0.1–0.4 | 8.28 | significant |

The first two rows are the ones that make the thresholds credible: a detector
that fires on a re-sample of its own calibration data makes every later alert
noise.

### Retraining is gated, not automatic

Drift says the world changed; it does not say a replacement would be better.

```
check_drift ──► decide ──┬─► none      stop
                         ├─► review    notify a human, stop
                         └─► retrain   train ─► evaluate ─► gate ─► register
```

A candidate ships only if it beats the incumbent by more than `MIN_IMPROVEMENT`
(0.005 mAP50). Training noise produces small positive deltas about half the time,
and shipping on those is a coin flip presented as a decision. Moderate drift
opens a review rather than firing a retrain, because retraining on every wobble
burns compute and risks fitting a noisy window.

The decision logic lives in `mlops/retrain.py` as plain functions with 32 tests;
`mlops/retrain_dag.py` is a thin Airflow wrapper that only schedules. Airflow is
not a project dependency — the DAG is meant to be dropped into a deployment.

```bash
python -m mlops.tracking --backfill      # log completed runs
python -m mlops.tracking --list
python -m mlops.drift --reference        # capture the reference distribution
python -m mlops.drift --check window.json
python -m mlops.retrain --check window.json
mlflow ui --backend-store-uri sqlite:///mlops/mlflow.db
```

---

## Verification

```bash
cd backend && python -m pytest test_decision.py -v      # 18 (1 skipped without torch)
python -m pytest llm-service/test_knowledge.py -v       # 22
python -m pytest llm-service/test_agent.py -v           # 48
python -m pytest twin_bridge -v                         # 19
cd llm-service && python eval.py --rule-only            # 8 scenarios
```

All four run in CI and nothing is built or published unless they pass. `eval.py`
exits `0` all passed, `1` a scenario failed, `2` model unavailable — in model
mode it never silently falls back to the rule engine.

One backend test imports `inference.py` and needs torch; it is skipped otherwise,
so CI reports **17 passed, 1 skipped**. Installing ~800 MB of torch in CI for one
test was a deliberate no.

Vision metrics and training notes: [`MODEL_RAPORU.md`](MODEL_RAPORU.md) _(Turkish)_.

---

## Quick start (macOS / Apple Silicon)

Docker Compose targets Linux + NVIDIA; on Apple Silicon run services natively.

```bash
brew install postgresql@17 pgvector && brew services start postgresql@17
createdb sure_rag && psql -d sure_rag -c "CREATE EXTENSION IF NOT EXISTS vector;"

cd llm-service && pip install -r requirements.txt
python -m rag.ingest
AQUA_ADAPTER_PATH=./sure-aqua-adapter uvicorn main:app --port 8001

cd backend && pip install -r requirements.txt && uvicorn main:app --port 8000
cd vision-service && pip install -r requirements.txt && python yolo_runner.py --source ../data/demo.MOV
cd frontend && npm install && npm run dev        # http://localhost:5173
```

Training and fine-tuning:

```bash
cd vision-service && python train_sure.py                    # YOLOv11s, 510 images
cd llm-service && python finetune.py --output ./adapter-v2   # LoRA; MLX or PEFT by device
```

## Configuration

| Variable | Default | Notes |
|---|---|---|
| `LLM_SERVICE_URL` | `http://localhost:8001` | |
| `BACKEND_URL` | `http://localhost:8000` | agent tools read history from here |
| `CORS_ORIGINS` | `*` | narrow for any public deployment |
| `DB_PATH` | `backend/sure_history.db` | |
| `AQUA_BASE_MODEL` | `KurmaAI/AQUA-1B` | the adapter was trained against 1B |
| `AQUA_ADAPTER_PATH` | _(empty)_ | not loaded when empty |
| `RAG_ENABLED` | `1` | `0` disables retrieval |
| `RAG_DATABASE_URL` | `postgresql:///sure_rag` | |
| `RAG_EMBED_MODEL` | `e5-small` | `e5-small` \| `tr-bert` |
| `RAG_CHUNK_STRATEGY` | `heading` | see the benchmark |
| `RAG_MIN_SIMILARITY` | `0.85` | recalibrate if the corpus changes |

## Layout

```
backend/          FastAPI, SQLite, tests
  rules.py        rule engine — single source of truth
llm-service/
  knowledge/      RAG corpus, 8 docs, thresholds in frontmatter
  rag/            chunking, embedding, pgvector, benchmark, calibration
  agent/          tools, loop, deterministic router, model benchmark
vision-service/   YOLO training + ByteTrack runner
frontend/         React dashboard
twin_bridge/      Modbus client for the digital twin + two-engine comparison
research/         the paper, its LaTeX source, and the full research record
```

Videos, dataset images and weights are excluded from git (see `.gitignore`) and
published via GitHub Releases.

Strings the model reads — the knowledge base, tool descriptions, prompts and
error messages — are Turkish, because the product answers in Turkish. Code,
comments and commits are English.

## Known limitations

- **Vision recall 0.782 at the threshold we ship** (`conf=0.20`), against a
  precision of 0.720. The 0.859 / 0.719 pair quoted in `MODEL_RAPORU.md` is the
  F1-argmax optimum and answers a different question. The fix for both is a
  larger dataset and retraining at `imgsz` 960/1280.
- **The validation set contains no sparse frames** (1–2 fish) — an untested
  regime, quantified in the paper.
- **32 near-duplicate frame pairs** between train and val, found by perceptual
  hash. Enumerated, not yet folded into a corrected headline metric.
- **The vector store has to be re-ingested when the corpus changes.** A
  superseded recall figure sat in `knowledge/06-davranis-ve-refah-gostergeleri.md`
  for a day before EXP11 found it — corrected in the source and re-ingested, but
  nothing enforces that the index matches the files on disk.
- **TensorRT rows are unmeasured** — no CUDA device available yet.
- **AQUA-1B has never been run through the eval in model mode**; `--rule-only`
  verifies the rule engine, not the model.
- **The LoRA adapter may still be the 8-sample v1**; v2 (128 samples) is pending.
- **The dashboard does not render `sources` yet** — citations reach
  `/api/decision` but are not displayed.

Out of scope: real sensor hardware, authentication, multi-tank, alerting.

---

_Built for the TEKNOFEST Agricultural Technologies competition._

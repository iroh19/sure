# EXP04 — Agentic Tool-Routing Reproduction, Constant-Answer Audit, and Scenario Expansion

**Status:** success (strong criterion met — fresh re-run on both models, constant-answer audit against the real per-scenario log, ≥4 new scenarios authored and run on both models)
**Sample size achieved:** n=9 scenarios (5 original + 4 new) × 2 models (AQUA-1B, AQUA-7B) = 18 agent runs, each a genuinely independent input (no `--repeat`, no byte-identical reruns).
**Environment:** `/opt/anaconda3/bin/python3`, run from `llm-service/`. AQUA-7B 1-scenario timing dry run: 27.9s (incl. ~10-15s model load) — well inside budget, so the full 9-scenario × 2-model matrix was run in full without subsampling. Total wall time: AQUA-1B ~16s for 9 scenarios; AQUA-7B ~125s for 9 scenarios.

## Open decisions resolved

1. **`--repeat N` is not a sample-size increase**: confirmed directly in `make_generator()`'s `generate()` — `inference._generate(prompt, temp=0.0, ...)`, greedy decoding — repeats are byte-identical. This experiment used 4 genuinely new `Scenario` fixtures instead (`new_scenarios.py`), not `--repeat`.
2. **`AQUA_ADAPTER_PATH`**: left **unset** (base model). `bench_agent.py`'s own docstring frames the question as whether "a real model" / "the model" can drive the closed-menu loop, with no "+adapter" framing anywhere in its code, output table, or the README's published results — unlike `eval.py`'s context, which explicitly says "AQUA-1B + LoRA adapter." No shell history, run log, or comment anywhere in the repo indicates the adapter was set for the original benchmark. This reproduction matches that condition.
3. **`PLAN_MAX_TOKENS`**: read directly from `agent/loop.py` — 48 tokens, `MAX_STEPS=4`, `MAX_SECONDS=45.0`. Confirmed small and unlikely to cause the "half an hour" pathology the docstring warns about (that failure mode is specifically about the 512-token *narration* budget leaking into planning calls, which does not happen here — `PLAN_MAX_TOKENS` is used correctly in `make_generator`).

## The 4 new scenarios

Authored in `new_scenarios.py` using the unmodified `Scenario`/`StaticDataSource`/`_falling`/`_vision`/`_sensors` helpers from `bench_agent.py` (imported, not copied):

- **A. "temperature rising, DO fine"** — rising trend on a *different* parameter than the original "oxygen falling" case, to check the model isn't just pattern-matching "a trend exists → get_sensor_trend" regardless of which parameter.
- **B. "pH improving, not degrading"** — current reading borderline-low (like "pH at the edge") but the *trend* is recovering upward — tests whether tool choice reflects the snapshot alone or genuine trend-seeking.
- **C. "low activity + falling TDS"** — combines a vision-only cue and a sensor-only cue in one scenario (the original 5 only ever present one at a time).
- **D. "borderline but safe on all axes"** — restraint test like "everything normal," but every parameter sits close to (not comfortably inside) its safe-range edge.

## Step 1 & 2 — Reproduction + constant-answer audit (original n=5)

| Model | Format | Selection | Mean steps | Mean seconds | Constant answer |
|---|--:|--:|--:|--:|:--:|
| AQUA-1B | **0%** (0/5) | **0%** (0/4 scored) | 0.0 | 2.2s | false (no tool ever emitted) |
| AQUA-7B | **100%** (5/5) | **50%** (2/4 scored) | 2.0 | 14.6s | **true** — `get_sensor_trend` in all 5 |
| *README (published, historical)* | *AQUA-1B 0% / AQUA-7B 60%* | *AQUA-1B 0% / AQUA-7B 50%* | *AQUA-7B 3.6* | *AQUA-7B 11.9s* | *AQUA-7B: constant answer, all 5* |

**Constant-answer audit (against the real per-scenario `tool=` log, not just the aggregate):** verified directly in `aqua7b_results.jsonl` / `aqua7b_stdout.log` — AQUA-7B's `first_tool` is `get_sensor_trend` in **every single one** of the 5 original scenarios, including "fish inactive, sensors normal" and "no fish detected," where `get_sensor_trend` is *not* in the acceptable set (it should have called `get_fish_activity`). The 50% selection figure is confirmed to be exactly the artifact the flag says it is: 2 of 4 scored scenarios happen to accept `get_sensor_trend`, and the other 2 don't, purely by chance of which tool the model always emits — not because it discriminated between them.

**Honest discrepancy vs. the published README table:** selection% (50%) and the constant-answer finding reproduce **exactly**. Format compliance and mean-steps do **not** reproduce exactly: this re-run measured AQUA-7B at 100% format / 2.0 mean steps, vs. the published 60% / 3.6 mean steps. Mean duration is close (14.6s vs. 11.9s). No config difference was found to explain this (adapter unset in both, `PLAN_MAX_TOKENS`/`MAX_STEPS` unchanged in the current code) — the most likely explanation is drift in the `mlx-lm`/model-serving stack or a HF revision update between whenever the original README table was produced and this run (git blame on the README table itself was not checked further, out of this experiment's scope). This is reported as a disclosed discrepancy, not silently smoothed into "reproduced."

## Step 3 & 4 — Expanded set (n=9: 5 original + 4 new)

| Model | Format | Selection | Mean steps | Mean seconds | Constant answer |
|---|--:|--:|--:|--:|:--:|
| AQUA-1B | **0%** (0/9) | **0%** (0/7 scored) | 0.0 | 1.7s | false |
| AQUA-7B | **100%** (9/9) | **71.4%** (5/7 scored) | 2.0 | 13.9s | **true** — `get_sensor_trend` in all 9 |

**The negative result is preserved, not softened, by growing the scenario set to n=9 — and the constant-answer finding gets meaningfully stronger evidence, not just a repeated one.** AQUA-1B's 0%/0% failure holds identically on all 4 new, never-before-seen scenarios. AQUA-7B chose `get_sensor_trend` as its **first tool in all 9 of 9 genuinely distinct scenarios** — including scenario C (low activity + falling TDS, where `get_fish_activity` was an equally defensible first move) and scenario D (borderline-but-safe, a restraint scenario where the "correct" answer is arguably no tool at all). This is now evidence from 9 independent samples, not 5, that AQUA-7B is emitting a constant, not discriminating.

**Honest caveat on the raw selection% number:** selection accuracy nominally rose from 50% to 71.4% on the expanded set. This is **not** evidence of better discrimination — it is a direct consequence of 3 of the 4 new scenarios (A, B, and partially C) being sensor-trend-relevant by design (following the original 5's own style, which already skews toward `get_sensor_trend`/`query_knowledge_base` as acceptable answers in 3 of 4 scored original scenarios too). A model that always says the same word will score well on any test whose answer key frequently contains that word — this is the exact hazard `bench_agent.py`'s own constant-answer flag exists to catch, and it correctly fires here (`constant_answer: true`) despite the higher raw selection score. The constant-answer flag, not the selection percentage, is the metric that should be quoted in the manuscript.

## Precision Check note (citing source 21)

> The constant-answer-detection technique used here and by `bench_agent.py` — flagging a headline accuracy number as an artifact when the underlying answer distribution has near-zero entropy (`len(set(chosen)) == 1` across ≥3 independent trials) — is a known-artifact-detection principle applied to a new task, not a novel contribution of this work. It mirrors findings in the multiple-choice-QA literature that LLMs can score well above chance on an evaluation while relying on answer-distribution artifacts rather than genuine task-relevant discrimination (source 21, "Artifacts or Abduction"). This experiment's contribution is applying that same discipline to closed-menu tool-selection benchmarking for small local models, and confirming — with 4 newly-authored, genuinely independent scenarios beyond the original 5 — that the artifact is not a small-sample fluke: AQUA-7B's constant answer persists identically across 9/9 scenarios.

## Success criteria assessment

- Fresh re-run on both models: done (AQUA-1B 0%/0%, AQUA-7B 100%/50% on original n=5 — selection% and constant-answer match published figures exactly; format%/mean-steps disclosed as a discrepancy).
- Constant-answer audit against real per-scenario log: done, confirmed genuine (not a coincidence of aggregate math).
- ≥4 new scenarios authored, full benchmark re-run on both models: done (4 authored, 9-scenario × 2-model matrix run in full, no subsampling needed).
- Source 21 cited to scope the novelty claim: done.
- `--repeat N` explicitly stated as not a sample-size increase: done (open_decision #1 above).

## Files
- `new_scenarios.py` (4 new Scenario fixtures)
- `run_bench.py` (runner, writes incrementally)
- `aggregate.py`, `aggregate_output.log` (before/after comparison)
- `aqua1b_results.jsonl`, `aqua1b_stdout.log`
- `aqua7b_results.jsonl`, `aqua7b_stdout.log`

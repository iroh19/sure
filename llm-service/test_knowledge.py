"""
Knowledge base <-> rule engine consistency.

Thresholds in the RAG corpus must match `SAFE` in `backend/rules.py` exactly.

This is the same class of bug `eval.py` once had: a copy of the rule logic that
drifted from production, leaving the eval green while verifying nothing. Here the
failure is nastier — if the corpus says oxygen is safe above 5 mg/L, the model
quotes that sentence as justification while the rule engine applies 6.0, and the
operator watches the system contradict itself.

Two hand-written copies can always drift. These tests are what stops them.

    python -m pytest llm-service/test_knowledge.py -v

Only needs pytest — no torch, psycopg or sentence-transformers.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import rules  # noqa: E402
from rag.chunk import STRATEGIES, chunk_document, load_documents  # noqa: E402

DOCS = load_documents()
PARAM_DOCS = [d for d in DOCS if "parameter" in d.meta]


# ── Threshold consistency ────────────────────────────────────────────────────

def test_knowledge_base_is_not_empty():
    assert len(DOCS) >= 5, "corpus too small for retrieval to mean anything"


@pytest.mark.parametrize("doc", PARAM_DOCS, ids=lambda d: d.doc_id)
def test_documented_thresholds_match_rule_engine(doc):
    """Documented bounds must equal rules.SAFE."""
    param = doc.meta["parameter"]

    if param == "avg_activity":
        # Activity is one-sided: below rules.MIN_ACTIVITY raises a warning.
        documented = float(doc.meta["activity_min"])
        assert documented == rules.MIN_ACTIVITY, (
            f"{doc.path.name}: aktivite eşiği {documented}, "
            f"rules.MIN_ACTIVITY {rules.MIN_ACTIVITY}"
        )
        return

    assert param in rules.SAFE, (
        f"{doc.path.name}: '{param}' rules.SAFE içinde yok. "
        f"Bilinen parametreler: {sorted(rules.SAFE)}"
    )
    lo, hi = rules.SAFE[param]
    assert float(doc.meta["safe_min"]) == lo, f"{doc.path.name}: safe_min ≠ rules.SAFE[{param}][0]"
    assert float(doc.meta["safe_max"]) == hi, f"{doc.path.name}: safe_max ≠ rules.SAFE[{param}][1]"


@pytest.mark.parametrize("doc", PARAM_DOCS, ids=lambda d: d.doc_id)
def test_documented_severity_matches_critical_key(doc):
    """Only the CRITICAL_KEY parameter may be documented as critical."""
    param = doc.meta["parameter"]
    documented = doc.meta.get("severity")
    expected = "critical" if param == rules.CRITICAL_KEY else "warning"
    assert documented == expected, (
        f"{doc.path.name}: severity '{documented}' yazılmış ama kural motoruna göre "
        f"'{expected}' olmalı (CRITICAL_KEY={rules.CRITICAL_KEY})"
    )


def test_every_sensor_parameter_is_documented():
    """Every parameter in rules.SAFE needs a document.

    Add a sensor parameter without a doc and retrieval returns nothing about it,
    leaving the model free to invent.
    """
    documented = {d.meta["parameter"] for d in PARAM_DOCS}
    missing = set(rules.SAFE) - documented
    assert not missing, f"Bu parametreler için bilgi tabanı dokümanı yok: {sorted(missing)}"


def test_threshold_values_appear_in_prose():
    """The number must appear in the prose, not only in frontmatter.

    Retrieval returns the body; frontmatter never reaches the model.
    """
    for doc in PARAM_DOCS:
        if doc.meta["parameter"] == "avg_activity":
            needles = [doc.meta["activity_min"]]
        else:
            needles = [doc.meta["safe_min"], doc.meta["safe_max"]]
        for needle in needles:
            # "6.0" may be written as "6.0" or "6" in the body.
            trimmed = needle.rstrip("0").rstrip(".")
            assert needle in doc.body or trimmed in doc.body, (
                f"{doc.path.name}: '{needle}' eşiği gövde metninde geçmiyor"
            )


# ── Chunking sanity ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("strategy", STRATEGIES)
def test_every_strategy_produces_nonempty_chunks(strategy):
    for doc in DOCS:
        chunks = chunk_document(doc, strategy)
        assert chunks, f"{doc.doc_id} / {strategy}: hiç chunk üretilmedi"
        for c in chunks:
            assert c.content.strip(), f"{doc.doc_id} / {strategy}: boş chunk"


def test_fixed_strategy_respects_size_bound():
    """fixed-<N>w must not exceed N words plus the title prefix."""
    for doc in DOCS:
        for size in (120, 240, 480):
            for c in chunk_document(doc, f"fixed-{size}w"):
                # Title prefix is included, so allow headroom.
                assert c.word_count <= size + 20, (
                    f"{doc.doc_id}: chunk {c.chunk_index} = {c.word_count} kelime, "
                    f"sınır {size}"
                )


def test_chunk_indices_are_unique_per_document():
    for strategy in STRATEGIES:
        for doc in DOCS:
            idx = [c.chunk_index for c in chunk_document(doc, strategy)]
            assert len(idx) == len(set(idx)), f"{doc.doc_id} / {strategy}: tekrarlı chunk_index"


# ── Derived system prompt ────────────────────────────────────────────────────
# SYSTEM_PROMPT does not hard-code thresholds; it derives them from knowledge/
# frontmatter, which the tests above tie to rules.py:
#     SYSTEM_PROMPT <- knowledge/*.md <- backend/rules.py
# These verify the last link.

def test_rendered_safe_ranges_contain_every_rule_engine_bound():
    from rag.thresholds import render_safe_ranges

    rendered = render_safe_ranges()
    for param, (lo, hi) in rules.SAFE.items():
        for bound in (lo, hi):
            # 6.0 -> "6.0", 200.0 -> "200"
            text = f"{bound:.1f}" if bound < 100 else str(int(bound))
            assert text in rendered, (
                f"bound {text} for {param} missing from rendered block:\n{rendered}"
            )


def test_rendered_safe_ranges_marks_only_the_critical_parameter():
    from rag.thresholds import critical_parameter, render_safe_ranges

    assert critical_parameter() == rules.CRITICAL_KEY
    assert render_safe_ranges().count("KRİTİK") == 1, (
        "exactly one parameter must be marked critical"
    )


def test_rendered_safe_ranges_include_activity_threshold():
    from rag.thresholds import render_safe_ranges

    assert str(rules.MIN_ACTIVITY) in render_safe_ranges()

"""
Single source for the safe ranges, on the llm-service side.

The "GÜVENLİ ARALIKLAR" block in the system prompt is derived from knowledge-base
frontmatter, never typed by hand.

Thresholds used to live in three places — `backend/rules.py`, `knowledge/*.md`
and `SYSTEM_PROMPT`. Three hand-typed copies drift, and the drift is silent in
the worst way: the model cites a stale threshold while the rule engine applies
the current one.

The llm-service image does not contain `backend/rules.py` (the Docker build
context is this directory), so the prompt cannot read the rule engine directly.
It can read `knowledge/`, and `test_knowledge.py` ties the knowledge base to the
rule engine, which closes the chain:

    SYSTEM_PROMPT  <-  knowledge/*.md  <-  backend/rules.py
"""
from __future__ import annotations

from dataclasses import dataclass

from .chunk import load_documents

# Human-readable labels for the prompt. Turkish because the prompt is Turkish.
LABELS: dict[str, tuple[str, str]] = {
    "dissolved_oxygen_mgl": ("Çözünmüş Oksijen (DO)", "mg/L"),
    "temperature_c": ("Sıcaklık", "°C"),
    "ph": ("pH", ""),
    "tds_ppm": ("TDS", "ppm"),
}

# Oxygen first — it is the only critical parameter.
ORDER = ("dissolved_oxygen_mgl", "temperature_c", "ph", "tds_ppm")


@dataclass(frozen=True)
class Threshold:
    parameter: str
    lo: float
    hi: float
    severity: str


def load_thresholds() -> dict[str, Threshold]:
    out: dict[str, Threshold] = {}
    for doc in load_documents():
        param = doc.meta.get("parameter")
        if not param or param == "avg_activity":
            continue
        out[param] = Threshold(
            parameter=param,
            lo=float(doc.meta["safe_min"]),
            hi=float(doc.meta["safe_max"]),
            severity=doc.meta.get("severity", "warning"),
        )
    return out


def load_activity_min() -> float | None:
    for doc in load_documents():
        if doc.meta.get("parameter") == "avg_activity":
            return float(doc.meta["activity_min"])
    return None


def _fmt(value: float) -> str:
    """Below 1, significant digits (0.002); below 100, one decimal (6.0); above,
    integer (200). The decimal keeps threshold precision visible where half a
    unit matters, as it does for oxygen."""
    if value < 1:
        return f"{value:g}"
    if value < 100:
        return f"{value:.1f}"
    return str(int(round(value)))


def render_safe_ranges() -> str:
    thresholds = load_thresholds()
    lines = ["GÜVENLİ ARALIKLAR:"]

    ordered = [p for p in ORDER if p in thresholds]
    ordered += [p for p in sorted(thresholds) if p not in ORDER]

    for param in ordered:
        t = thresholds[param]
        label, unit = LABELS.get(param, (param, ""))
        suffix = f" {unit}" if unit else ""
        line = f"- {label}: {_fmt(t.lo)}-{_fmt(t.hi)}{suffix}"
        if t.severity == "critical":
            line += f"  →  <{_fmt(t.lo)} = KRİTİK"
        lines.append(line)

    activity = load_activity_min()
    if activity is not None:
        lines.append(f"- avg_activity <{_fmt(activity)} → hareketsizlik/stres şüphesi")

    return "\n".join(lines)


def critical_parameter() -> str | None:
    for param, t in load_thresholds().items():
        if t.severity == "critical":
            return param
    return None

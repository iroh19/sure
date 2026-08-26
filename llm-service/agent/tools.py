"""
Tool layer for the agent.

A tool is a schema the model reads, a function that runs, and validation between
them. No LLM in this file — tools are plain functions and are tested without a
model, so a bad output can be attributed to the tool or the model, not both.

Three decisions worth knowing:

* `description` is prompt engineering, not documentation. The model picks a tool
  by reading it, so it is written for the model and stays in Turkish along with
  every other string that reaches the model.
* Tools compress. Returning 300 raw readings burns the prompt budget and gives a
  1B model something it cannot reason over; a tool returns the sentence a person
  would say out loud.
* Every tool is read-only. The model gathers evidence; `backend/rules.py` decides
  and raises alarms. A write tool would need a deterministic gate or human
  approval in front of it.

Data access is injected (`DataSource`) so tools run against fixtures in tests and
HTTP in production.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Any, Callable, Protocol


class DataSource(Protocol):
    def sensor_history(self) -> list[dict]: ...
    def vision_history(self) -> list[dict]: ...


@dataclass
class StaticDataSource:
    """In-memory source for tests and offline runs."""
    sensor: list[dict]
    vision: list[dict]

    def sensor_history(self) -> list[dict]:
        return self.sensor

    def vision_history(self) -> list[dict]:
        return self.vision


class HttpDataSource:
    """Reads history from the backend, caching one fetch per agent turn."""

    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._cache: dict | None = None

    def _fetch(self) -> dict:
        if self._cache is None:
            import httpx

            resp = httpx.get(f"{self.base_url}/api/history", timeout=self.timeout)
            resp.raise_for_status()
            self._cache = resp.json()
        return self._cache

    def invalidate(self) -> None:
        self._cache = None

    def sensor_history(self) -> list[dict]:
        return self._fetch().get("sensor") or []

    def vision_history(self) -> list[dict]:
        return self._fetch().get("vision") or []


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict          # JSON Schema
    fn: Callable[..., str]
    read_only: bool = True


class ToolError(Exception):
    """Tool could not run. Fed back to the model as an observation."""


def _tail(rows: list[dict], count: int) -> list[dict]:
    # Sampling is a fixed 2 s, so a record count converts directly to minutes.
    # Switch to timestamp filtering if the interval ever becomes variable.
    return rows[-count:] if count < len(rows) else list(rows)


def _direction(values: list[float]) -> str:
    """Compare the two halves of the window.

    A regression slope would be more elegant and buys nothing: the model gets a
    label, not a coefficient. The 0.15 band keeps noise from reading as trend.
    """
    if len(values) < 4:
        return "belirsiz"
    mid = len(values) // 2
    first, second = statistics.fmean(values[:mid]), statistics.fmean(values[mid:])
    span = max(values) - min(values)
    if span == 0:
        return "sabit"
    delta = (second - first) / span
    if delta > 0.15:
        return "yükseliyor"
    if delta < -0.15:
        return "düşüyor"
    return "sabit"


SENSOR_PARAMS = {
    "dissolved_oxygen_mgl": ("çözünmüş oksijen", "mg/L"),
    "temperature_c": ("sıcaklık", "°C"),
    "ph": ("pH", ""),
    "tds_ppm": ("TDS", "ppm"),
}


def get_sensor_trend(source: DataSource, parameter: str, minutes: int = 30) -> str:
    if parameter not in SENSOR_PARAMS:
        raise ToolError(
            f"'{parameter}' geçerli bir parametre değil. "
            f"Seçenekler: {', '.join(SENSOR_PARAMS)}"
        )
    minutes = max(1, min(int(minutes), 120))
    rows = _tail(source.sensor_history(), minutes * 30)
    values = [r[parameter] for r in rows if isinstance(r.get(parameter), (int, float))]

    if not values:
        return f"{SENSOR_PARAMS[parameter][0]} için kayıt yok."

    label, unit = SENSOR_PARAMS[parameter]
    birim = f" {unit}" if unit else ""
    return (
        f"{label}: son {minutes} dakikada {len(values)} ölçüm. "
        f"İlk {values[0]:.2f}{birim} → son {values[-1]:.2f}{birim}. "
        f"En düşük {min(values):.2f}, en yüksek {max(values):.2f}, "
        f"ortalama {statistics.fmean(values):.2f}{birim}. "
        f"Eğilim: {_direction(values)}."
    )


def get_fish_activity(source: DataSource, minutes: int = 30) -> str:
    minutes = max(1, min(int(minutes), 120))
    rows = _tail(source.vision_history(), minutes * 15)
    counts = [r["fish_count"] for r in rows if isinstance(r.get("fish_count"), int)]
    acts = [r["avg_activity"] for r in rows if isinstance(r.get("avg_activity"), (int, float))]

    if not counts and not acts:
        return "Görüntü işleme kaydı yok — vision servisi bağlı olmayabilir."

    parts = [f"Görüntü: son {minutes} dakikada {len(rows)} kare."]
    if counts:
        parts.append(
            f"Balık sayısı ortalama {statistics.fmean(counts):.1f} "
            f"(en az {min(counts)}, en çok {max(counts)}), "
            f"eğilim {_direction([float(c) for c in counts])}."
        )
        if min(counts) == 0:
            sifir = sum(1 for c in counts if c == 0)
            parts.append(f"UYARI: {sifir} karede hiç balık tespit edilmedi.")
    if acts:
        parts.append(
            f"Ortalama hareket {statistics.fmean(acts):.4f} "
            f"(en düşük {min(acts):.4f}), eğilim {_direction(acts)}."
        )
    return " ".join(parts)


def query_knowledge_base(source: DataSource, query: str) -> str:
    """Exposes the RAG layer as a tool the model can call on demand."""
    from rag.retriever import build_context, retrieve

    hits = retrieve(query)
    if not hits:
        return (
            "Bilgi tabanında bu konuda yeterince yakın bir kayıt yok. "
            "Bu soruyu bilgi tabanına dayanarak yanıtlama."
        )
    context, sources = build_context(hits, max_chars=1200)
    etiketler = ", ".join(f"{s['marker']}={s['doc_id']}" for s in sources)
    return f"Bilgi tabanı ({etiketler}):\n{context}"


# Schemas are JSON Schema so switching to a hosted tool-calling API later is a
# transport change, not a rewrite.
TOOLS: dict[str, Tool] = {
    "get_sensor_trend": Tool(
        name="get_sensor_trend",
        description=(
            "Bir su kalitesi parametresinin son N dakikadaki eğilimini özetler. "
            "Değerin yükselip düşmediğini anlamak için kullan. Anlık değer zaten "
            "elinde — bu araç TRENDİ verir."
        ),
        parameters={
            "type": "object",
            "properties": {
                "parameter": {"type": "string", "enum": list(SENSOR_PARAMS)},
                "minutes": {"type": "integer", "default": 30},
            },
            "required": ["parameter"],
        },
        fn=get_sensor_trend,
    ),
    "get_fish_activity": Tool(
        name="get_fish_activity",
        description=(
            "Balık sayısı ve hareketliliğinin son N dakikadaki seyrini özetler. "
            "Sensörler normal görünürken balıkta sıkıntı olup olmadığını anlamak "
            "için kullan; davranış çoğu zaman sensörden önce bozulur."
        ),
        parameters={
            "type": "object",
            "properties": {"minutes": {"type": "integer", "default": 30}},
            "required": [],
        },
        fn=get_fish_activity,
    ),
    "query_knowledge_base": Tool(
        name="query_knowledge_base",
        description=(
            "RAS uzmanlık bilgisi arar: bir parametrenin neden saptığı, ne anlama "
            "geldiği, hangi müdahalenin yapılacağı. Nedeni veya çözümü "
            "bilmediğin her durumda kullan."
        ),
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        fn=query_knowledge_base,
    ),
}


def run_tool(source: DataSource, name: str, args: dict[str, Any]) -> str:
    """Validate then execute.

    Nothing the model produces is trusted. Passing unvalidated arguments through
    to a function is an indirect way of handing the model code execution.
    """
    tool = TOOLS.get(name)
    if tool is None:
        raise ToolError(f"'{name}' diye bir araç yok. Kullanılabilir: {', '.join(TOOLS)}")
    if not tool.read_only:
        raise ToolError(f"'{name}' yazma aracı; ajan menüsünden çağrılamaz.")

    schema = tool.parameters
    allowed = set(schema.get("properties", {}))
    unknown = set(args) - allowed
    if unknown:
        raise ToolError(
            f"'{name}' için tanımsız argüman: {', '.join(sorted(unknown))}. "
            f"Beklenen: {', '.join(sorted(allowed)) or 'yok'}"
        )
    missing = set(schema.get("required", [])) - set(args)
    if missing:
        raise ToolError(f"'{name}' için zorunlu argüman eksik: {', '.join(sorted(missing))}")

    try:
        return tool.fn(source, **args)
    except ToolError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ToolError(f"'{name}' çalışırken hata: {type(exc).__name__}: {exc}") from exc


def tool_menu() -> str:
    """Plain text rather than JSON Schema: small models ignore long schema blocks
    and hallucinate around them. Schemas stay in code for validation."""
    satirlar = []
    for t in TOOLS.values():
        args = ", ".join(
            f"{k}{'' if k in t.parameters.get('required', []) else '?'}"
            for k in t.parameters.get("properties", {})
        )
        satirlar.append(f"- {t.name}({args}): {t.description}")
    return "\n".join(satirlar)

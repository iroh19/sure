"""
S.U.R.E. — Karar motoru birim testleri
=======================================
Güvenlik-kritik kural motorunu doğrular: DO < 6 mg/L → MUTLAKA "critical".
Bu, sistemin ana vaadi; sessizce bozulursa tehlike "ok" görünür.

Çalıştır (backend bağımlılıkları kurulu ortamda):
    cd backend && python -m pytest test_decision.py -v
"""
from pathlib import Path

import pytest

from main import (
    rule_based_decision,
    apply_rule_override,
    parse_decision_text,
    _recommend,
    SensorReading,
    VisionFrame,
)


def _sensor(do=8.0, temp=18.0, ph=7.0, tds=300.0) -> SensorReading:
    return SensorReading(
        timestamp="2026-01-01T00:00:00Z",
        temperature_c=temp,
        dissolved_oxygen_mgl=do,
        ph=ph,
        tds_ppm=tds,
    )


def _vision(fish=5, activity=0.05) -> VisionFrame:
    return VisionFrame(
        timestamp="2026-01-01T00:00:00Z",
        frame_id=1,
        fish_count=fish,
        avg_activity=activity,
        tracks=[],
    )


# ── Kural motoru: dört durum ────────────────────────────────────────────────
def test_all_safe_is_ok():
    d = rule_based_decision(_vision(), _sensor())
    assert d["status"] == "ok"
    assert d["engine"] == "rule-based-fallback"


def test_low_oxygen_is_critical():
    """Ürünün ana vaadi: DO < 6 → critical."""
    d = rule_based_decision(_vision(), _sensor(do=5.5))
    assert d["status"] == "critical"
    assert "dissolved_oxygen_mgl" in d["reasoning"]


def test_oxygen_boundary_exactly_6_is_ok():
    """6.0 güvenli alt sınır; sınır değeri kapsam içi → ok."""
    d = rule_based_decision(_vision(), _sensor(do=6.0))
    assert d["status"] == "ok"


def test_high_temperature_is_warning_not_critical():
    d = rule_based_decision(_vision(), _sensor(temp=25.0))
    assert d["status"] == "warning"


def test_low_ph_is_warning():
    d = rule_based_decision(_vision(), _sensor(ph=5.0))
    assert d["status"] == "warning"


def test_low_activity_is_warning():
    d = rule_based_decision(_vision(fish=3, activity=0.001), _sensor())
    assert d["status"] == "warning"
    assert "aktivite" in d["reasoning"].lower()


def test_critical_outranks_warning():
    """Hem sıcaklık yüksek hem DO düşük → critical kazanır."""
    d = rule_based_decision(_vision(), _sensor(do=5.0, temp=25.0))
    assert d["status"] == "critical"


def test_zero_fish_is_warning_not_activity_alert():
    """fish_count == 0 kendi başına uyarı; aktivite kuralı ayrıca tetiklenmemeli.

    Bir refah izleyicisi 'her şey yolunda' derken hiç balık görmüyorsa ya
    vision arızalıdır ya sürü dibe çökmüştür — ikisi de sessiz geçilemez.
    llm-service/eval.py T08 senaryosu da bu davranışı bekliyor.
    """
    d = rule_based_decision(_vision(fish=0, activity=0.0), _sensor())
    assert d["status"] == "warning"
    assert "hiç balık tespit edilmedi" in d["reasoning"]
    # Aktivite kuralı çift raporlamamalı
    assert "aktivitesi çok düşük" not in d["reasoning"]


def test_no_vision_frame_is_still_ok():
    """Vision servisi henüz bağlanmadıysa (v=None) 'balık yok' uyarısı verilmez."""
    d = rule_based_decision(None, _sensor())
    assert d["status"] == "ok"


def test_none_inputs_are_safe():
    d = rule_based_decision(None, None)
    assert d["status"] == "ok"
    assert d["recommendations"]


def test_recommendations_match_status():
    assert _recommend("critical")
    assert _recommend("warning")
    assert _recommend("ok") == ["Mevcut bakım rutinini sürdür."]


# ── Kural motoru override — /api/decision ve /api/decision/stream ortak ağı ──
def test_override_escalates_when_model_misses_critical():
    """Model 'ok' derken DO 5.0 ise kural motoru critical'a yükseltmeli."""
    parsed = {"status": "ok", "reasoning": "Her şey yolunda.", "recommendations": ["devam"]}
    out = apply_rule_override(parsed, _vision(), _sensor(do=5.0))
    assert out["status"] == "critical"
    assert out["rule_override"] is True
    assert "Kural motoru override" in out["reasoning"]


def test_override_does_not_downgrade_model():
    """Model kural motorundan daha ciddi diyorsa aşağı çekilmemeli."""
    parsed = {"status": "critical", "reasoning": "Model kritik gördü.", "recommendations": []}
    out = apply_rule_override(parsed, _vision(), _sensor())   # kural motoru: ok
    assert out["status"] == "critical"
    assert "rule_override" not in out


def test_override_treats_missing_status_as_ok():
    """status alanı hiç yoksa güvenli tarafa düşüp kural motorunu uygulamalı."""
    out = apply_rule_override({"reasoning": "bozuk"}, _vision(), _sensor(do=5.0))
    assert out["status"] == "critical"


def test_override_treats_unknown_status_as_ok():
    """Model tanınmayan bir status ('kritik' gibi) dönerse override çalışmalı."""
    out = apply_rule_override({"status": "kritik", "reasoning": "x"},
                              _vision(), _sensor(do=5.0))
    assert out["status"] == "critical"


# ── Stream metninden karar ayrıştırma ───────────────────────────────────────
def test_parse_decision_text_extracts_json():
    raw = 'Tabii, işte karar: {"status":"warning","reasoning":"pH yüksek"} umarım yardımcı olur'
    out = parse_decision_text(raw)
    assert out["status"] == "warning"
    assert out["reasoning"] == "pH yüksek"


def test_parse_decision_text_survives_garbage():
    """JSON yoksa çökmemeli; status 'ok' varsayılır, override yine de yükseltir."""
    out = parse_decision_text("model saçmaladı, JSON yok")
    assert out["status"] == "ok"
    assert out["engine"].startswith("aqua-1b")
    escalated = apply_rule_override(out, _vision(), _sensor(do=5.0))
    assert escalated["status"] == "critical"


# ── LLM çıktı ayrıştırma (torch yoksa atlanır) ──────────────────────────────
def test_generate_decision_handles_malformed_output(monkeypatch):
    """Model geçerli JSON dönmezse generate_decision çökmeden güvenli fallback üretir."""
    pytest.importorskip("torch")
    import importlib
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "llm-service"))
    inference = importlib.import_module("inference")

    monkeypatch.setattr(inference, "_generate",
                        lambda *a, **k: "model bozuk metin döndü, JSON yok")
    out = inference.generate_decision({"sensor": None, "vision": None})
    assert "status" in out and "engine" in out
    assert out["status"] == "ok"  # ayrıştırılamayınca güvenli varsayılan
    # Bu 'ok' modelin kararı değil. engine ve status başarı yoluyla birebir aynı
    # olduğu için tek ayırt edici işaret bu.
    assert out["parsed"] is False


def test_generate_decision_marks_parsed_output(monkeypatch):
    """Model geçerli JSON döndüğünde karar `parsed: True` taşır."""
    pytest.importorskip("torch")
    import importlib
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "llm-service"))
    inference = importlib.import_module("inference")

    monkeypatch.setattr(inference, "_generate",
                        lambda *a, **k: '{"status": "warning", "reasoning": "test"}')
    out = inference.generate_decision({"sensor": None, "vision": None})
    assert out["status"] == "warning"
    assert out["parsed"] is True

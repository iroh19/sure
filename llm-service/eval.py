"""
S.U.R.E. AQUA-7B Eval Script
=============================
Fine-tune sonrası model kalitesini 8 senaryo üzerinde ölçer.
Model yoksa kural motoru ile test eder (fallback mod).

Kullanım:
  python eval.py                    # model + kural motoru karşılaştırma
  python eval.py --rule-only        # sadece kural motoru (model gerekmez)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# ─── Test senaryoları ─────────────────────────────────────────────────────────
SCENARIOS = [
    {
        "id": "T01", "name": "Normal koşullar",
        "sensor": {"temperature_c": 18.5, "dissolved_oxygen_mgl": 7.2, "ph": 7.1, "tds_ppm": 320},
        "vision": {"fish_count": 8, "avg_activity": 0.0031},
        "expected": "ok",
    },
    {
        "id": "T02", "name": "Kritik oksijen",
        "sensor": {"temperature_c": 22.1, "dissolved_oxygen_mgl": 5.7, "ph": 7.8, "tds_ppm": 390},
        "vision": {"fish_count": 6, "avg_activity": 0.0015},
        "expected": "critical",
    },
    {
        "id": "T03", "name": "pH uyarısı",
        "sensor": {"temperature_c": 19.2, "dissolved_oxygen_mgl": 6.1, "ph": 8.3, "tds_ppm": 420},
        "vision": {"fish_count": 7, "avg_activity": 0.0028},
        "expected": "warning",
    },
    {
        "id": "T04", "name": "Optimal koşullar",
        "sensor": {"temperature_c": 20.5, "dissolved_oxygen_mgl": 9.4, "ph": 7.3, "tds_ppm": 280},
        "vision": {"fish_count": 10, "avg_activity": 0.0058},
        "expected": "ok",
    },
    {
        "id": "T05", "name": "Soğuk su + düşük pH",
        "sensor": {"temperature_c": 15.2, "dissolved_oxygen_mgl": 8.0, "ph": 6.2, "tds_ppm": 180},
        "vision": {"fish_count": 5, "avg_activity": 0.0019},
        "expected": "warning",
    },
    {
        "id": "T06", "name": "Yüksek oksijen, yüksek aktivite",
        "sensor": {"temperature_c": 17.8, "dissolved_oxygen_mgl": 11.2, "ph": 7.5, "tds_ppm": 350},
        "vision": {"fish_count": 9, "avg_activity": 0.0044},
        "expected": "ok",
    },
    {
        "id": "T07", "name": "Acil durum — çoklu parametre",
        "sensor": {"temperature_c": 23.5, "dissolved_oxygen_mgl": 4.8, "ph": 8.6, "tds_ppm": 500},
        "vision": {"fish_count": 4, "avg_activity": 0.0008},
        "expected": "critical",
    },
    {
        "id": "T08", "name": "Vision yok — sensör normal",
        "sensor": {"temperature_c": 18.0, "dissolved_oxygen_mgl": 7.8, "ph": 6.9, "tds_ppm": 310},
        "vision": {"fish_count": 0, "avg_activity": 0.0},
        "expected": "warning",
    },
]

SAFE = {
    "temperature_c":        (16.0, 21.0),
    "dissolved_oxygen_mgl": (6.0, 12.0),
    "ph":                   (6.5, 8.0),
    "tds_ppm":              (200.0, 450.0),
}


# ─── Kural motoru (backend'den kopyalanmış — circular import önlemek için) ────
def rule_based_status(sensor: dict, vision: dict) -> str:
    status = "ok"
    for key, (lo, hi) in SAFE.items():
        val = sensor.get(key, 0)
        if val < lo or val > hi:
            status = "critical" if key == "dissolved_oxygen_mgl" else \
                     ("warning" if status == "ok" else status)
    fc = vision.get("fish_count", 1)
    act = vision.get("avg_activity", 1)
    if fc > 0 and act < 0.002:
        status = "warning" if status == "ok" else status
    if fc == 0:
        status = "warning" if status == "ok" else status
    return status


# ─── Model çağrısı ────────────────────────────────────────────────────────────
def model_status(snapshot: dict) -> tuple[str, str]:
    """AQUA-7B'den status döner. Model yoksa (rule-fallback, error) tuple."""
    try:
        import inference
        result = inference.generate_decision(snapshot)
        return result.get("status", "?"), "model"
    except Exception as e:
        return rule_based_status(snapshot["sensor"], snapshot["vision"]), f"rule-fallback ({e.__class__.__name__})"


# ─── Eval runner ──────────────────────────────────────────────────────────────
def run_eval(rule_only: bool = False) -> None:
    print(f"\n{'='*60}")
    print("S.U.R.E. AQUA-7B Eval — 8 Senaryo")
    print(f"Mod: {'Kural Motoru (--rule-only)' if rule_only else 'Model + Kural Karşılaştırma'}")
    print(f"{'='*60}\n")

    results = []
    for sc in SCENARIOS:
        snapshot = {"sensor": sc["sensor"], "vision": sc["vision"], "safe_ranges": SAFE}
        if rule_only:
            pred = rule_based_status(sc["sensor"], sc["vision"])
            source = "rule"
        else:
            pred, source = model_status(snapshot)

        passed = pred == sc["expected"]
        results.append(passed)

        icon = "✓" if passed else "✗"
        print(f"  {icon} [{sc['id']}] {sc['name']}")
        print(f"       Beklenen: {sc['expected']:8s}  Üretilen: {pred:8s}  Kaynak: {source}")
        if not passed:
            print(f"       ⚠ HATA: beklenen '{sc['expected']}' ama '{pred}' üretildi")
        print()

    passed_n = sum(results)
    total = len(results)
    pct = passed_n / total * 100
    print(f"{'='*60}")
    print(f"SONUÇ: {passed_n}/{total} geçti ({pct:.0f}%)")
    if pct == 100:
        print("✓ Tüm senaryolar geçti.")
    elif pct >= 75:
        print("⚠ Çoğu senaryo geçti, başarısızlıkları gözden geçir.")
    else:
        print("✗ Ciddi başarısızlıklar var — model veya fine-tune sorunu olabilir.")
    print(f"{'='*60}\n")

    sys.exit(0 if pct == 100 else 1)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--rule-only", action="store_true", help="Modeli yükleme, sadece kural motorunu test et")
    a = p.parse_args()
    run_eval(a.rule_only)

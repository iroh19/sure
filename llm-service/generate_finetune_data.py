"""
S.U.R.E. Fine-Tune Veri Üreticisi
====================================
sensor_mock.csv okur, kural motoru ile etiketler, JSONL çıktısı üretir.
Mevcut 8 el yazımı senaryoyla birleştirir.

Kullanım:
  python generate_finetune_data.py --output sure_finetune_data_v2.jsonl
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

SENSOR_CSV = Path(__file__).resolve().parent.parent / "data" / "sensor_mock.csv"
EXISTING_DATA = Path(__file__).resolve().parent / "sure_finetune_data.jsonl"

SAFE = {
    "temperature_c":        (16.0, 21.0),
    "dissolved_oxygen_mgl": (6.0, 12.0),
    "ph":                   (6.5, 8.0),
    "tds_ppm":              (200.0, 450.0),
}

REASON_TEMPLATES = {
    "ok": "Tüm su kalitesi parametreleri güvenli aralıkta. {fish_count} balık normal aktivite gösteriyor.",
    "warning": "{alerts} Parametreler izlenmeli.",
    "critical": "KRİTİK: {alerts} Acil müdahale gerekiyor.",
}

RECOMMENDATIONS = {
    "ok":       ["Mevcut bakım rutinini sürdür.", "Günlük filtre kontrolü yap."],
    "warning":  ["Parametreleri yakından izle.", "Trend kötüleşirse müdahale planı hazırla."],
    "critical": ["Havalandırmayı/oksijen pompasını derhal artır.", "Yemlemeyi durdur, suyu kontrol et."],
}


def rule_label(sensor: dict, vision: dict) -> tuple[str, str]:
    alerts = []
    status = "ok"
    for key, (lo, hi) in SAFE.items():
        val = sensor[key]
        if val < lo or val > hi:
            label = {"temperature_c": "Sıcaklık", "dissolved_oxygen_mgl": "Çözünmüş oksijen",
                     "ph": "pH", "tds_ppm": "TDS"}[key]
            alerts.append(f"{label} aralık dışı ({val:.1f}, güvenli {lo}-{hi}).")
            if key == "dissolved_oxygen_mgl":
                status = "critical"
            elif status == "ok":
                status = "warning"

    fc = vision["fish_count"]
    act = vision["avg_activity"]
    if fc > 0 and act < 0.002:
        alerts.append(f"Düşük aktivite ({act:.4f}) — stres belirtisi.")
        if status == "ok":
            status = "warning"
    if fc == 0:
        alerts.append("Kamera görüş alanında balık tespit edilemedi.")
        if status == "ok":
            status = "warning"

    alert_str = " ".join(alerts) if alerts else ""
    reasoning = REASON_TEMPLATES[status].format(
        fish_count=fc, alerts=alert_str
    )
    return status, reasoning


def load_sensor_csv() -> list[dict]:
    if not SENSOR_CSV.exists():
        print(f"[warning] {SENSOR_CSV} bulunamadı, sadece el yazımı veri kullanılacak.")
        return []
    rows = []
    with open(SENSOR_CSV) as f:
        for row in csv.DictReader(f):
            rows.append({
                "temperature_c":        float(row["temperature_c"]),
                "dissolved_oxygen_mgl": float(row["dissolved_oxygen_mgl"]),
                "ph":                   float(row["ph"]),
                "tds_ppm":              float(row["tds_ppm"]),
            })
    return rows


def load_existing() -> list[dict]:
    if not EXISTING_DATA.exists():
        return []
    records = []
    with open(EXISTING_DATA) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def generate(output_path: str) -> None:
    existing = load_existing()
    sensor_rows = load_sensor_csv()

    new_records = []
    fish_counts = [4, 5, 6, 7, 8, 9, 10]
    activities  = [0.0008, 0.0015, 0.0019, 0.0028, 0.003, 0.004, 0.0044, 0.0058]

    for i, sensor in enumerate(sensor_rows):
        vision = {
            "fish_count":   random.choice(fish_counts),
            "avg_activity": random.choice(activities),
        }
        status, reasoning = rule_label(sensor, vision)
        new_records.append({
            "sensor": sensor,
            "vision": vision,
            "label": {
                "status": status,
                "reasoning": reasoning,
                "recommendations": RECOMMENDATIONS[status],
            }
        })

    all_records = existing + new_records
    with open(output_path, "w") as f:
        for r in all_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    status_counts = {}
    for r in all_records:
        s = r["label"]["status"]
        status_counts[s] = status_counts.get(s, 0) + 1

    print(f"[generate] {len(all_records)} örnek yazıldı → {output_path}")
    print(f"[generate] Dağılım: {status_counts}")
    print(f"[generate] Fine-tune için kullan: python finetune.py --data {output_path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="sure_finetune_data_v2.jsonl")
    a = p.parse_args()
    generate(a.output)

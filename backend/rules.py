"""
S.U.R.E. — Kural tabanlı refah karar motoru (TEK KAYNAK)
=========================================================
Bu dosya sistemin güvenlik ağıdır ve BİLEREK bağımsızdır: FastAPI, pydantic
veya httpx import etmez. Böylece hem backend hem de `llm-service/eval.py`
aynı kodu çalıştırabilir.

Neden ayrı dosya: eval.py eskiden bu mantığın kendi kopyasını taşıyordu ve
kopya üretimden ayrışmıştı (fish_count == 0 senaryosunda biri "ok", diğeri
"warning" diyordu). Eval'in ölçtüğü motor, sahada çalışan motor olmalı.

Girdiler düz `dict` — pydantic modeli değil — ki hiçbir servise bağlı olmasın.
"""
from __future__ import annotations

from typing import Optional

# Mersin balığı (sturgeon) RAS güvenli aralıkları.
SAFE: dict[str, tuple[float, float]] = {
    "temperature_c":        (16.0, 21.0),
    "dissolved_oxygen_mgl": (6.0, 12.0),
    "ph":                   (6.5, 8.0),
    "tds_ppm":              (200.0, 450.0),
}

# Çözünmüş oksijen tek başına kritik; diğer parametreler uyarı seviyesinde.
CRITICAL_KEY = "dissolved_oxygen_mgl"

# Hareketsizlik/stres eşiği (normalize edilmiş ortalama aktivite).
MIN_ACTIVITY = 0.002

SEVERITY = {"ok": 0, "warning": 1, "critical": 2}


def recommend(status: str) -> list[str]:
    if status == "critical":
        return ["Havalandırmayı/oksijen pompasını derhal artır.",
                "Yemlemeyi durdur, suyu kontrol et."]
    if status == "warning":
        return ["Parametreleri yakından izle.",
                "Trend kötüleşirse müdahale planı hazırla."]
    return ["Mevcut bakım rutinini sürdür."]


def _raise_to(status: str, level: str) -> str:
    """Durumu yalnızca yukarı çeker; asla aşağı indirmez."""
    return level if SEVERITY[level] > SEVERITY[status] else status


def evaluate(sensor: Optional[dict], vision: Optional[dict]) -> dict:
    """Sensör + vision anlık görüntüsünden refah kararı üretir.

    sensor/vision None olabilir (servis henüz bağlanmadıysa) — bu durumda
    ilgili kurallar atlanır, uydurma uyarı üretilmez.
    """
    alerts: list[str] = []
    status = "ok"

    if sensor:
        for key, (lo, hi) in SAFE.items():
            val = sensor.get(key)
            if val is None:
                continue
            if val < lo or val > hi:
                alerts.append(f"{key} aralık dışı: {val} (güvenli {lo}-{hi})")
                status = _raise_to(status, "critical" if key == CRITICAL_KEY else "warning")

    if vision is not None:
        fish_count = vision.get("fish_count")
        activity   = vision.get("avg_activity")
        if fish_count == 0:
            # Refah izleyicisinin "her şey yolunda" demesi ile hiç balık
            # görmemesi aynı anda doğru olamaz: ya vision arızalı ya sürü dipte.
            alerts.append("Karede hiç balık tespit edilmedi "
                          "(vision servisi arızalı veya sürü dibe çökmüş olabilir).")
            status = _raise_to(status, "warning")
        elif fish_count and activity is not None and activity < MIN_ACTIVITY:
            alerts.append(f"Balık aktivitesi çok düşük ({activity})")
            status = _raise_to(status, "warning")

    if not alerts:
        alerts.append("Tüm parametreler güvenli aralıkta.")

    return {
        "status": status,
        "reasoning": " ".join(alerts),
        "recommendations": recommend(status),
    }


def evaluate_status(sensor: Optional[dict], vision: Optional[dict]) -> str:
    """Sadece status isteyen çağıranlar için kısayol (eval.py)."""
    return evaluate(sensor, vision)["status"]

"""
S.U.R.E. AQUA-1B Eval — model kalite testi
==========================================
8 senaryoyu çalıştırır ve `status` alanını doğrular.

ÖNEMLİ: Kural motoru buradan KOPYALANMAZ. `backend/rules.py` doğrudan import
edilir; yani eval'in ölçtüğü motor, sahada çalışan motorun ta kendisidir.
(Eskiden burada bir kopya vardı ve üretimden ayrışmıştı: fish_count == 0
senaryosunda kopya "warning", üretim "ok" diyordu — eval yeşil yanıyordu ama
hiçbir şeyi doğrulamıyordu.)

Kullanım:
  python eval.py                # AQUA-1B'yi çalıştırır, kural motoruyla karşılaştırır
  python eval.py --rule-only    # sadece kural motoru (model gerekmez)

Çıkış kodları:
  0 = tüm senaryolar geçti
  1 = en az bir senaryo başarısız
  2 = model yüklenemedi (model modunda istendi ama gelmedi)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Kural motorunun TEK kaynağı: backend/rules.py
_BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(_BACKEND))
try:
    import rules  # noqa: E402
except ImportError:
    sys.exit(
        f"\n✗ Kural motoru bulunamadı: {_BACKEND / 'rules.py'}\n"
        "  eval.py, üretimdeki kural motorunu depo kökünden import eder.\n"
        "  Depo dışından ya da yalnızca llm-service'i içeren bir konteynerden\n"
        "  çalıştırıyorsan, tam depoyu klonlayıp tekrar dene.\n"
    )


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
        "id": "T08", "name": "Balık tespit edilmedi — sensör normal",
        "sensor": {"temperature_c": 18.0, "dissolved_oxygen_mgl": 7.8, "ph": 6.9, "tds_ppm": 310},
        "vision": {"fish_count": 0, "avg_activity": 0.0},
        "expected": "warning",
    },
]


# ─── Motorlar ─────────────────────────────────────────────────────────────────
def rule_status(sc: dict) -> str:
    """Üretimdeki kural motoru (backend/rules.py) — kopya değil."""
    return rules.evaluate_status(sc["sensor"], sc["vision"])


def load_model():
    """AQUA-1B'yi yükler. Başarısızlıkta istisna fırlatır — sessizce düşmez."""
    import inference
    inference._load()
    return inference


def model_status(inference, sc: dict) -> tuple[str, bool]:
    """(status, parsed) döndürür.

    `parsed` olmadan bu fonksiyon modelin kararıyla, çıktısı ayrıştırılamadığı
    için düşülen güvenli varsayılanı aynı şey sanıyordu — ikisi de 'ok' ve ikisi
    de aynı engine. Yani skor, kısmen modeli değil fallback'i ölçüyordu.
    """
    snapshot = {"sensor": sc["sensor"], "vision": sc["vision"], "safe_ranges": rules.SAFE}
    out = inference.generate_decision(snapshot)
    return out.get("status", "?"), bool(out.get("parsed", False))


# ─── Eval runner ──────────────────────────────────────────────────────────────
def run_eval(rule_only: bool = False, repeat: int = 1) -> int:
    inference = None
    if not rule_only:
        try:
            inference = load_model()
        except Exception as exc:
            # Sessizce kural motoruna düşüp "8/8 geçti" basmak, ölçüm yapmadan
            # yeşil yanmak demekti. Model istendiyse model yoksa bu bir hatadır.
            print(f"\n✗ AQUA-1B yüklenemedi: {exc.__class__.__name__}: {exc}")
            print("  Model olmadan model kalitesi ölçülemez.")
            print("  Sadece kural motorunu test etmek istiyorsan: python eval.py --rule-only\n")
            return 2

    mode = "Kural Motoru (--rule-only)" if rule_only else "AQUA-1B + Kural Motoru Karşılaştırma"
    print(f"\n{'='*68}")
    print("S.U.R.E. Eval — 8 Senaryo")
    print(f"Mod: {mode}")
    print(f"Motor kaynağı: backend/rules.py (üretimle aynı)")
    if not rule_only:
        import inference as _inf
        print(f"Sıcaklık: {_inf.TEMPERATURE}  ·  tekrar: {repeat}")
        if _inf.TEMPERATURE > 0 and repeat == 1:
            print("UYARI: karar yolu örnekleme yapıyor, bu tek bir çekiliş.")
            print("       Ölçüm istiyorsan --repeat N ver ya da AQUA_TEMPERATURE=0 kur.")
    print(f"{'='*68}\n")

    failures = []
    disagreements = []
    unparsed = []
    unstable = []

    for sc in SCENARIOS:
        rule = rule_status(sc)
        if rule_only:
            pred, source = rule, "rule"
        else:
            draws = [model_status(inference, sc) for _ in range(repeat)]
            statuses = [d[0] for d in draws]
            n_unparsed = sum(1 for d in draws if not d[1])
            # Çoğunluk değil en kötü durum: bir senaryo bazen 'ok' bazen
            # 'critical' diyorsa, raporlanacak olan modelin ıskaladığı hâldir.
            pred = min(statuses, key=lambda st: rules.SEVERITY.get(st, 0)) \
                if len(set(statuses)) > 1 else statuses[0]
            source = "aqua-1b" if n_unparsed == 0 else (
                f"aqua-1b → AYRIŞTIRILAMADI ({n_unparsed}/{repeat}), güvenli varsayılan")
            if n_unparsed:
                unparsed.append(f"{sc['id']}({n_unparsed}/{repeat})")
            if len(set(statuses)) > 1:
                unstable.append((sc["id"], sorted(set(statuses))))
            if pred != rule:
                disagreements.append((sc["id"], pred, rule))

        passed = pred == sc["expected"]
        if not passed:
            failures.append(sc["id"])

        icon = "✓" if passed else "✗"
        print(f"  {icon} [{sc['id']}] {sc['name']}")
        print(f"       Beklenen: {sc['expected']:9s} Üretilen: {pred:9s} Kaynak: {source}")
        if not rule_only:
            print(f"       Kural motoru: {rule}")
        if not passed:
            print(f"       ⚠ HATA: beklenen '{sc['expected']}' ama '{pred}' üretildi")
        print()

    total = len(SCENARIOS)
    passed_n = total - len(failures)
    pct = passed_n / total * 100

    print(f"{'='*68}")
    print(f"SONUÇ: {passed_n}/{total} geçti ({pct:.0f}%)   [mod: {'kural' if rule_only else 'model'}]")
    if failures:
        print(f"Başarısız senaryolar: {', '.join(failures)}")
    if disagreements:
        print(f"\nModel ile kural motorunun ayrıştığı {len(disagreements)} senaryo:")
        for sid, m, r in disagreements:
            print(f"  {sid}: model='{m}' kural='{r}'  → canlıda kural motoru override eder")
    if unstable:
        print(f"\nAynı girdide farklı cevap veren {len(unstable)} senaryo:")
        for sid, opts in unstable:
            print(f"  {sid}: {' / '.join(opts)}  → yukarıda en kötü durum raporlandı")
    if not rule_only:
        print(f"\nModelin çıktısı {len(unparsed)}/{total} senaryoda ayrıştırılamadı"
              + (f": {', '.join(unparsed)}" if unparsed else ""))
        if unparsed:
            print("  Bu senaryolarda 'ok' modelin kararı değil, güvenli varsayılan.")
            print("  Yukarıdaki yüzde o kadarıyla modeli değil fallback'i ölçüyor.")
    if rule_only:
        print("\nNOT: Bu çalıştırma kural motorunu doğruladı, MODELİ DEĞİL.")
        print("     Tez/sunumda model başarımı olarak bu sayıyı kullanma.")
    print(f"{'='*68}\n")

    return 0 if not failures else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="S.U.R.E. karar motoru eval")
    p.add_argument("--rule-only", action="store_true",
                   help="Modeli yükleme, sadece kural motorunu test et")
    p.add_argument("--repeat", type=int, default=1,
                   help="Her senaryoyu N kez koştur (karar yolu örnekleme yapıyor)")
    a = p.parse_args()
    sys.exit(run_eval(a.rule_only, max(1, a.repeat)))

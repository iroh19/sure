<!-- /autoplan restore point: /Users/batuhancitak/.gstack/projects/sure-project/main-autoplan-restore-20260824-115620.md -->
# S.U.R.E. — Geliştirme Planı (TAMAMLANDI)

## Bağlam

Tez sunumu için hazırlanan mersin balığı refah izleme sistemi prototipi.
Gerçek çiftlik videoları, simüle sensör verisi, YOLOv11 + ByteTrack + AQUA-1B + React stack.

**Durum:** Bu plandaki 5 maddenin tamamı sevk edildi. 2026-08-24 tarihli
`/autoplan` incelemesi maddelerin üçünde "üretildi ama bağlanmadı" sorunu
buldu; hepsi düzeltildi. Ayrıntı: [İnceleme bulguları](#inceleme-bulgulari-2026-08-24).

---

## Kapsam — sevk durumu

| # | Madde | Durum | Not |
|---|-------|-------|-----|
| 1 | Kritik DO uyarı overlay'i | ✅ Sevk edildi | `CriticalAlertBanner`, sensörden doğrudan hesaplanır |
| 2 | AQUA LLM streaming yanıt (SSE) | ✅ Sevk edildi | Chat stream'de; karar paneli bilinçli olarak bloklayan uçta |
| 3 | Eval script — model kalite testi | ✅ Sevk edildi | Artık üretim kural motorunu import eder |
| 4 | Status timeline şeridi | ✅ Sevk edildi | 60 kare + gerçek 1 saatlik uyarı/kritik sayacı |
| 5 | Fine-tune veri genişletme (50+) | ✅ Sevk edildi | 128 örnek, `finetune.py` varsayılanı v2 |

### 2. AQUA LLM Streaming Yanıt — SSE

- `llm-service/inference.py`: `generate_decision_stream()` + `generate_chat_stream()`
- `llm-service/main.py`: `/generate/stream`, `/chat/stream` (SSE)
- `backend/main.py`: `/api/decision/stream`, `/api/chat/stream`
- `frontend/src/App.jsx`: `ChatBar` token token render (fetch + ReadableStream)

**Karar paneli neden stream'e bağlı değil:** karar yapılandırılmış bir JSON
verdiktir, düzyazı değil. Token token JSON akıtmak kullanıcıya spinner'dan daha
kötü bir deneyim verir; `DecisionPanel` zaten bir yükleniyor durumu gösteriyor.
`/api/decision/stream` uç noktası çalışır ve güvenlidir, isteyen bağlayabilir.

### 3. Eval Script

- `llm-service/eval.py`: 8 senaryo, `status` doğrulaması
- Kural motoru **kopyalanmaz** — `backend/rules.py` import edilir
- Model yüklenemezse sessizce kural motoruna düşmez, exit 2 ile hata verir

### 4. Status Timeline Şeridi

- `frontend/src/App.jsx`: `DecisionTimeline` (header'da)
- `backend/main.py`: `/api/decision/history` — SQLite'tan son N karar
- 60 renkli kare + "son 1 saat: N kritik · N uyarı" özeti

### 5. Fine-Tune Veri Genişletme

- `llm-service/generate_finetune_data.py`: `sensor_mock.csv`'den otomatik JSONL
- `sure_finetune_data_v2.jsonl`: 128 örnek (8 el yazımı + otomatik senaryolar)
- `finetune.py --data` varsayılanı v2

---

## İnceleme bulguları (2026-08-24)

`/autoplan` sevk edilen kodu inceledi. Düzeltilen başlıca sorunlar:

**Kredibilite (tez/sunum riski)**
1. `eval.py` kural motorunun kopyasını test ediyordu; kopya üretimden ayrışmıştı
   (T08: kopya "warning", üretim "ok"). → `backend/rules.py` tek kaynak oldu.
2. `eval.py` model yüklenemeyince sessizce kural motoruna düşüp "8/8 %100 ✓"
   basıyordu. → Model modunda model yoksa exit 2.
3. `finetune.py` varsayılanı 8 örneklik v1'di; maddenin gerekçesi buydu. → v2.
4. `mlx-lm` `requirements.txt`'te yoktu; README'nin Mac quickstart'ı startup'ta
   patlıyordu. → Platform işaretçisiyle eklendi.
5. `llm-service/Dockerfile` `AQUA_BASE_MODEL=KurmaAI/AQUA-7B` diyordu; adaptör
   1B tabana göre eğitilmiş. → AQUA-1B.

**Güvenlik / mimari**
6. `/api/decision/stream` kural motoru override'ını atlıyordu (DO<6 → critical
   yükseltmesi yoktu) ve `decision_history`'ye yazmıyordu. → Ortak
   `apply_rule_override`; iki uç da aynı güvenlik ağından geçiyor.
7. SQLite: her yazma yeni bağlantı açıyordu ve `with` bağlantıyı kapatmıyordu.
   → Tek paylaşılan bağlantı + WAL + satır cap + temiz kapanış.
8. Vision ~15fps'te her frame'i diske yazıyordu. → ~1Hz.
9. MJPEG dedup `id(jpeg)` ile yapılıyordu (GC id'yi geri kullanabilir).
   → Monotonik `frame_seq`.
10. Kural motoru "0 balık" durumunda "ok" diyordu. → Açık `warning` kuralı.

**Kapsam dışı bırakılanlar:** yok. Tüm bulgular kapatıldı.

---

## Kapsam Dışı (değişmedi)

- Gerçek sensör donanımı entegrasyonu
- Çok-tank desteği
- Kimlik doğrulama (auth)
- Telegram uyarı sistemi

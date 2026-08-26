# S.U.R.E. — TODOS

Ertelenen işler. Kapatılanlar en altta arşivde.

---

## Açık

### 1. Vision recall'ını yükselt (P2)

**Ne:** `sure_v1` recall ~0.695 — yoğun/örtüşen karelerde balıkların ~%30'u
kaçırılıyor. `NMS time limit exceeded` uyarıları bunu doğruluyor.

**Çözüm yönü:** yoğun karelerde etiket gözden geçirme + `imgsz` 960/1280 ile
yeniden eğitim, ya da demo için inference'ta `conf` düşürüp `max_det` artırma.
En etkili adım veri setini büyütmek.

**Dosyalar:** `vision-service/train_sure.py`, `vision-service/yolo_runner.py`.
**Bağımlılık:** Yok. Ayrıntı: [`MODEL_RAPORU.md`](MODEL_RAPORU.md).

### 2. AQUA-1B'yi gerçek modelle eval'den geçir (P1 — tez öncesi)

**Ne:** `llm-service/eval.py` artık üretim kural motorunu doğru şekilde test
ediyor, ama **model modunda hiç çalıştırılmadı**. `--rule-only` sonucu kural
motorunu doğrular, modeli değil.

**Neden:** Tez savunmasında "model ne kadar iyi?" sorusunun sayısal yanıtı
ancak model modunda çalıştırınca oluşur.

**Çözüm:**
```bash
cd llm-service
AQUA_ADAPTER_PATH=./sure-aqua-adapter python3 eval.py
```
8/8 beklenmiyor; model ile kural motorunun ayrıştığı senaryolar raporun
sonunda listelenir. Canlıda kural motoru override eder, yani ayrışma
tehlikeli değil — ama bilinmesi gerekir.

**Dosyalar:** `llm-service/eval.py`.
**Bağımlılık:** Model + adaptörün indirilmiş olması.

### 3. Adaptörü v2 veriyle yeniden eğit (P2)

**Ne:** `llm-service/sure-aqua-adapter/` büyük olasılıkla 8 örneklik v1 ile
eğitildi (`finetune.py` varsayılanı o zaman v1'di). Varsayılan artık
`sure_finetune_data_v2.jsonl` (128 örnek) ama adaptör yeniden eğitilmedi.

**Çözüm:** `cd llm-service && python3 finetune.py --output ./sure-aqua-adapter-v2`
Sonra eval'i iki adaptörle karşılaştır, iyi olanı kullan.

**Dosyalar:** `llm-service/finetune.py`, `llm-service/sure_finetune_data_v2.jsonl`.
**Bağımlılık:** Madde 2 (ölçüm olmadan karşılaştırma anlamsız).

### 4. Frontend bundle'ını böl (P3)

**Ne:** `dist/assets/index-*.js` 577 KB (gzip 173 KB) — recharts + lucide tek
chunk'ta. Vite 500 KB uyarısı veriyor.

**Çözüm:** Recharts'ı `React.lazy` ile grafik paneline böl.
**Dosyalar:** `frontend/src/App.jsx`, `frontend/vite.config.js`.
**Bağımlılık:** Yok. Kapalı ağ demosunda etkisi yok.

### 5. Production'da CORS'u kısıtla (P3)

**Ne:** `CORS_ORIGINS` ortam değişkeni eklendi ama varsayılan hâlâ `*`
(kapalı ağ demosu için bilinçli). Backend açılışta bunu log'luyor.

**Çözüm:** İnternete açık bir deployment'ta
`CORS_ORIGINS="https://sure.example.com"` ver.
**Dosyalar:** `backend/main.py`.
**Bağımlılık:** Yok. Sadece public deployment öncesi.

---

## Kapatıldı (2026-08-24 `/autoplan` incelemesi)

| # | İş | Nasıl kapatıldı |
|---|----|-----------------|
| ~~1~~ | SQLite yazma yolunu right-size et | Tek paylaşılan bağlantı + WAL + `DB_ROW_CAP` prune + vision ~1Hz (`VISION_DB_INTERVAL`) + kapanışta `db_close()` |
| ~~2~~ | MJPEG frame dedup'ını sayaca çevir | `Store.frame_seq` monotonik sayaç; `id(jpeg)` karşılaştırması kaldırıldı |
| ~~3~~ | Frontend'i MJPEG stream'e geçir | `LiveFeedPanel` artık `/api/vision/stream`'e bağlı; 250ms polling kaldırıldı, kopunca 2sn'de yeniden bağlanır |
| ~~4~~ | CORS'u kısıtla | `CORS_ORIGINS` env eklendi (yukarıda madde 5 olarak izleniyor) |

Aynı incelemede kapatılan diğer bulgular için [`PLAN.md`](PLAN.md) →
"İnceleme bulguları" bölümüne bak.

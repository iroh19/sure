# S.U.R.E. — TODOS

Ertelenen işler. Kapatılanlar en altta arşivde.

---

## Açık

### 1. Vision recall'ını yükselt (P2)

**Ne:** `sure_v1` recall, koştuğumuz `conf=0.20` eşiğinde 0.782 — yoğun/örtüşen
karelerde balıkların ~%22'si kaçırılıyor. `NMS time limit exceeded` uyarıları
bunu doğruluyor. (Bu madde önceden 0.695 diyordu; o sayı epoch 73'e aitti ve
`best.pt` epoch 77. Ayrıntı `MODEL_RAPORU.md`.)

**Çözüm yönü:** yoğun karelerde etiket gözden geçirme + `imgsz` 960/1280 ile
yeniden eğitim, ya da inference'ta `max_det` artırma. En etkili adım veri setini
büyütmek — bu aynı zamanda EXP05'in bulduğu 32 yakın-kopya train/val çiftini de
temizler.

**Dosyalar:** `vision-service/train_sure.py`, `vision-service/yolo_runner.py`.
**Bağımlılık:** Yok. Ayrıntı: [`MODEL_RAPORU.md`](MODEL_RAPORU.md).

### 2. Karar yolunun örnekleme yapması (P1 — tez öncesi karar)

**Ne:** `AQUA_TEMPERATURE` varsayılanı `0.3` ve `generate_decision` bunu
kullanıyor. Yani aynı sensör snapshot'ı için koşular arasında farklı severity
çıkabiliyor. `--repeat 3` ile 8 senaryonun **6'sı** aynı girdide farklı cevap
verdi.

**Neden karar gerekiyor:** Anlatı metni için sıcaklık istenebilir, ama severity
alanı için bu bir kumar — üstelik ölçümü de imkânsızlaştırıyor. Seçenekler:
severity'yi greedy üretip yalnızca gerekçeyi örneklemek, ya da tüm karar
yolunu `temp=0`'a çekip sıcaklığı sohbet ucunda bırakmak.

**Dosyalar:** `llm-service/inference.py` (`TEMPERATURE`, `generate_decision`).
**Bağımlılık:** Yok. Tez sayılarının anlamlı olması buna bağlı.

### 3. Adaptörü v2 veriyle yeniden eğit (P1 — madde 2'nin ölçümü hazır)

**Ne:** `llm-service/sure-aqua-adapter/` 8 örneklik v1 ile eğitildi — EXP03 bunu
`_mlx_data/{train,valid}.jsonl` kayıt sayısı + içerik eşleşmesi + mtime sırasıyla
kanıtladı. `finetune.py`'nin kendi docstring'i o veri için "yetersiz, sadece
duman testi" diyor. Varsayılan artık `sure_finetune_data_v2.jsonl` (128 örnek).

**Artık temel çizgi var:** `--repeat 3` ile v1 adaptörü 4/8, 6/8 senaryoda en az
bir ayrıştırılamayan çekiliş, T07 3/3 ayrıştırılamadı. v2 bunu geçmeli.

**Çözüm:** `cd llm-service && python3 finetune.py --output ./sure-aqua-adapter-v2`
Sonra `eval.py --repeat 3`'ü iki adaptörle koştur, karşılaştır.

**Dosyalar:** `llm-service/finetune.py`, `llm-service/sure_finetune_data_v2.jsonl`.
**Bağımlılık:** Yok (madde 2'nin ölçümü artık mevcut).

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

| # | İş | Nasıl kapatıldı |
|---|----|-----------------|
| ~~2~~ | AQUA-1B'yi gerçek modelle eval'den geçir | İlk kez koşturuldu. Sonuç `--repeat 3` ile **4/8**, kural motoruyla 4 ayrışma — hepsi düşük tahmin, hepsi override edildi. Koşum, ölçüm aracının kendisinde bir kör nokta ortaya çıkardı: ayrıştırılamayan çıktı ile modelin "ok" demesi ayırt edilemiyordu. `parsed` alanı üretim yoluna eklendi, eval artık görüyor. Ayrıntı: PR #7 |

Aynı incelemede kapatılan diğer bulgular için [`PLAN.md`](PLAN.md) →
"İnceleme bulguları" bölümüne bak.

# S.U.R.E. — TODOS

Demo (TEKNOFEST) için bilinçli ertelenen işler. Her madde `/plan-eng-review`
(2026-06-05) sırasında tartışıldı ve demo sonrasına bırakıldı.

---

## 1. SQLite yazma yolunu right-size et  (P2)

**Ne:** Backend her ~15fps vision frame'ini async handler içinde senkron `sqlite3`
ile, her yazmada yeni bir bağlantı açarak yazıyor; tablolar sınırsız büyüyor.

**Neden:** Senkron disk I/O event loop'u bloklar → uzun demoda frame ingest,
karar çağrıları ve MJPEG stream birlikte takılır. DB dosyası da sürekli şişer.

**Çözüm:**
- Vision'ı her frame yerine ~1Hz yaz (canlı veri zaten `Store.deque`'da, maxlen 300).
- Modül düzeyinde tek SQLite bağlantısı kullan (bağlantı-per-yazma yerine).
- Periyodik prune veya satır cap (ör. son 10k kayıt) ekle.

**Dosyalar:** `backend/main.py` → `Store.push_vision`, `push_sensor`, `db_insert_*`.
**Bağımlılık:** Yok. Demo'da risk düşük olduğu için ertelendi.

## 2. MJPEG frame dedup'ını sayaca çevir  (P2)

**Ne:** `backend/main.py:384` MJPEG stream'inde yeni frame tespiti `id(jpeg)` ile
yapılıyor. Python GC sonrası nesne id'sini geri kullanabilir → yeni bir frame eski
bir id ile çakışıp atlanabilir.

**Çözüm:** `Store`'a monotonik `frame_seq` sayacı ekle, dedup'ı ona göre yap.
**Dosyalar:** `backend/main.py` → `Store.push_frame`, `vision_stream`.
**Bağımlılık:** Madde 3'ün ön koşulu.

## 3. Frontend'i MJPEG stream'e geçir  (P2)

**Ne:** `LiveFeedPanel` şu an `/api/vision/frame.jpg`'i 250ms'de bir poll ediyor
(incelemede 100ms'den düşürüldü). Backend'de zaten kullanılmayan bir MJPEG push
stream var (`/api/vision/stream`).

**Çözüm:** `<img src>`'i `/api/vision/stream`'e bağla → polling tamamen biter,
sunucu frame'leri push eder. Önce Madde 2 (id dedup) düzeltilmeli.
**Dosyalar:** `frontend/src/App.jsx` → `LiveFeedPanel`.
**Bağımlılık:** Madde 2.

## 4. CORS'u kısıtla  (P3)

**Ne:** `backend/main.py:315` `allow_origins=["*"]` — tüm originlere açık.

**Neden:** Kapalı ağ demosunda kabul edilebilir; internete açık bir deployment'ta
güvenlik açığı.

**Çözüm:** Production'da `allow_origins`'i frontend origin'iyle sınırla.
**Dosyalar:** `backend/main.py`.
**Bağımlılık:** Yok. Sadece production deployment öncesi gerekli.

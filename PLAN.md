# S.U.R.E. — Geliştirme Planı

## Bağlam

Tez sunumu için hazırlanan mersin balığı refah izleme sistemi prototipi.
Gerçek çiftlik videoları, simüle sensör verisi, YOLOv11 + ByteTrack + AQUA-7B + React stack.

Kritik DO uyarı overlay'i tamamlandı (öncelik 1). Kalan 4 geliştirme bu planda.

---

## Kapsam

### 2. AQUA LLM Streaming Yanıt — SSE (30 dk)

**Sorun:** `llm-service/main.py` → `GET /generate` 4-8 sn bloklıyor. Kullanıcı yanıt gelene kadar boş ekrana bakıyor.

**Çözüm:**
- `llm-service/inference.py`: `generate_decision_stream()` + `generate_chat_stream()` generator fonksiyonları ekle
- `llm-service/main.py`: `StreamingResponse(media_type="text/event-stream")` endpoint'i
- `backend/main.py`: `/api/decision` ve `/api/chat` SSE proxy'e dönüştür
- `frontend/src/App.jsx`: `ChatBar` ve `DecisionPanel`'de `EventSource` ile token token render

**Etkilenen dosyalar:** `llm-service/inference.py`, `llm-service/main.py`, `backend/main.py`, `frontend/src/App.jsx`

---

### 3. Eval Script — Model Kalite Testi (45 dk)

**Sorun:** Fine-tune sonrası AQUA-7B'nin doğru çalıştığını kanıtlayan hiçbir ölçüm yok. Tez sunumunda "model ne kadar iyi?" sorusu yanıtsız kalıyor.

**Çözüm:**
- `llm-service/eval.py` (yeni dosya): 8 test senaryosu çalıştır, `status` alanını doğrula, `pass/fail` raporla
- `llm-service/sure_finetune_data.jsonl`'deki mevcut örnekleri test senaryosu olarak kullan
- Kural tabanlı motor ile AQUA-7B çıktısını karşılaştır

**Etkilenen dosyalar:** `llm-service/eval.py` (yeni), `llm-service/sure_finetune_data.jsonl`

---

### 4. Status Timeline Şeridi — Header'da Karar Geçmişi (45 dk)

**Sorun:** Son 20 kararın trendi görünmüyor. Çiftlik çalışanı "1 saatte kaç kez warning aldım?" bilgisine ulaşamıyor.

**Çözüm:**
- `frontend/src/App.jsx`: Header'a `DecisionTimeline` bileşeni ekle
- Son 20 kararı (ok/warning/critical) renkli küçük kareler olarak göster
- `state.decision_history` backend endpoint'inden al veya frontend'de lokalde biriktir
- `backend/main.py`: `/api/decision/history` — son N karar geçmişini dönen endpoint

**Etkilenen dosyalar:** `frontend/src/App.jsx`, `backend/main.py`

---

### 5. Fine-Tune Veri Genişletme — 50+ Örnek (2 saat)

**Sorun:** `sure_finetune_data.jsonl` sadece 8 satır. LoRA fine-tune için minimum 50 örnek gerekli; aksi halde model underfitting.

**Çözüm:**
- `llm-service/generate_finetune_data.py` (yeni): `sensor_mock.csv`'yi okuyarak kural motoru etiketiyle otomatik JSONL üret
- Sensör kombinasyonları (multi-parametre sapmalar) ekle
- Mevcut 8 el yazımı senaryoyu koru, 42 otomatik senaryo ekle

**Etkilenen dosyalar:** `llm-service/generate_finetune_data.py` (yeni), `llm-service/sure_finetune_data.jsonl`

---

## Kapsam Dışı

- Gerçek sensör donanımı entegrasyonu
- SQLite kalıcı depolama
- Telegram uyarı sistemi
- Çok-tank desteği
- Kimlik doğrulama (auth)

## Mevcut Altyapı

- `llm-service/inference.py` — AQUA-7B MLX/HF çıkarım (değiştirilecek: stream eklenecek)
- `llm-service/main.py` — FastAPI LLM servis (değiştirilecek: SSE endpoint)
- `backend/main.py` — FastAPI backend (değiştirilecek: SSE proxy + history endpoint)
- `frontend/src/App.jsx` — React dashboard (değiştirilecek: streaming + timeline)
- `llm-service/sure_finetune_data.jsonl` — 8 eğitim örneği (genişletilecek)

# S.U.R.E. — Otonom Mersin Balığı Refah İzleme Sistemi

> **S**turgeon · **U**nified · **R**efah · **E**ngine
> Kapalı Devre Balık Yetiştiriciliği (RAS) için bilgisayarlı görü + su kalitesi
> sensörü + yerel LLM karar motorunu birleştiren gerçek zamanlı izleme prototipi.
> _TEKNOFEST için geliştirilmiştir._

---

## Ne yapar?

Bir tank kamerasından gelen görüntüde mersin balıklarını **YOLOv11 + ByteTrack**
ile tespit ve takip eder; su kalitesi sensörlerini (çözünmüş oksijen, sıcaklık,
pH, TDS) okur; bu verileri yerel çalışan **AQUA-1B** diline (RAS uzmanı,
fine-tune edilmiş) vererek Türkçe refah kararı üretir. Kritik durumlarda
(örn. oksijen < 6 mg/L) anlık uyarı verir. Tümü **React** tabanlı canlı bir
dashboard'da gösterilir.

## Mimari

```
vision-service ──POST /api/vision/ingest (metrikler ~15fps)──┐
  (YOLOv11+ByteTrack) ─POST /api/vision/frame (JPEG)─────────┤
                                                             ▼
sensor (mock CSV) ──2s──────────────►  backend (FastAPI :8000)
                                          │  Store(deque 300) + SQLite
                                          │  GET /api/decision ─► llm-service :8001
                                          ▼                        (AQUA-1B, mlx/HF)
                                      frontend :5173 (React + Recharts)
```

| Servis | Görev | Teknoloji |
|--------|-------|-----------|
| `backend` | API, durum birleştirme, kural motoru, SQLite geçmiş | FastAPI |
| `llm-service` | Refah kararı + sohbet (SSE streaming) | AQUA-1B, mlx-lm / transformers |
| `vision-service` | Balık tespit + takip | YOLOv11, ByteTrack, OpenCV |
| `frontend` | Canlı dashboard | React 19, Vite, Tailwind, Recharts |

## Hızlı başlangıç (Mac / Apple Silicon — native)

> Docker Compose **yalnızca Linux + NVIDIA GPU** içindir. Apple Silicon'da
> servisleri aşağıdaki gibi elle çalıştır.

```bash
# 0. Python ortamı
python3 -m venv venv && source venv/bin/activate

# 1. LLM servisi (mlx, ilk açılışta modeli indirir)
#    AQUA_ADAPTER_PATH → fine-tune adaptörü (Türkçe + alana-uyarlı yanıt)
cd llm-service && pip install -r requirements.txt
AQUA_ADAPTER_PATH=./sure-aqua-adapter uvicorn main:app --port 8001

# 2. Backend (yeni terminal)
cd backend && pip install -r requirements.txt
uvicorn main:app --port 8000

# 3. Vision (yeni terminal) — demo videosuyla
cd vision-service && pip install -r requirements.txt
python yolo_runner.py --source ../data/demo.MOV

# 4. Frontend (yeni terminal)
cd frontend && npm install && npm run dev
# → http://localhost:5173
```

## Testler

```bash
cd backend && python -m pytest test_decision.py -v
```
Güvenlik-kritik kural motorunu doğrular (DO < 6 mg/L → "critical").

## Model eğitimi

Vision modeli (YOLOv11) kendi makinende eğitilir:

```bash
cd vision-service
python train_sure.py     # 510 görsel (412 train / 98 val), 100 epoch, mps
```
Çıktı: `sure_models/sure_v1/weights/best.pt`. Production (`yolo_runner.py`) bu
ağırlığa bağlıdır. Model başarım analizi ve eğitim notları için bkz.
[`MODEL_RAPORU.md`](MODEL_RAPORU.md).

## Büyük dosyalar (repoda yok)

Videolar, dataset görselleri ve model ağırlıkları boyut nedeniyle git'e
**dahil edilmez** (bkz. `.gitignore`). Bunları **GitHub Releases** veya bir
bulut linkinden indir:

- `data/balık_videolar/` — kaynak videolar → _Releases_
- `data/sure_dataset/` — 510 etiketli görsel → _Releases / Drive_
- `sure_models/*/weights/*.pt` — eğitilmiş ağırlıklar → _Releases_
- `data/demo.MOV` — demo videosu → _Releases_

> Base ağırlıklar (`yolo11n.pt`, `yolo11s.pt`) ultralytics'ten ilk eğitimde
> otomatik iner; commit'lemeye gerek yok.

## Proje yapısı

```
backend/         FastAPI API + kural motoru + SQLite + testler
llm-service/     AQUA-1B çıkarım, SSE streaming, fine-tune, eval
vision-service/  YOLO eğitim + ByteTrack runner
frontend/        React dashboard
data/            sensor_mock.csv + dataset yaml'ları (görseller hariç)
sure_models/     eğitim çıktıları (ağırlıklar hariç)
MODEL_RAPORU.md  model başarım analizi
TODOS.md         ertelenen iyileştirmeler
```

## Bilinen sınırlamalar / yapılacaklar

Demo sonrası iyileştirmeler [`TODOS.md`](TODOS.md)'de listelidir
(SQLite yazma yolu, MJPEG stream'e geçiş, CORS kısıtlama).

## Kapsam dışı

Gerçek sensör donanımı entegrasyonu, kimlik doğrulama, çok-tank desteği,
Telegram uyarısı — prototip kapsamı dışındadır.

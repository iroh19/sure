# S.U.R.E. — Otonom Mersin Balığı Refah İzleme Sistemi

Kapalı devre balık yetiştiriciliği (RAS) için gerçek zamanlı refah izleme:
bilgisayarlı görü, su kalitesi sensörleri ve yerel çalışan bir LLM — hepsi
deterministik bir güvenlik ağının arkasında.

_English: [README.md](README.md)_

[![CI](https://github.com/iroh19/sure/actions/workflows/ci.yml/badge.svg)](https://github.com/iroh19/sure/actions/workflows/ci.yml)

| | |
|---|---|
| Tespit | YOLOv11s · mAP50 **0.840** · precision **0.878** · recall 0.695 |
| Veri seti | 510 etiketli görsel (412 train / 98 val), tek sınıf `sturgeon` |
| Testler | 18 birim + 22 bilgi tabanı + 48 ajan + 8 senaryo eval — hepsi CI kapısı |
| Retrieval | pgvector · 8 doküman / 44 chunk · MRR **0.856** · hit@1 **0.793** |
| LLM | AQUA-1B (Gemma 3 1B) · LoRA adaptörü · tamamen on-prem |

---

## Problem

Çözünmüş oksijenin 6 mg/L altına düşmesi saatler içinde stok kaybına yol açar.
Bir dil modeli burada gerçekten faydalı — sensör verisiyle balık davranışını
birlikte yorumluyor ve gerekçesini doğal dilde yazıyor. Ama **bir LLM'in
güvenlik-kritik bir eşiği sessizce kaçırması kabul edilemez.**

Bu yüzden model önerir, deterministik kural motoru karar verir. Model `ok`
derken `backend/rules.py` `critical` görüyorsa durum yükseltilir ve kural
motorunun gerekçesi eklenir. Bozuk çıktıda sistem güvenli tarafa düşer. LLM
servisi tamamen kapalıysa karar yine kural motorundan üretilir.

## Tasarım kararları

**Model son söz sahibi değil.** `rules.py` tek kaynak ve bilinçli olarak
bağımsız: FastAPI, pydantic veya httpx import etmiyor, böylece backend ile eval
aynı kodu çalıştırıyor. Durum yalnızca yukarı çekilir. Arayüzdeki kritik oksijen
bandı doğrudan sensörden hesaplanır, LLM'e hiç uğramaz.

**Eval üretimi ölçüyor.** Eskiden kural mantığının kopyasını taşıyordu ve kopya
ayrışmıştı: `fish_count == 0` senaryosunda kopya `warning`, üretim `ok` diyordu —
yeşil yanıyor ama hiçbir şeyi doğrulamıyordu. Kopya kaldırıldı.

**Eşiklerin tek kaynağı var.** Üç yerde yaşıyorlardı (kural motoru, bilgi tabanı,
sistem prompt'u) ve elle yazılmış kopyalar ayrışır. Zincir artık
`SYSTEM_PROMPT <- knowledge/*.md <- backend/rules.py` ve 22 test bunu tutuyor.
Testler mutasyonla doğrulandı: değişen eşik, değişen severity ve silinen doküman
senaryolarının üçünde de düşüyorlar.

**Retrieval precision'ı recall'a tercih ediyor** ve **araç seçimi modelde değil
kodda** — ikisi de ölçümle, aşağıda.

---

## Mimari

```
vision-service ──POST /api/vision/ingest (~15 fps)──┐
  (YOLOv11 + ByteTrack)  ──POST /api/vision/frame───┤
                                                    ▼
sensör (mock CSV) ──2 sn─────────► backend (FastAPI :8000)
                                     │  Store(deque 300) + SQLite
                                     │  GET /api/decision ─► llm-service :8001
                                     ▼                       (AQUA-1B, mlx/HF)
                                 frontend :5173 (React + Recharts)
```

| Servis | Görev | Teknoloji |
|---|---|---|
| `backend` | API, durum birleştirme, kural motoru, geçmiş | FastAPI |
| `llm-service` | Karar + sohbet (SSE), RAG, ajan araçları | AQUA-1B, mlx-lm / transformers |
| `vision-service` | Tespit ve takip | YOLOv11, ByteTrack, OpenCV |
| `frontend` | Canlı dashboard | React 19, Vite, Tailwind, Recharts |
| `pgvector` | Bilgi tabanı vektör deposu | PostgreSQL 17 + pgvector 0.8 |

`v*.*.*` etiketinde CD önce kalite kapısını çalıştırır, ancak geçerse GHCR'a
imaj basar.

---

## Retrieval

`llm-service/knowledge/` altındaki 8 doküman (oksijen, sıcaklık, pH/alkalinite,
azot döngüsü, TDS, davranış, acil müdahale, karar mantığı) pgvector'de
indeksleniyor. Kanıt, **sapan parametreye göre** seçilip prompt'a giriyor; model
gerekçesini `[K1]`, `[K2]` ile işaretliyor ve kaynaklar karara ekleniyor.

`rag/bench.py`, 2 embedding modeli × 4 chunking stratejisini 29 etiketli sorgu
üzerinde karşılaştırıyor. Metrikler doküman seviyesinde.

| Model | Strateji | Chunk | hit@1 | hit@3 | MRR | Bağlam (kelime) | |
|---|---|--:|--:|--:|--:|--:|---|
| e5-small | fixed-480w | 8 | 0.862 | 0.897 | 0.900 | 1646 | dar uzay, bütçe aşımı |
| e5-small | fixed-240w | 16 | 0.759 | 1.000 | 0.868 | 922 | bütçe aşımı |
| **e5-small** | **heading** | **44** | **0.793** | **0.931** | **0.856** | **317** | **seçildi** |
| tr-bert | heading | 44 | 0.724 | 0.931 | 0.833 | 317 | |
| tr-bert | fixed-480w | 8 | 0.414 | 0.828 | 0.614 | 1646 | dar uzay |

Tablonun tepesi seçilmedi. `fixed-480w` doküman başına tek chunk üretiyor; k=5
ile korpusun %62'si dönüyor ve hit@5 = 1.000 beceri değil aritmetik. Ayrıca
~1646 kelime istiyor, prompt bütçesi ~380 — yani ölçülen skor üretimde
ulaşılamaz. `bench.py` iki tuzağı da işaretliyor.

`e5-small` her stratejide `tr-bert`'i geçiyor ve chunk büyüdükçe fark açılıyor
(MRR 0.833 → 0.614): e5 asimetrik retrieval için `query:`/`passage:` önekleriyle
eğitilmiş, `tr-bert` ise cümle benzerliği modeli ve uzun pasajlar eğitim
dağılımının dışında kalıyor.

**Eşik.** Bi-encoder her sorguya en yakın chunk'ı döndürür — korpusun
yanıtlayamayacağı sorulara bile. `rag/calibrate.py` 29 pozitifi 12 zor negatifle
karşılaştırıyor: pozitifler 0.841–0.892, negatifler 0.813–0.847 — örtüşüyorlar.

| Eşik | Geçen pozitif | Geçen negatif | F1 |
|---|--:|--:|--:|
| 0.84 | 29/29 | 3/12 | 0.951 |
| **0.85** | 24/29 | **0/12** | 0.906 |

F1 0.84'ü seçer; biz 0.85 kullanıyoruz. Hatalar simetrik değil: kaçırılan
doküman yalnızca gerekçeyi zayıflatır ve kural motoru yine karar verir, uydurma
bağlam ise yanlış bilgiyi kaynak göstererek sunar.

Retrieval bir iyileştirmedir, bağımlılık değil: pgvector kapalıysa `retrieve()`
boş döner ve sistem çalışmaya devam eder.

```bash
cd llm-service
python -m rag.ingest        # korpusu indeksle
python -m rag.bench         # model × strateji
python -m rag.calibrate     # benzerlik eşiği
```

---

## Ajan

`agent/tools.py` üç okuma aracı tanımlıyor (sensör trendi, balık hareketliliği,
bilgi tabanı); JSON Schema doğrulaması ve enjekte edilen veri erişimiyle. Yazma
aracı yok — model kanıt toplar, kural motoru karar verir ve alarm üretir.

`agent/loop.py` elle yazılmış bir ajan döngüsü: adım bütçesi, tekrar tespiti,
araç hatalarının gözlem olarak geri beslenmesi ve adım sayacından bağımsız duvar
saati. `generate` dışarıdan enjekte ediliyor, bu yüzden 48 test onu senaryolanmış
sahte modelle, hiç LLM olmadan sürüyor.

`agent/bench_agent.py` sonra asıl soruyu sordu — gerçek bir model bunu sürebilir mi:

| Model | Format | Seçim | Adım | Süre |
|---|--:|--:|--:|--:|
| AQUA-1B (Gemma 3 1B) | 0% | 0% | 0.0 | 2.7 sn |
| AQUA-7B (Mistral, 4-bit) | 60% | 50% | 3.6 | 11.9 sn |

AQUA-1B ayrıştırılabilir tek bir eylem üretmiyor: talimatı tekrarlıyor ya da JSON
şablonunu kopyalıyor, ve prefill testinde dört farklı senaryoda birebir aynı
çıktıyı verdi. 7B biçimi daha sık tutturuyor ama **beş senaryonun hepsinde**
`get_sensor_trend` seçti — sabit cevap, yani %50 tesadüfi. `bench_agent.py` bunu
`CONSTANT ANSWER` olarak raporluyor, yüzdenin yanıltmasına izin vermiyor.

Bunun yerine `agent/router.py` üretimde: yönlendirme deterministik kod, model
yalnızca anlatıyor. Araçlar, doğrulama ve çalıştırma döngüyle ortak; yalnızca
planlayıcı farklı. `loop.py` depoda kalıyor — tool-calling yapabilen bir model
gelirse benchmark yerini hak edip etmediğini söyler.

---

## Doğrulama

```bash
cd backend && python -m pytest test_decision.py -v      # 18 (torch yoksa 1 atlanır)
python -m pytest llm-service/test_knowledge.py -v       # 22
python -m pytest llm-service/test_agent.py -v           # 48
cd llm-service && python eval.py --rule-only            # 8 senaryo
```

Dördü de CI'da çalışıyor ve geçmeden hiçbir imaj build edilmiyor. `eval.py`
çıkış kodları: `0` hepsi geçti, `1` başarısız senaryo, `2` model yüklenemedi —
model modunda sessizce kural motoruna düşmez.

Bir backend testi `inference.py`'ı import ettiği için torch istiyor ve yoksa
atlanıyor; CI **17 geçti, 1 atlandı** raporluyor. Tek test için CI'a ~800 MB
torch kurmak bilinçli olarak tercih edilmedi.

Vision metrikleri ve eğitim notları: [`MODEL_RAPORU.md`](MODEL_RAPORU.md).

---

## Hızlı başlangıç (macOS / Apple Silicon)

Docker Compose Linux + NVIDIA hedefler; Apple Silicon'da servisleri native çalıştır.

```bash
brew install postgresql@17 pgvector && brew services start postgresql@17
createdb sure_rag && psql -d sure_rag -c "CREATE EXTENSION IF NOT EXISTS vector;"

cd llm-service && pip install -r requirements.txt
python -m rag.ingest
AQUA_ADAPTER_PATH=./sure-aqua-adapter uvicorn main:app --port 8001

cd backend && pip install -r requirements.txt && uvicorn main:app --port 8000
cd vision-service && pip install -r requirements.txt && python yolo_runner.py --source ../data/demo.MOV
cd frontend && npm install && npm run dev        # http://localhost:5173
```

Eğitim ve fine-tune:

```bash
cd vision-service && python train_sure.py                    # YOLOv11s, 510 görsel
cd llm-service && python finetune.py --output ./adapter-v2   # LoRA; cihaza göre MLX veya PEFT
```

## Yapılandırma

| Değişken | Varsayılan | Not |
|---|---|---|
| `LLM_SERVICE_URL` | `http://localhost:8001` | |
| `BACKEND_URL` | `http://localhost:8000` | ajan araçları geçmişi buradan okur |
| `CORS_ORIGINS` | `*` | public deployment'ta mutlaka daralt |
| `DB_PATH` | `backend/sure_history.db` | |
| `AQUA_BASE_MODEL` | `KurmaAI/AQUA-1B` | adaptör 1B tabana göre eğitildi |
| `AQUA_ADAPTER_PATH` | _(boş)_ | boşsa yüklenmez |
| `RAG_ENABLED` | `1` | `0` retrieval'ı kapatır |
| `RAG_DATABASE_URL` | `postgresql:///sure_rag` | |
| `RAG_EMBED_MODEL` | `e5-small` | `e5-small` \| `tr-bert` |
| `RAG_CHUNK_STRATEGY` | `heading` | bkz. benchmark |
| `RAG_MIN_SIMILARITY` | `0.85` | korpus değişirse yeniden kalibre et |

## Dizin yapısı

```
backend/          FastAPI, SQLite, testler
  rules.py        kural motoru — tek kaynak
llm-service/
  knowledge/      RAG korpusu, 8 doküman, eşikler frontmatter'da
  rag/            chunking, embedding, pgvector, benchmark, kalibrasyon
  agent/          araçlar, döngü, deterministik yönlendirici, model ölçümü
vision-service/   YOLO eğitimi + ByteTrack runner
frontend/         React dashboard
```

Videolar, veri seti görselleri ve ağırlıklar git'e dahil değil (bkz.
`.gitignore`); GitHub Releases üzerinden dağıtılıyor.

Modele giden metinler — bilgi tabanı, araç açıklamaları, prompt'lar ve hata
mesajları — Türkçe, çünkü ürün Türkçe yanıt veriyor. Kod, yorumlar ve commit'ler
İngilizce.

## Bilinen sınırlamalar

- **Vision recall 0.695** — yoğun karelerde balıkların ~%30'u kaçırılıyor.
  Çözüm: veri setini büyütmek ve `imgsz` 960/1280 ile yeniden eğitmek.
- **AQUA-1B model modunda eval'den hiç geçirilmedi**; `--rule-only` kural
  motorunu doğrular, modeli değil.
- **LoRA adaptörü hâlâ 8 örneklik v1 olabilir**; v2 (128 örnek) bekliyor.
- **Dashboard `sources` alanını göstermiyor** — alıntılar `/api/decision`'a
  ulaşıyor ama arayüzde render edilmiyor.

Kapsam dışı: gerçek sensör donanımı, kimlik doğrulama, çok-tank, alarm bildirimi.

---

_TEKNOFEST Tarım Teknolojileri yarışması kapsamında geliştirilmiştir._

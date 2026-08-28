# S.U.R.E. — Otonom Mersin Balığı Refah İzleme Sistemi

Kapalı devre balık yetiştiriciliği (RAS) için gerçek zamanlı refah izleme:
bilgisayarlı görü, su kalitesi sensörleri ve yerel çalışan bir LLM — hepsi
deterministik bir güvenlik ağının arkasında.

_English: [README.md](README.md)_

[![CI](https://github.com/iroh19/sure/actions/workflows/ci.yml/badge.svg)](https://github.com/iroh19/sure/actions/workflows/ci.yml)

**[Canlı demo →](https://iroh19.github.io/sure/)** — dashboard, kaydedilmiş bir
oturumu oynatıyor. GitHub Pages yalnızca statik dosya sunar, yani tarayıcıda
çıkarım yapılmıyor; sensörler, tespitler, kararlar ve alıntılar gerçek
bileşenlerle üretildi ve sayfa bunu açıkça yazıyor. Sistemi gerçekten çalıştırmak
için: [![Codespaces'te aç](https://img.shields.io/badge/Codespaces-a%C3%A7-24292e?logo=github)](https://codespaces.new/iroh19/sure)

**[Makaleyi oku →](research/SURE-paper.pdf)** — çift katmanlı mimari üzerine 32
sayfa, ve [nasıl araştırıldığı](research/SURE-arastirma-sureci.pdf)
_([English](research/SURE-research-process.pdf))_. Arkasındaki her şey — on bir
deney, ham loglar, bağımsız doğrulama — [`research/`](research/) altında.

| | |
|---|---|
| Tespit | YOLOv11s · mAP50 **0.840** |
| Çalışma noktası | `conf=0.20` → precision **0.720** · recall **0.782** · F1 **0.750** |
| Veri seti | 510 etiketli görsel (412 train / 98 val), tek sınıf `sturgeon` |
| Testler | 18 birim + 22 bilgi tabanı + 48 ajan + 32 MLOps + 19 twin-bridge + 8 senaryo eval — hepsi CI kapısı |
| Retrieval | pgvector · 8 doküman / 44 chunk · MRR **0.856** · hit@1 **0.793** |
| LLM | AQUA-1B (Gemma 3 1B) · LoRA adaptörü · tamamen on-prem |

---

## Makale

[**`research/SURE-paper.pdf`**](research/SURE-paper.pdf) · 32 sayfa · 56 kaynak · 5 şekil

Aşağıdaki mimari akademik bir makale olarak yazıldı; MIT kaynaklı ajan tabanlı
araştırma hattı [pAI/MSc](https://dspace.mit.edu/handle/1721.1/165377) ile, biz
döngünün üzerinde kalarak. Sürecin uzun anlatımı:
[`SURE-arastirma-sureci.pdf`](research/SURE-arastirma-sureci.pdf).

Makaleyi yazmak, bu kod tabanına karşı on bir deney koşturmak demekti ve üçü bu
README'nin eskiden söylediğiyle çelişti:

- **Kural motoru modeli nadiren düzeltiyor.** 8 vakanın 1'inde LLM'in gerçek bir
  düşük tahminini yakaladı. 4'ünde ise sadece modelin çıktısı hiç
  ayrıştırılamadığı için güvenli varsayılana düştü. Baskın güvenlik mekanizması
  hata düzeltme değil, güvenli varsayılana düşme — ve 8 gerekçenin 6'sı girdide
  hiç olmayan sensör değerleri uydurmuştu; yalnızca çıktıya bakan bir kontrol
  bunu göremez.
- **Çift katmanlı tasarım özgün değil.** Düşmanca literatür taraması bunu Safety
  Instrumented Systems kalıbı (IEC 61508/61511) olarak sınıflandırdı. Makale
  katkıyı bunun yerine katmanlar arası tutarlılık üzerinden çerçeveliyor.
- **Alıntıladığımız recall, çalıştığımız recall değil.** Gerçekten kullandığımız
  `conf=0.20` recall 0.782 / precision 0.720 veriyor. `MODEL_RAPORU.md`'deki
  0.859 / 0.719 çifti F1-argmax optimumu — doğru, ama farklı bir sorunun cevabı.

Tüm iz [`research/`](research/) altında commitli: LaTeX kaynağı, ham log ve
betikleriyle on bir deney, her manşet sayıyı yeniden hesaplayan bağımsız
doğrulama ve hattın tam kaydı.

> **Kapsam.** S.U.R.E. hiçbir zaman çalışan bir su ürünleri tesisinde koşmadı.
> Fiziksel sensör donanımı mevcut değil; tüm deneylerdeki her sensör okuması
> sentetik olarak üretildi. 510 görüntülük veri seti düzeneğin elle etiketlenmiş
> gerçek görüntüleri, ama kasıtlı olarak küçük. Katkı, bir saha validasyonu
> değil, fizibilite ve kaynak yönetimi gösterimidir.

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
| AQUA-7B (Mistral, 4-bit) | 100% | 50% | 2.0 | 15.8 sn |

AQUA-1B ayrıştırılabilir tek bir eylem üretmiyor: talimatı tekrarlıyor ya da JSON
şablonunu kopyalıyor, ve prefill testinde dört farklı senaryoda birebir aynı
çıktıyı verdi. 7B biçimi her seferinde tutturuyor ama **beş senaryonun hepsinde**
`get_sensor_trend` seçti — sabit cevap, yani %50 tesadüfi. `bench_agent.py` bunu
`CONSTANT ANSWER` olarak raporluyor, yüzdenin yanıltmasına izin vermiyor. Aynı
çağrı tekrarlandığı için `loop.py`'nin tekrar koruması her senaryoyu 2. adımda
durduruyor — buradaki adım sayısı o taban, planlama derinliğinin ölçüsü değil.

_2026-08-27'de commitlenmiş kodla yeniden ölçüldü; makalenin denetimindeki
bağımsız koşumla ([EXP04](research/experiments/EXP04/)) birebir aynı çıktı. Bu
tablonun önceki hâli 60% / 3.6 adım diyordu; bu sayı commitlenen `loop.py` ile
üretilemez, çünkü sabit cevap tekrar korumasını 2. adımda tetikler. Beş senaryo
üzerinde tek bir greedy (`temp=0.0`) geçiş — seçim yüzdesini oran olarak okumak
için fazla az._

Bunun yerine `agent/router.py` üretimde: yönlendirme deterministik kod, model
yalnızca anlatıyor. Araçlar, doğrulama ve çalıştırma döngüyle ortak; yalnızca
planlayıcı farklı. `loop.py` depoda kalıyor — tool-calling yapabilen bir model
gelirse benchmark yerini hak edip etmediğini söyler.

---

## Edge export

`vision-service/export_bench.py` modeli makinede mevcut her formata çıkarır ve
her birini **temel çizgiyi üreten aynı 98 görsellik doğrulama setinde** koşturur.
Tek başına hız sayısı sonuç değildir: her format doğruluğu bir yerde takas eder
ve ikisi birlikte ölçülmezse bu takas görünmez.

Gecikme, **önceden belleğe alınmış** 40 gerçek doğrulama karesi üzerinde p50/p95
olarak, 8 ısınma koşusu atılarak ölçülür. Ortalama değil yüzdelik: gerçek zamanlı
bir hat en kötü karelerine göre yargılanır.

| Format | Cihaz | mAP50 | ΔmAP50 | mAP50-95 | p50 ms | p95 ms | FPS | Boyut MB |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| pt | mps | 0.8395 | temel | 0.5952 | 31.4 | 36.7 | 31.8 | 54.5 |
| pt | cpu | 0.8395 | +0.0000 | 0.5952 | 39.2 | 41.0 | 25.5 | 54.5 |
| onnx | cpu | 0.8291 | −0.0104 | 0.5867 | 53.5 | 66.1 | 18.7 | 36.2 |
| onnx-int8 | cpu | 0.8313 | −0.0082 | 0.5863 | 36.2 | 39.2 | 27.6 | **9.4** |
| **coreml** | ANE | 0.8298 | −0.0097 | 0.5840 | **9.0** | **9.5** | **111.2** | 18.2 |
| torchscript | cpu | 0.8291 | −0.0104 | 0.5867 | 52.8 | 54.8 | 18.9 | 36.4 |

**Export'un kendisi, quantization olmadan da doğruluk kaybettiriyor.** fp32 ONNX
ve TorchScript aynı −0.0104 mAP50 kaybını veriyor ve mAP50-95'te dört haneye
kadar aynı sayıya oturuyor. İki farklı çalışma zamanının birebir aynı sonucu
vermesi, kaybın sayısal gürültü değil **sistematik** olduğunu gösterir — kayıp
export edilmiş modellerin izlediği son-işleme yolundan geliyor, ağırlık
hassasiyetinden değil.

**INT8 neredeyse bedava ve fp32 ONNX'i geçiyor.** 9.4 MB ile 5.8 kat küçük, daha
hızlı (36.2 ms vs 53.5 ms) ve kaybı *daha az* (−0.0082 vs −0.0104). Bu,
quantization'ın doğruluk artırdığı anlamına gelmez; yukarıdaki bulguyla birlikte
okunmalı — kayıp export yolundan geliyor ve INT8 gürültüsü çalışma noktasını
tesadüfen lehte kaydırmış. Fark gürültü bandında.

**Apple Silicon'da CoreML açık ara kazanıyor.** 9.0 ms p50 (111 FPS), MPS
PyTorch'tan 3.5 kat hızlı, 3 kat küçük ve p95 kuyruğu en dar format (p50'nin
%6 üstü). ONNX'in kuyruğu en kötüsü, %24 — ortalamaya bakınca görünmeyen bir fark.

**TensorRT ölçülmedi.** CUDA gerektiriyor ve Apple Silicon'da çalışmıyor.
`export_bench.py --emit-jetson`, aynı metodolojiyle FP16 ve INT8 satırlarını
hedef cihazda üreten `jetson_bench.py`'ı yazar. Tabloya uydurma TensorRT sayısı
konmadı.

```bash
cd vision-service
python export_bench.py                  # export et ve hepsini ölç
python export_bench.py --skip-export    # mevcut export'ları yeniden ölç
python export_bench.py --emit-jetson    # Jetson tarafı betiğini yaz
```

---

## MLOps

Ağırlıklar git'te duruyor ve dosya adıyla ayırt ediliyordu. Bu, rapor epoch 73
derken sahadaki `best.pt`'nin epoch 77 olduğu ortaya çıkana kadar sürdü —
Ultralytics manşet metriğe göre değil fitness'a (`0.1*mAP50 + 0.9*mAP50-95`) göre
seçiyor. Registry tam da bu tür soruyu arkeoloji olmaktan çıkarmak için var.

`mlops/tracking.py --backfill` tamamlanmış koşuların `results.csv`'sini okuyor,
yani depo ilk komuttan itibaren gerçek geçmişi tutuyor:

| koşu | metrik geçerli | en iyi epoch | mAP50 | precision | recall |
|---|---|--:|--:|--:|--:|
| sure_v1 | evet | 77 | 0.8395 | 0.8583 | 0.7188 |
| ogretmen | **hayır** | 74 | 0.9254 | 0.8829 | 0.9073 |

Öğretmen koşusu kaydediliyor **ve** geçersiz olarak etiketleniyor — aynı 20 kare
ile eğitilip doğrulandığı için 0.925 ezberi ölçüyor. Yalnızca iyi koşuları tutan
bir registry "bunu neden kullanmadık" sorusunu yanıtlayamaz.

### Drift

Üretimde etiket yok, bu yüzden drift modelin kendi çıktısından çıkarılıyor:
tespit güveni dağılımı üzerinde **Population Stability Index**, eğitim zamanında
doğrulama setinden alınan bir referansa karşı. Balık sayısı değil güven, çünkü
sayı karışık bir sinyal — az tespit, model bozulduğu için de olabilir tankta az
balık olduğu için de.

İlk uygulama [0,1] üzerinde eşit genişlikli on bölme kullanıyordu ve işe
yaramıyordu. Dedektörün güvenleri kabaca 0.5–0.9 arasında; referansta altı bölme
boştu ve bunlardan birine düşen her kayma boş bölme tabanına çarpıyordu: PSI
0.06'dan doğrudan 1.05'e sıçrıyor, arada hiçbir şey olmuyordu — gradyan kılığında
ikili alarm. Referansın kendi yüzdeliklerinden alınan **quantile kenarları** her
bölmeye ~%10 kütle veriyor ve sinyal dereceleniyor:

| pencere | PSI | sonuç |
|---|--:|---|
| referansın kendi iki yarısı | 0.039 | yok |
| 200 / 500 / 1000 gerçek alt örnek | 0.029 / 0.014 / 0.002 | yok |
| tespitlerin %10'u bozulur | 0.098 | yok |
| %20'si bozulur | 0.265 | significant |
| güven 0.1–0.4'e çöker | 8.28 | significant |

İlk iki satır eşikleri güvenilir yapan şey: kendi kalibrasyon verisinin
yeniden örneklemesinde alarm veren bir dedektör, sonraki bütün alarmlarını
gürültüye çevirir.

### Yeniden eğitim otomatik değil, kapılı

Drift dünyanın değiştiğini söyler; yerine geçecek modelin daha iyi olacağını değil.

```
drift kontrolü ──► karar ──┬─► yok       dur
                           ├─► inceleme  insana bildir, dur
                           └─► eğit      eğit ─► değerlendir ─► kapı ─► kaydet
```

Aday ancak mevcudu `MIN_IMPROVEMENT`'tan (0.005 mAP50) fazla geçerse yayına
alınır. Eğitim gürültüsü zaten yaklaşık yarı yarıya küçük pozitif farklar üretir;
onlara bakarak yayına almak, karar kılığında yazı tura atmaktır. Orta seviye
drift yeniden eğitim değil inceleme açar — her dalgalanmada eğitmek hem hesap
yakar hem gürültülü bir pencereye uydurma riski taşır.

Karar mantığı `mlops/retrain.py` içinde 32 testli düz fonksiyonlar olarak duruyor;
`mlops/retrain_dag.py` yalnızca zamanlama yapan ince bir Airflow sarmalayıcısı.
Airflow proje bağımlılığı değil — DAG bir Airflow kurulumuna bırakılmak üzere.

```bash
python -m mlops.tracking --backfill      # tamamlanmış koşuları kaydet
python -m mlops.tracking --list
python -m mlops.drift --reference        # referans dağılımı yakala
python -m mlops.drift --check window.json
python -m mlops.retrain --check window.json
mlflow ui --backend-store-uri sqlite:///mlops/mlflow.db
```

### Döngüyü kapatmak

Buradaki diğer bütün ölçümler bir bileşene not veriyor. Bu, tavsiyeye uyulunca
balıkların daha iyi durumda olup olmadığını soruyor: aynı tesis iki kez
koşturuluyor ve tek bir değişken oynatılıyor — S.U.R.E.'nin hükmü kontrolöre
ulaşıyor mu.

İlk koşu boş sonuç verdi ve asıl değer teşhiste: S.U.R.E. ile PLC **aynı
okumada** tetikleniyor, yani danışman katman hiç erken uyarmıyor, aynı anda
uyarıyor. Kontrolörün eşiğini paylaşan bir erken uyarı sisteminin ekleyecek şeyi
yok.

`twin_bridge/advisor.py` bunu seviyeye değil **eğime** bakarak çözüyor; oksijenin
eşiği ne zaman keseceğini öngörüyor. `rules.py` değişmedi: hüküm hâlâ onun ve
hüküm bir taban — öngörü yükseltebilir, indiremez. Öngörü penceresi taramayla
seçildi; 10 tick'ten sonrası aynı faydayı daha pahalıya aldığı için dirsek orada.

| Senaryo | Kol | En düşük DO | Eşik altı | Aerasyon |
|---|---|--:|--:|--:|
| crash | kontrolör tek başına | 4.50 | 37 | 14.7% |
| crash | + S.U.R.E. (trend) | 4.50 | **34** | 15.5% |
| decline | kontrolör tek başına | 4.30 | 213 | 76.2% |
| decline | + S.U.R.E. (trend) | 4.30 | **208** | 77.0% |

**Erken uyarı maruziyeti kısaltır, tabanı yükseltmez.** En düşük değer hiç
oynamıyor, çünkü çöküşün dibinde aeratör zaten doygun ve doygun bir aktüatöre
setpoint yükseltmek bir şey söylemiyor. Taban bir aktüatör boyutlandırma
problemi, zeka problemi değil — bu iddia testle sabitli ki ileride tabanı
yükseltiyor gibi görünen bir değişiklik kutlanmak yerine sorgulansın.

Sayılar `fake_plc.Plant`'i tarif ediyor. Bulgunun şekli bir kontrol sistemi
özelliği; büyüklükler CODESYS'e karşı yeniden ölçülmeli. Gerçek ikizde döngü
ayrıca orada tek bir değişiklik istiyor: `main.gd` HR6'yı simülasyondan yazıyor,
yani Godot ile S.U.R.E. birbirini ezer.

```bash
python -m twin_bridge.experiment --scenario crash --sweep
```

---

## Doğrulama

```bash
cd backend && python -m pytest test_decision.py -v      # 18 (torch yoksa 1 atlanır)
python -m pytest llm-service/test_knowledge.py -v       # 22
python -m pytest llm-service/test_agent.py -v           # 48
python -m pytest twin_bridge -v                         # 19
cd llm-service && python eval.py --rule-only            # 8 senaryo
AQUA_ADAPTER_PATH=... python eval.py --repeat 3         # model modu, 3 çekiliş
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
| `AQUA_TEMPERATURE` | `0.3` | **karar yolu örnekleme yapıyor.** Aynı snapshot, koşular arasında farklı severity — ölçüm için `0` ver |
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
twin_bridge/      Dijital ikiz için Modbus istemcisi + iki-motor karşılaştırması
research/         makale, LaTeX kaynağı ve tüm araştırma kaydı
```

Videolar, veri seti görselleri ve ağırlıklar git'e dahil değil (bkz.
`.gitignore`); GitHub Releases üzerinden dağıtılıyor.

Modele giden metinler — bilgi tabanı, araç açıklamaları, prompt'lar ve hata
mesajları — Türkçe, çünkü ürün Türkçe yanıt veriyor. Kod, yorumlar ve commit'ler
İngilizce.

## Bilinen sınırlamalar

- **Kullandığımız eşikte vision recall 0.782** (`conf=0.20`), precision 0.720
  karşılığında. `MODEL_RAPORU.md`'de alıntılanan 0.859 / 0.719 çifti F1-argmax
  optimumu ve farklı bir soruya cevap veriyor. İkisinin de çözümü: veri setini
  büyütmek ve `imgsz` 960/1280 ile yeniden eğitmek.
- **Doğrulama setinde hiç seyrek kare yok** (1–2 balık) — test edilmemiş bir
  rejim, makalede sayısallaştırıldı.
- **Train ve val arasında 32 yakın-kopya kare çifti**, algısal karma ile bulundu.
  Sayıldı, henüz düzeltilmiş bir manşet metriğe yansıtılmadı.
- **Korpus değişince vektör deposu yeniden beslenmek zorunda.** Aşılmış bir
  recall değeri `knowledge/06-davranis-ve-refah-gostergeleri.md` içinde bir gün
  boyunca durdu, EXP11 bulana kadar — kaynakta düzeltilip yeniden beslendi, ama
  indeksin diskteki dosyalarla eşleştiğini zorlayan bir mekanizma yok.
- **TensorRT satırları ölçülmedi** — henüz CUDA'lı bir cihaz yok.
- **AQUA-1B'nin kararlı bir hükmü yok.** 3 tekrarla ölçüldü: 8 güvenlik
  senaryosunun 4'ünde kural motoruyla uyuşuyor, 6'sında *aynı girdiye farklı
  cevap* veriyor — ikisi hayati senaryo. Katkısı gerekçe üretmek, yargı değil;
  kararı override veriyor. Bkz. [`MODEL_RAPORU.md`](MODEL_RAPORU.md).
- **LoRA adaptörü hâlâ 8 örneklik v1 olabilir**; v2 (128 örnek) bekliyor.
- **Dashboard `sources` alanını göstermiyor** — alıntılar `/api/decision`'a
  ulaşıyor ama arayüzde render edilmiyor.

Kapsam dışı: gerçek sensör donanımı, kimlik doğrulama, çok-tank, alarm bildirimi.

---

_TEKNOFEST Tarım Teknolojileri yarışması kapsamında geliştirilmiştir._

# S.U.R.E. — Model Başarım Raporu

_Vision (YOLOv11) tespit modeli + AQUA-1B karar kalitesi · son güncelleme: 2026-08-28_

---

## Güncel durum (tez/sunumda kullanılacak sayılar)

Production (`vision-service/yolo_runner.py`) **`sure_models/sure_v1/weights/best.pt`**
ağırlığına bağlıdır. Geçerli metrikler bunlardır:

| Metrik | Değer (best.pt, epoch 77) |
|--------|---------------------------|
| Precision | **0.859** |
| Recall | **0.719** |
| mAP50 | **0.840** |
| mAP50-95 | **0.595** |

- Ağ: YOLOv11s · Veri: 510 görsel (412 train / 98 val) · Tek sınıf: `sturgeon`
- Eğitim: 100 epoch hedefi, epoch 79'da durduruldu
- Doğrulama seti: 98 görsel / 1525 balık (train'den ayrı)
- Model epoch 62-79 boyunca ~0.84 mAP50'de platoya oturdu

> **Düzeltme (2026-08-26).** Bu tablo daha önce epoch 73'ün sayılarını
> (P 0.878 / R 0.695) taşıyordu ve yanlıştı. Ultralytics `best.pt`'yi mAP50'ye
> göre değil **fitness = 0.1·mAP50 + 0.9·mAP50-95** ölçütüne göre kaydeder; bu
> ölçüt epoch 77'yi seçmiş. Hata, `best.pt` üzerinde temel çizgi yeniden
> koşturulurken yakalandı: taze `val()` çıktısı (0.8590 / 0.7189 / 0.8395) epoch
> 77 satırıyla dört haneye kadar eşleşti, epoch 73 ile eşleşmedi.
>
> Pratik etkisi: mAP değerleri neredeyse değişmedi, ama **precision olduğundan
> yüksek, recall olduğundan düşük** raporlanmıştı. Sahadaki model belgelenenden
> daha iyi recall'a sahip.

**Not:** mAP eşikten bağımsızdır ve tekrar üretilebilir; precision/recall ise PR
eğrisi üzerinde tek bir çalışma noktasıdır (Ultralytics bunları F1'i maksimize
eden confidence değerinde raporlar). İki koşu arasında mAP sabit kalırken P/R'ın
birlikte kayması normaldir — biri artarken diğeri azalır.

### Çalıştığımız nokta yukarıdaki tablo değil

Yukarıdaki P/R çifti Ultralytics'in F1-argmax raporu. Production ise
`vision-service/yolo_runner.py:44`'te `CONF_THRESH = 0.20` ile koşuyor.
Ultralytics'in ince taneli confidence eğrisi doğrudan okunduğunda:

| Confidence | Precision | Recall | F1 |
|------------|-----------|--------|-----|
| **0.20 (production)** | **0.720** | **0.782** | **0.750** |
| 0.30 | 0.820 | 0.743 | 0.780 |
| 0.35 | 0.851 | 0.725 | 0.783 |
| F1-argmax (eğri tepesi, conf=0.341) | 0.845 | 0.730 | 0.784 |
| Yukarıdaki tablo (`box.mp`/`box.mr`) | 0.859 | 0.719 | 0.783 |

İkisi de doğru; farklı sorulara cevap veriyorlar. Tablo "bu model en iyi ayarında
ne yapar" sorusunun, 0.20 satırı "sahada koşan sistem ne yapıyor" sorusunun
cevabı. Tezde ve sunumda hangisinin kullanıldığı açıkça söylenmeli.

**Metodolojik uyarı:** `model.val(conf=X)` bu soruyu cevaplamaz. `box.mp`/`box.mr`
conf 0.10'dan 0.30'a kadar birebir aynı geliyor (0.859/0.719), çünkü Ultralytics
korunan eğri üzerinde argmax raporluyor — düşük bir `conf` geçmek, gerçek en-iyi-F1
noktası aralıkta kaldığı sürece raporlanan P/R'ı değiştirmiyor. Çalışma
noktasındaki P/R için eğrinin kendisi okunmalı.

**Kalan zayıf nokta:** Çalışma noktasında bile recall 0.782 — yoğun/örtüşen
balıklar kaçırılıyor. `NMS time limit exceeded` uyarıları ve kalabalık kareler
bunu doğruluyor. Çözüm yönü: yoğun karelerde etiket gözden geçirme + daha yüksek
çözünürlük (imgsz 960/1280), ya da inference'ta `max_det` artırma.

Ölçüm ayrıntısı: [`research/experiments/EXP07/`](research/experiments/EXP07/).

### Sunumda kullanma

- ✅ Yukarıdaki `sure_v1` sayılarını kullan — ayrı doğrulama setinde ölçüldü.
- ❌ `ogretmen` modelinin mAP50 = 0.918 değerini **kullanma**. Aşağıda açıklandığı
  gibi veri sızıntılı; gerçek genelleme başarısını göstermiyor.
- ⚠️ `sure_v1` sayıları da tamamen temiz değil: train ve val arasında algısal karma
  ile **32 yakın-kopya kare çifti** bulundu (14'ü komşu indeksli). Etkisi henüz
  sayısallaştırılmadı, yani yukarıdaki mAP50/P/R bir miktar iyimser olabilir.
  Ayrıntı: [`research/experiments/EXP05/`](research/experiments/EXP05/).
- ⚠️ Doğrulama setinde **hiç seyrek kare yok** (1–2 balıklı) — sistemin bu rejimde
  ne yaptığı ölçülmedi.

---

## Sistemdeki iki model

| Model | Ağ | Veri | Rol | Metrik geçerli mi? |
|-------|-----|------|-----|--------------------|
| `sure_v1` | YOLOv11s | 510 görsel (412/98) | **Production tespit** | ✅ Evet (yukarıdaki tablo) |
| `ogretmen` | YOLOv11n | 20 görsel (train=val) | Otomatik etiketleme (tek seferlik) | ❌ Hayır — veri sızıntısı |

`ogretmen` modelinin tek işi `sure_v1`'in eğitim setini etiketlemekti; o işi yaptı.
Ondan performans metriği beklenmiyor.

### Neden `ogretmen` metriği geçersiz

`data/ogretmen.yaml`:

```yaml
train: .../ogretmen_dataset/images
val:   .../ogretmen_dataset/images   # ← AYNI klasör
```

Doğrulama, eğitim görselleriyle yapılmış. Model 20 görseli ezberlemiş ve metrik
kendi eğitildiği veride ölçülmüş.

---

## Yeniden eğitim (gerekirse)

`vision-service/train_sure.py` ayarları: `epochs: 100`, `patience: 40`,
`close_mosaic: 10` (son 10 epoch mosaic kapanır → daha temiz yakınsama).

```bash
cd vision-service
python3 train_sure.py
```

M4 Pro'da batch 8 / 640px ile epoch başına ~1 dk → ~1.5-2 saat.

### Eğitim sonrası kontrol listesi

1. `sure_models/sure_v1/results.png` → mAP eğrisi platoya oturmuş mu?
2. `sure_models/sure_v1/confusion_matrix.png` → false negative oranı.
3. `val_batch0_pred.jpg` → kutular görsel olarak oturmuş mu?
4. Production zaten `sure_v1/best.pt`'ye bağlı; ekstra bir şey gerekmez.

### İsteğe bağlı iyileştirmeler

- Donanım yeterliyse `yolo11s` → `yolo11m` (yavaşlar, doğruluk artar).
- Recall hâlâ düşükse en etkili adım veri setini büyütmek.
- Tek sınıf olduğu için sınıf karışıklığı yok; tüm hata localization + recall tarafında.

---

<details>
<summary><strong>Tarihsel ek — çözülmüş sorunlar (arşiv)</strong></summary>

Bu bölüm 2026-06-05 öncesindeki durumu belgeler. **Sayıları güncel sanma**;
üçü de düzeltildi ve yukarıdaki bölüm geçerli olandır.

### 1. Production yanlış modele bağlıydı — ÇÖZÜLDÜ

`yolo_runner.py` `DEFAULT_MODEL` olarak 20 görselli `ogretmen` ağırlığını
kullanıyordu. `sure_v1/weights/best.pt`'ye çevrildi.

### 2. `sure_v1` eğitimi 5. epoch'ta kesilmişti — ÇÖZÜLDÜ

O dönemki `results.csv` yalnızca 5 satır içeriyordu:

| Epoch | mAP50 | mAP50-95 | Precision | Recall |
|-------|-------|----------|-----------|--------|
| 1 | 0.179 | 0.093 | 0.204 | 0.697 |
| 2 | 0.675 | 0.382 | 0.720 | 0.603 |
| 3 | 0.678 | 0.372 | 0.755 | 0.596 |
| **4** | **0.730** | **0.445** | 0.788 | 0.630 |
| 5 | 0.639 ↓ | 0.385 | 0.781 | 0.551 |

Eğri yakınsamamıştı, recall %55-63 seviyesindeydi. 100 epoch'luk yeniden eğitimle
çözüldü.

### 3. Yeniden eğitimin kazancı

| Metrik | Eski (5 epoch) | epoch 73 (o zaman best.pt sanılan) | Fark |
|--------|----------------|---------------------|------|
| Precision | 0.788 | 0.878 | +0.090 |
| Recall | 0.630 | 0.695 | +0.065 |
| mAP50 | 0.730 | 0.840 | +0.110 |
| mAP50-95 | 0.445 | 0.592 | +0.147 |

</details>

---

## Edge export ölçümü (2026-08-26)

`vision-service/export_bench.py` her formatı **aynı 98 görsellik doğrulama
setinde** koşturur ve mAP ile gecikmeyi birlikte raporlar. Sadece FPS vermek
eksik tablodur; her format doğruluğu bir yerde takas eder.

Gecikme, diskten okuma zamanlanan döngünün dışında kalacak şekilde **önceden
belleğe alınmış** 40 gerçek doğrulama karesi üzerinde, 8 ısınma koşusu atılarak
ölçüldü. Ortalama değil p50/p95: gerçek zamanlı bir hat en kötü karelerine göre
yargılanır.

| Format | Cihaz | mAP50 | ΔmAP50 | mAP50-95 | p50 ms | p95 ms | FPS | Boyut MB |
|--------|-------|------:|-------:|---------:|-------:|-------:|----:|---------:|
| pt | mps | 0.8395 | temel | 0.5952 | 31.4 | 36.7 | 31.8 | 54.5 |
| pt | cpu | 0.8395 | +0.0000 | 0.5952 | 39.2 | 41.0 | 25.5 | 54.5 |
| onnx | cpu | 0.8291 | −0.0104 | 0.5867 | 53.5 | 66.1 | 18.7 | 36.2 |
| onnx-int8 | cpu | 0.8313 | −0.0082 | 0.5863 | 36.2 | 39.2 | 27.6 | **9.4** |
| **coreml** | ANE | 0.8298 | −0.0097 | 0.5840 | **9.0** | **9.5** | **111.2** | 18.2 |
| torchscript | cpu | 0.8291 | −0.0104 | 0.5867 | 52.8 | 54.8 | 18.9 | 36.4 |

### Üç bulgu

**1 · Export'un kendisi doğruluk kaybettiriyor — quantization olmadan da.**
fp32 ONNX ve TorchScript aynı kaybı veriyor: −0.0104 mAP50, ve mAP50-95 dört
haneye kadar birebir aynı (0.5867). İki farklı çalışma zamanının aynı sayıyı
vermesi bunun sayısal gürültü değil **sistematik** olduğunu gösteriyor; kayıp
export edilmiş modellerin izlediği son-işleme yolundan geliyor, ağırlıkların
hassasiyetinden değil. "fp32 export bedavadır" varsayımı burada yanlış.

**2 · INT8 neredeyse bedava, hatta fp32 ONNX'ten iyi.**
5.8 kat küçük (9.4 MB) ve fp32 ONNX'ten hızlı (36.2 ms vs 53.5 ms), kaybı da
daha az (−0.0082 vs −0.0104). Bu ters sonuç quantization'ın doğruluk *artırdığı*
anlamına gelmez; 1. bulguyla birlikte okunmalı — kayıp export yolundan geliyor ve
INT8'in gürültüsü çalışma noktasını tesadüfen biraz lehte kaydırmış. Fark gürültü
bandında.

**3 · Apple Silicon'da CoreML açık ara önde.**
9.0 ms p50 (111 FPS), MPS PyTorch'tan **3.5 kat hızlı**, 3 kat küçük ve p95
kuyruğu en dar olan format (p50'nin yalnızca %6 üstü). ONNX'in kuyruğu ise en
kötüsü (%24). Kuyruk farkı ortalamaya bakınca görünmez.

> **Ölçüm hatası notu.** İlk koşuda gecikme `predict(dosya_yolu)` ile ölçülmüştü
> ve her yinelemede JPEG diskten okunuyordu. Kareler önceden belleğe alınınca
> CoreML 13.9 ms'den 9.0 ms'ye düştü — hata en çok, sonucu en çok çarpıttığı
> yerde önemliydi.

### TensorRT — henüz ölçülmedi

FP16 ve INT8 TensorRT satırları **bu makinede üretilemez**: TensorRT CUDA
gerektirir, geliştirme makinesi Apple Silicon. `vision-service/jetson_bench.py`
(üretmek için `export_bench.py --emit-jetson`) aynı metodolojiyle — aynı
doğrulama seti, aynı yüzdelik gecikme, aynı ısınma — o satırları Jetson üzerinde
üretir ve `jetson_results.json` yazar.

Tabloya uydurma TensorRT sayısı **konmadı**. Jetson hedefi henüz elde yok;
olduğunda satırlar buraya eklenecek.

---

## AQUA-1B karar kalitesi ölçümü (2026-08-28)

`llm-service/eval.py` model modunda ilk kez çalıştırıldı. Ölçtüğü şey: 8 güvenlik
senaryosunda modelin `status` kararı, üretimdeki kural motorunun kararıyla
karşılaştırılıyor.

| Koşu | Uyum | Düşen senaryolar |
|------|-----:|------------------|
| sıcaklık 0.3, tek çekiliş | 4/8 | T01, T04, T06, T07 |
| sıcaklık 0 (deterministik) | 4/8 | T01, T02, T04, T07 |
| sıcaklık 0.3, 3 tekrar | 4/8 | T02, T04, T05, T07 |

### Asıl bulgu: kararlılık, doğruluk değil

Üç koşu da 4/8 veriyor ama **her seferinde farklı senaryolar düşüyor**. Üç
tekrarlı koşuda 8 senaryonun **6'sı aynı girdiye farklı cevap** verdi:

| Senaryo | Üretilen cevaplar |
|---------|-------------------|
| T01 Normal koşullar | ok / warning |
| T02 **Kritik oksijen** | **critical / warning** |
| T03 pH uyarısı | critical / warning |
| T06 Yüksek oksijen | ok / warning |
| T07 **Acil durum, çoklu parametre** | **critical / warning** |
| T08 Balık tespit edilmedi | critical / warning |

"%50 doğru" yanıltıcı bir özet olur. Doğru özet: **modelin kararlı bir görüşü
yok.** Aynı tank durumuna, örnekleme çekilişine göre farklı hüküm veriyor — ve
bu, sistemin var olma sebebi olan iki senaryoda (T02, T07) da oluyor.

### Ayrıştırma

Üç tekrarlı koşuda 2 senaryoda (T01, T06) çıktı 3 koşunun 2'sinde
ayrıştırılamadı. O senaryolarda görünen `ok`, modelin kararı değil güvenli
varsayılan — yani yukarıdaki yüzde bir miktar modeli değil fallback'i ölçüyor.
`eval.py` bunu ayrı raporluyor; ölçmeseydi skor olduğundan iyi görünecekti.

Not: ajan benchmark'ında AQUA-1B format uyumu **%0**'dı. Karar prompt'unda
çoğunlukla geçerli JSON üretiyor. LoRA adaptörü eğitildiği formatı öğretmiş ama
yeni bir formata genellememiş — beklenen davranış.

### Ne anlama geliyor

Mimarinin en baştaki kararı — *model önerir, deterministik kural motoru karar
verir* — bu ölçümle doğrulanıyor. Override dekoratif değil: **4/8 senaryoda
kararı değiştiriyor** ve bunların ikisinde modelin az alarm vermesini yakalıyor.
Kural motoru olmasaydı sistem kritik oksijende zar atışına göre `warning`
diyebilirdi.

LLM'in katkısı **gerekçe üretmek**, yargı değil. Bu artık iddia değil ölçüm.

Tekrar üretmek için:

```bash
cd llm-service
AQUA_ADAPTER_PATH=./sure-aqua-adapter python3 eval.py --repeat 3
```

# S.U.R.E. — Model Başarım Raporu

_Vision (YOLOv11) tespit modeli · son güncelleme: 2026-06-05_

---

## Güncel durum (tez/sunumda kullanılacak sayılar)

Production (`vision-service/yolo_runner.py`) **`sure_models/sure_v1/weights/best.pt`**
ağırlığına bağlıdır. Geçerli metrikler bunlardır:

| Metrik | Değer (best.pt, epoch 73) |
|--------|---------------------------|
| Precision | **0.878** |
| Recall | **0.695** |
| mAP50 | **0.840** |
| mAP50-95 | **0.592** |

- Ağ: YOLOv11s · Veri: 510 görsel (412 train / 98 val) · Tek sınıf: `sturgeon`
- Eğitim: 100 epoch hedefi, epoch 79'da durduruldu, en iyi epoch 73
- Doğrulama seti: 98 görsel / 1525 balık (train'den ayrı)
- Model epoch 62-79 boyunca ~0.84 mAP50'de platoya oturdu

**Kalan zayıf nokta:** Recall ~0.70 — yoğun/örtüşen balıklar kaçırılıyor.
`NMS time limit exceeded` uyarıları ve kalabalık kareler bunu doğruluyor.
Çözüm yönü: yoğun karelerde etiket gözden geçirme + daha yüksek çözünürlük
(imgsz 960/1280), ya da demo için inference'ta `conf` düşürme + `max_det` artırma.

### Sunumda kullanma

- ✅ Yukarıdaki `sure_v1` sayılarını kullan — ayrı doğrulama setinde ölçüldü.
- ❌ `ogretmen` modelinin mAP50 = 0.918 değerini **kullanma**. Aşağıda açıklandığı
  gibi veri sızıntılı; gerçek genelleme başarısını göstermiyor.

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

| Metrik | Eski (5 epoch) | Yeni best.pt (ep73) | Fark |
|--------|----------------|---------------------|------|
| Precision | 0.788 | 0.878 | +0.090 |
| Recall | 0.630 | 0.695 | +0.065 |
| mAP50 | 0.730 | 0.840 | +0.110 |
| mAP50-95 | 0.445 | 0.592 | +0.147 |

</details>

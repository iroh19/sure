# S.U.R.E. — Model Başarım Raporu

_Tarih: 2026-06-05 · Vision (YOLOv11) tespit modeli_

## ✅ GÜNCELLEME — Yeniden eğitim tamamlandı (best.pt = epoch 73)

`sure_v1` 100 epoch hedefiyle yeniden eğitildi (epoch 79'da durduruldu; en iyi
epoch 73, `best.pt` orada kayıtlı):

| Metrik | Eski (5 epoch) | **Yeni best.pt (ep73)** |
|--------|----------------|--------------------------|
| Precision | 0.788 | **0.878** |
| Recall | 0.630 | **0.695** |
| mAP50 | 0.730 | **0.840** |
| mAP50-95 | 0.445 | **0.592** |

Yeniden eğitim işe yaradı: mAP50 **+0.11**, recall **+0.065**, lokalizasyon
(mAP50-95) **+0.15**. Doğrulama seti: 98 görsel / 1525 balık. Model epoch 62-79
boyunca ~0.84 mAP50'de platoya oturdu.

**Kalan zayıf nokta:** Recall ~0.70 — yoğun/örtüşen balıkları kaçırma. NMS
uyarıları (`NMS time limit exceeded`) ve kalabalık kareler bunu doğruluyor.
Çözüm yönü: yoğun karelerde etiket gözden geçirme + daha yüksek çözünürlük
(imgsz 960/1280), ya da demo için inference'ta `conf` düşürme + `max_det` artırma.

> Aşağıdaki "5. epoch'ta kesilmiş" analizi artık **tarihsel referanstır** —
> sorun çözüldü, yukarıdaki sayılar günceldir.

## Özet

Sistemde iki model var ve **ikisinde de sorun var**:

| Model | Ağ | Veri | Epoch | Durum |
|-------|-----|------|-------|-------|
| `ogretmen` | YOLOv11n | 20 görsel (train=val) | 94/100 | Metrikleri **sahte** (veri sızıntısı) |
| `sure_v1` | YOLOv11s | 510 görsel (412/98) | **5/20** | **Yarım kaldı, underfit** |

**En kritik bulgu:** Production (`yolo_runner.py`) yanlış modeli — 20 görselli öğretmeni — kullanıyor.

---

## 1. Production yanlış modele bağlı

`vision-service/yolo_runner.py:34`:

```python
DEFAULT_MODEL = ".../sure_models/ogretmen/weights/best.pt"   # 20 görselli öğretmen
```

Öğretmen modeli (nano, 20 görsel) sadece **otomatik etiketleme** için eğitildi. Gerçek
zamanlı tespitte 510 görselli `sure_v1` (small) çalışmalı. Şu an tank kamerası
20 görselle ezberlemiş bir modele bakıyor.

**Düzeltme yapıldı:** `DEFAULT_MODEL` → `sure_v1/weights/best.pt`. Sen `sure_v1`'i
yeniden eğitince otomatik olarak güçlü model devreye girer.

## 2. Öğretmen modelinin mAP50 = 0.918 değeri geçersiz

`data/ogretmen.yaml`:

```yaml
train: .../ogretmen_dataset/images
val:   .../ogretmen_dataset/images   # ← AYNI klasör
```

Doğrulama (validation) eğitim görselleriyle yapılmış. Model 20 görseli ezberlemiş,
metrik kendi eğittiği veride ölçülmüş. **Bu sayıyı tez/sunumda kullanma** — gerçek
genelleme başarısını göstermiyor. Öğretmen modelinin tek işi etiket üretmekti, o işi
yaptı; performans metriği aramıyoruz.

## 3. `sure_v1` eğitimi 5. epoch'ta kesilmiş

`sure_models/sure_v1/results.csv` sadece 5 satır içeriyor (20 planlanmıştı):

| Epoch | mAP50 | mAP50-95 | Precision | Recall |
|-------|-------|----------|-----------|--------|
| 1 | 0.179 | 0.093 | 0.204 | 0.697 |
| 2 | 0.675 | 0.382 | 0.720 | 0.603 |
| 3 | 0.678 | 0.372 | 0.755 | 0.596 |
| **4** | **0.730** | **0.445** | 0.788 | 0.630 |
| 5 | 0.639 ↓ | 0.385 | 0.781 | 0.551 |

- Eğri hâlâ tırmanışta, yakınsamamış.
- **Recall %55-63** → tanktaki balıkların ~%40'ı tespit edilemiyor.
- Epoch 5'te metrik düştü (mosaic augmentation gürültüsü, normal — daha çok epoch gerek).
- `mAP50-95 ≈ 0.44` → bounding box konumlandırması gevşek.

20 epoch zaten yetersizdi; 5 epoch çok daha yetersiz.

---

## Yeniden eğitim için öneri (kendi bilgisayarında — M-serisi / mps)

`vision-service/train_sure.py` güncellendi:

- `epochs: 20 → 100` (412 görsel + ağır augmentation için makul)
- `patience: 30 → 40` (erken durma marjı)
- `close_mosaic: 10` (son 10 epoch mosaic kapanır → daha temiz yakınsama)

Çalıştır:

```bash
cd vision-service
python3 train_sure.py
```

M4 Pro'da batch 8 / 640px ile epoch başına ~1 dk → ~1.5-2 saat. Eğitim biraz uzun ama
gece bırakılabilir. Beklenti: mAP50'nin 0.73'ten **0.85+** seviyesine, recall'ın
%60'tan %80+ seviyesine çıkması.

### Eğitim sonrası kontrol listesi

1. `sure_models/sure_v1/results.png` → mAP eğrisinin platoya oturduğunu doğrula.
2. `sure_models/sure_v1/confusion_matrix.png` → false negative oranına bak.
3. `val_batch0_pred.jpg` → görsel olarak kutular oturmuş mu kontrol et.
4. Production zaten `sure_v1/best.pt`'ye bağlandı; ekstra bir şey yapmana gerek yok.
5. Sunumda **gerçek** metrik olarak `sure_v1`'in val mAP50'sini kullan (öğretmeninkini değil).

### İsteğe bağlı iyileştirmeler

- Daha yüksek doğruluk + donanım yeterliyse `yolo11s` → `yolo11m` dene (yavaşlar).
- 510 görsel iyi bir başlangıç; recall hâlâ düşükse veri setini büyütmek en etkili adım.
- Tek sınıf (`sturgeon`) olduğu için sınıf karışıklığı yok; tüm hata
  tespit/kaçırma (localization + recall) tarafında.

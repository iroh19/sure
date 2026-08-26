---
doc_id: karar-mantigi
title: Karar Mantığı ve Alarm Önceliği
---

# Karar Mantığı ve Alarm Önceliği

## Üç durum seviyesi

S.U.R.E. karar motoru üç seviye üretir:

- **`ok`** — tüm ölçülen parametreler güvenli aralıkta.
- **`warning`** — en az bir parametre aralık dışında, ancak akut tehlike yok.
  Sıcaklık, pH, TDS sapmaları ve düşük balık aktivitesi bu seviyeyi üretir.
- **`critical`** — çözünmüş oksijen güvenli aralığın dışında. Derhal müdahale
  gerektirir.

## Durum asla aşağı çekilmez

Karar motorunun temel garantisi: bir parametre `critical` üretmişse, başka bir
parametrenin normal olması durumu düşürmez. Seviye yalnızca yukarı yükseltilir.
Bu davranış birim testlerle sabitlenmiştir.

## Dil modeli son söz sahibi değildir

Sistemde büyük dil modeli doğal dilde gerekçe ve öneri üretir, ancak nihai
durumu belirlemez. Deterministik kural motoru her model kararını denetler:

- Model `ok` derken kural motoru `critical` görüyorsa, durum **yükseltilir** ve
  kural motorunun gerekçesi karara eklenir.
- Model bozuk veya eksik bir durum alanı döndürürse, sistem güvenli tarafa düşer.
- Model hiç yanıt vermezse, karar tamamen kural motorundan üretilir.

Bunun nedeni, bir dil modelinin güvenlik-kritik bir eşiği sessizce kaçırmasının
kabul edilemez olmasıdır. Model yanılabilir; 6.0 mg/L eşiği yanılamaz.

## Sensör verisi eksikse

Sensör veya görüntü servisi henüz bağlanmadıysa, ilgili kurallar **atlanır** —
uydurma uyarı üretilmez. Eksik veri, "sorun yok" anlamına gelmediği gibi
"sorun var" anlamına da gelmez; yalnızca o kanaldan karar üretilmez.

## Öneriler

Durum seviyesine göre üretilen standart öneriler:

- **`critical`:** Havalandırmayı ve oksijen pompasını derhal artır. Yemlemeyi
  durdur, suyu kontrol et.
- **`warning`:** Parametreleri yakından izle. Trend kötüleşirse müdahale planı
  hazırla.
- **`ok`:** Mevcut bakım rutinini sürdür.

## Dashboard'daki bağımsız uyarı

Arayüzdeki kritik oksijen bandı, karar motorundan ve dil modelinden **bağımsız
olarak** doğrudan sensör değerinden hesaplanır. Karar zincirinin tamamı arızalansa
bile operatör kritik oksijeni görür.

---
doc_id: sicaklik
title: Su Sıcaklığı Yönetimi
parameter: temperature_c
safe_min: 16.0
safe_max: 21.0
severity: warning
---

# Su Sıcaklığı Yönetimi

## Sistem eşiği

S.U.R.E. sisteminde güvenli su sıcaklığı aralığı **16.0 – 21.0 °C**'dir. Bu
aralık dışındaki ölçümler `warning` seviyesi üretir; sıcaklık tek başına
`critical` sayılmaz, çünkü sapma genellikle kademelidir ve müdahale için saatler
mertebesinde zaman bırakır.

Ancak sıcaklık, diğer tüm parametreleri dolaylı olarak sürükler: oksijen
çözünürlüğünü, amonyağın iyonize olmayan oranını, balığın metabolik hızını ve
biyofiltre verimini aynı anda değiştirir. Bu nedenle sıcaklık sapması tek başına
kritik olmasa da, başka bir sapmayla birlikte görüldüğünde risk çarpan etkisi
yaratır.

## Mersin balığı için sıcaklık toleransı

Mersin balığı ılık-serin su türüdür. Büyüme performansı 18–20 °C civarında
tepe yapar. 16 °C altında metabolizma yavaşlar, yem dönüşüm oranı bozulur ve
büyüme durur — akut tehlike yoktur ama üretim kaybı vardır.

22 °C üzerinde tablo tersine döner: metabolik oksijen talebi artarken suyun
oksijen taşıma kapasitesi düşer. 24 °C üzeri uzun süreli maruziyet kronik strese,
bağışıklık baskılanmasına ve hastalık duyarlılığına yol açar.

## Sıcaklık – oksijen bağlantısı

Suyun oksijen doygunluk değeri sıcaklıkla düşer:

| Sıcaklık | Yaklaşık DO doygunluğu |
|----------|------------------------|
| 16 °C | ~9.9 mg/L |
| 18 °C | ~9.5 mg/L |
| 20 °C | ~9.1 mg/L |
| 22 °C | ~8.7 mg/L |
| 24 °C | ~8.4 mg/L |

Tablo, sıcaklık üst sınıra yaklaşırken oksijen için kalan güvenlik payının
daraldığını gösterir. Sıcaklık 21 °C'ye yaklaşırken DO 7 mg/L civarındaysa,
sistem henüz alarm üretmiyor olsa bile trend tehlikelidir.

## Ani sıcaklık değişimi

Mutlak değer kadar **değişim hızı** da önemlidir. Saatte 2 °C'den hızlı değişim,
mutlak değer güvenli aralıkta kalsa bile termal şok üretir. Su değişimi veya
taze su takviyesi yapılırken gelen suyun sıcaklığı tank suyuna yakın olmalıdır.

## Isı kaynakları ve kontrol

Kapalı devre sistemde ısı üç yerden gelir: pompa ve blower'ların attığı atık
ısı, ortam sıcaklığı ve biyolojik aktivite. Yaz aylarında pompa atık ısısı tek
başına tankı üst sınırın üzerine taşıyabilir.

Kontrol seçenekleri: plakalı ısı değiştirici, chiller, gece saatlerinde artırılan
su değişimi ve tank yalıtımı. Yalıtım hem ısınmayı hem soğumayı yavaşlatır, yani
ani değişime karşı da tampon görevi görür.

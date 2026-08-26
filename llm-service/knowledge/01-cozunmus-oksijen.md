---
doc_id: cozunmus-oksijen
title: Çözünmüş Oksijen (DO) Yönetimi
parameter: dissolved_oxygen_mgl
safe_min: 6.0
safe_max: 12.0
severity: critical
---

# Çözünmüş Oksijen (DO) Yönetimi

## Sistem eşiği

S.U.R.E. kapalı devre sisteminde mersin balığı için güvenli çözünmüş oksijen
aralığı **6.0 – 12.0 mg/L**'dir. Bu aralığın dışına çıkan her ölçüm doğrudan
`critical` seviyesine yükseltilir. Çözünmüş oksijen, sistemdeki **tek başına
kritik** parametredir; sıcaklık, pH ve TDS sapmaları uyarı seviyesinde kalırken
DO sapması derhal müdahale gerektirir.

Bu ayrımın nedeni tepki süresidir. pH'ın 6.2'ye düşmesi saatler içinde telafi
edilebilir; oksijenin 4 mg/L'ye düşmesi ise dakikalar içinde ölüme yol açabilir.

## Neden mersin balığı için kritik

Mersin balığı (Acipenser spp.) dip yaşamına uyarlanmış, görece yüksek oksijen
talebi olan bir türdür. Solungaç yüzeyi ve kan oksijen taşıma kapasitesi, hızlı
yüzen pelajik türlere göre daha dar bir güvenlik payı bırakır. Oksijen 5 mg/L
altına indiğinde yem alımı belirgin şekilde düşer; 4 mg/L altında solungaç
hasarı ve kronik stres başlar; 3 mg/L altında akut ölüm riski oluşur.

## Oksijen düşüşünün tipik nedenleri

**Biyolojik yük artışı.** Stok yoğunluğu veya balık biyokütlesi arttıkça
solunum tüketimi artar. Yemleme sonrası 1–3 saatlik pencerede oksijen talebi
tepe yapar; bu, günün en riskli aralığıdır.

**Sıcaklık artışı.** Suyun oksijen çözme kapasitesi sıcaklıkla ters orantılıdır.
20 °C'de doygunluk yaklaşık 9.1 mg/L iken 25 °C'de 8.2 mg/L'ye iner. Aynı anda
balığın metabolik oksijen talebi de artar — çift yönlü baskı oluşur.

**Havalandırma arızası.** Blower, difüzör tıkanması veya oksijen konisi
beslemesinin kesilmesi en hızlı düşüşü üretir. Kapalı devre sistemde su hacmi
küçük olduğu için tampon süresi kısadır.

**Biyofiltre aşırı yüklenmesi.** Nitrifikasyon bakterileri de oksijen tüketir.
Ani yem artışı veya organik madde birikimi biyofiltrenin oksijen tüketimini
yükseltir.

**Elektrik kesintisi.** Sirkülasyon durduğunda hem havalandırma hem de tank içi
karışım kaybolur; tabanda oksijen katmanlaşması oluşur ve dip yaşayan mersin
balığı en düşük oksijenli katmanda kalır.

## Müdahale sırası

Ölçüm 6.0 mg/L altına düştüğünde uygulanacak sıra:

1. **Havalandırmayı ve oksijen beslemesini derhal maksimuma çıkar.** Yedek
   blower varsa devreye al.
2. **Yemlemeyi durdur.** Sindirim oksijen tüketiminin en büyük tek kalemidir;
   yemlemeyi kesmek talebi hızla düşürür.
3. **Su değişimini artır.** Taze su takviyesi hem oksijen getirir hem metabolik
   atıkları seyreltir.
4. **Sıcaklığı kontrol et.** Sıcaklık üst sınıra yakınsa soğutma, oksijen
   çözünürlüğünü doğrudan artırır.
5. **Balık davranışını gözle.** Yüzeye çıkma ve ağız solunumu (piping),
   oksijenin sensör ölçümünden daha kötü olduğunun işaretidir.

## Aşırı doygunluk riski

Üst sınır olan 12.0 mg/L keyfi değildir. Saf oksijen enjeksiyonu yapılan
sistemlerde aşırı doygunluk gaz kabarcığı hastalığına (gas bubble disease) yol
açabilir: gazlar balığın dokularında kabarcık oluşturur. 12 mg/L üzeri ölçümler
de bu nedenle uyarı üretir ve oksijen beslemesinin kısılmasını gerektirir.

## Sensör güvenilirliği

Optik DO probları zamanla biyofilm kaplar ve **gerçekte olduğundan yüksek**
değer okumaya başlar — yani tehlikeyi gizler. Probun haftalık temizliği ve
aylık kalibrasyonu, sistemin en kritik bakım kalemidir. Sensör değeri normal
görünürken balıkta solunum sıkıntısı belirtisi varsa, öncelik sensöre değil
davranışa verilmelidir.

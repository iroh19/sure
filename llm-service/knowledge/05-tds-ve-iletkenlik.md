---
doc_id: tds-ve-iletkenlik
title: TDS ve İletkenlik
parameter: tds_ppm
safe_min: 200.0
safe_max: 450.0
severity: warning
---

# TDS ve İletkenlik

## Sistem eşiği

S.U.R.E. sisteminde güvenli toplam çözünmüş katı (TDS) aralığı
**200 – 450 ppm**'dir. Bu aralık dışındaki ölçümler `warning` seviyesi üretir.

## TDS ne ölçer, ne ölçmez

TDS, sudaki çözünmüş iyonların toplam derişimini gösterir: kalsiyum, magnezyum,
sodyum, klorür, sülfat, bikarbonat ve birikmiş nitrat. Pratikte iletkenlik
ölçülür ve sabit bir katsayıyla TDS'e çevrilir.

TDS **hangi** iyonun biriktiğini söylemez. 400 ppm okuması sağlıklı bir mineral
dengesinden de, birikmiş nitrattan da gelebilir. Bu yüzden TDS tek başına değil,
trend olarak ve pH ile birlikte yorumlanmalıdır.

## Düşük TDS'in riski

200 ppm altındaki TDS, suyun mineral bakımından fakirleştiğini gösterir. Sonuçlar:

- **Ozmotik stres.** Tatlı su balığı sürekli su alıp tuz kaybeder; çok yumuşak
  suda bu yük artar ve enerji büyümeden çalınır.
- **Alkalinite kaybı.** Düşük TDS genellikle düşük alkaliniteyle birlikte gelir;
  sistem pH tamponunu yitirir ve pH ani düşer.
- **Biyofiltre verimi düşer.** Nitrifikasyon bakterileri iyon eksikliğinden
  etkilenir.

Genellikle aşırı su değişimi veya ters ozmoz suyu kullanımı sonrası görülür.
Çözüm mineral takviyesi ve alkalinite ayarıdır.

## Yüksek TDS'in riski

450 ppm üzerindeki TDS, kapalı devre sistemde neredeyse her zaman **atık
birikimidir** — özellikle nitrat ve tuzlar. Su değişiminin yetersiz kaldığını
gösterir.

Yüksek TDS'in kendisi mersin balığı için akut toksik değildir; asıl mesaj
taşıdığı bilgidir: sistem kendi atığını temizleyemiyor. Bu okuma görüldüğünde
nitrat manuel olarak test edilmelidir.

## Trend, mutlak değerden önemlidir

Sabit 380 ppm sağlıklı bir sistemi gösterebilir. Üç günde 250'den 420'ye çıkan
bir TDS ise, her iki değer de aralık içinde olmasına rağmen ciddi bir sorundur:
su değişimi durmuş veya yemleme aşırı artmıştır. Karar motoru anlık değeri
denetler; trendi operatörün dashboard grafiğinden okuması beklenir.

---
doc_id: davranis-ve-refah
title: Davranışsal Refah Göstergeleri
parameter: avg_activity
activity_min: 0.002
severity: warning
---

# Davranışsal Refah Göstergeleri

## Sistem eşiği

S.U.R.E. görüntü işleme servisi her kare için iki metrik üretir: **balık sayısı**
(`fish_count`) ve **normalize ortalama hareket hızı** (`avg_activity`).
Ortalama aktivite **0.002** eşiğinin altına düştüğünde sistem `warning` üretir.

Ayrıca **hiç balık tespit edilmemesi de uyarı üretir.** Bunun iki olası anlamı
vardır ve ikisi de müdahale gerektirir: ya görüntü servisi arızalanmıştır, ya da
sürü tankın dibine çökmüştür. İkincisi ağır stresin klasik işaretidir.

## Neden davranış, sensörden önce haber verir

Su kalitesi sensörleri tankın belirli bir noktasını ölçer. Balık ise tüm hacmi
dolaşır ve koşulları bütünsel yaşar. Oksijen katmanlaşması, lokal ölü bölge veya
sensörün biyofilm nedeniyle yüksek okuması durumlarında **davranış, sensörden
önce bozulur.**

Bu nedenle görüntü tabanlı metrikler sensör verisinin yedeği değil, bağımsız bir
kanaldır.

## Stres göstergeleri

**Aktivite düşüşü (letarji).** Hareket hızının eşiğin altına inmesi; genellikle
düşük oksijen, düşük sıcaklık veya hastalığın erken işaretidir.

**Dipte kümelenme.** Mersin balığı zaten dip yaşar, ancak hareketsiz ve toplu
halde dipte kalma normal dip davranışından ayrılır ve stres göstergesidir.

**Yüzeye çıkma ve ağız solunumu.** Dip yaşayan bir türün yüzeye çıkması ciddi
oksijen sıkıntısının işaretidir. Bu davranış görüldüğünde sensör değeri normal
okusa bile oksijen müdahalesi başlatılmalıdır.

**Aşırı ve düzensiz hareket.** Ani hızlanma, tank duvarına çarpma ve dönme
hareketi; genellikle toksik madde, ani pH kayması veya yüksek amonyağa işaret
eder.

**Yem alımının kesilmesi.** Refahın en güvenilir tek göstergesi. Su kalitesi
parametreleri normal görünürken yem alımı düşüyorsa, henüz ölçülmeyen bir
parametre (amonyak, nitrit, CO₂) bozulmuş demektir.

## Aktivite metriğinin sınırları

Normalize hareket hızı, tespit edilen kutuların kareler arası yer değiştirmesinden
hesaplanır. İki bilinen zayıflık vardır:

- **Kalabalık karelerde takip kimliği karışabilir**; bu, gerçekte olmayan yüksek
  hareket üretir.
- **Tespit modelinin recall'ı, sistemin koştuğu `conf=0.20` eşiğinde 0.782'dir**;
  yoğun karelerde balıkların bir kısmı kaçırılır, ortalama gerçekte olduğundan
  farklı çıkabilir.

Bu yüzden aktivite metriği tek başına `critical` üretmez; yalnızca uyarı
seviyesindedir ve sensör verisiyle birlikte yorumlanır.

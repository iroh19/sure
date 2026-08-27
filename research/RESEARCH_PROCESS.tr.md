# S.U.R.E. Makalesi Nasıl Araştırıldı ve Yazıldı

### pAI/MSc ile yürütülmüş bir ajan tabanlı araştırma koşusunun kaydı — insan döngü üzerinde

**Proje:** S.U.R.E. (Aquaculture Welfare Integration) — Kapalı Devre Su Ürünleri Yetiştiriciliği
Sistemlerinde Edge-AI ve RAG Destekli Deterministik Füzyon ile Otonom Mersin Balığı Refah İzleme
**Makale yazarları:** Batuhan Çıtak, Erdem Sabri Veli
**Koşu aralığı:** 26–27 Ağustos 2026
**Çıktılar:** Bu depodaki [`research/`](.) dizini

---

## 1. Bu belge neden var

[`SURE-paper.pdf`](SURE-paper.pdf) dosyasındaki makale elle yazılmadı. **pAI/MSc** adlı, MIT
kaynaklı bir araştırma ajanı tarafından, biz insanlar döngünün üzerinde kalarak üretildi. Bu hattın
ürettiği her ara çıktı, makaleyle birlikte [`pipeline/`](pipeline/) ve
[`experiments/`](experiments/) altında bu depoya işlendi.

Yalnızca ürünü değil süreci de yayımlıyoruz; üç nedenle:

1. **Şeffaflık.** Makine destekli bir makaleyle karşılaşan okuyucu, onun nasıl üretildiğini ve insan
   yargısının nereye girdiğini bilmeyi hak eder. Makale bunu teşekkür bölümünde ve sayfa filigranında
   zaten belirtiyor; bu belge aynı beyanın uzun hâli.
2. **Denetlenebilirlik.** Hattın en değerli çıktısı metin değildi. Kendi sistemimiz hakkında
   inandığımız birkaç şeyi çürüten on bir yürütülmüş deneydi. Bu çelişkiler ham loglarıyla birlikte
   [`experiments/`](experiments/) altında duruyor ve herkes yeniden kontrol edebilir.
3. **Yöntem.** Hâlihazırda kurulmuş bir sistemin üzerinde bir araştırma ajanı çalıştırmak, "yapay
   zekâya makale yazdırmak"tan gerçekten farklı bir iş çıktı. Bu belge, rahatsız edici yerler dâhil,
   ne olduğunu anlatıyor.

---

## 2. pAI/MSc nedir

pAI/MSc, MIT teknik raporu *"pAI/MSc: ML Theory Research with Humans on the Loop"* içinde
tanımlanan bir araştırma hattıdır; yazarları Mahmoud Abdelmoneum, Pierfrancesco Beneventano ve
Tomaso Poggio (MIT, Technical Report v0, 2026) — <https://dspace.mit.edu/handle/1721.1/165377>.

Tasarım öncülü şu: bir araştırma ajanı tek bir uzun prompt olmamalı. Bunun yerine, farklı ajanların
birbiriyle tartıştığı, literatür taramasının araştırmacının kendi özgünlük iddialarına karşı
düşmanca (adversarial) yürütüldüğü, deneylerin *onları koşturan ajandan bağımsız biçimde*
doğrulandığı ve insana yalnızca birkaç kritik noktada karar sorulduğu aşamalı bir hat. "Humans on
the loop" ifadesi tam olarak bunu anlatıyor: insan her adımın içinde değil, döngünün üzerinde.

Makale bu raporu `pAIMSc_2026` olarak kaynak gösteriyor ve teşekkür bölümünde şunu belirtiyor: *"We
partially used pAI/MSc for this manuscript."* Derlenmiş PDF ayrıca her sayfasında düşük kontrastlı
bir arka plan filigranı taşıyor: *"Generated with a research agent created by Pierfrancesco
Beneventano."* Bu filigran kasıtlıdır ve aracın atıf gerekliliğinin bir parçasıdır — bir render
hatası değildir.

**Buradaki "kısmen" tam olarak ne demek:** hakkında yazılan sistemin kendisi — kod, modeller, eğitim
koşuları, görüntü veri seti — bize ait ve makaleden önce vardı. Hat; literatür temellendirmesini,
deney tasarımını, deneylerin mevcut kod tabanımız üzerinde yürütülmesini, bağımsız doğrulamayı ve
metin yazımını yaptı. §6'daki nihai olgusal düzeltmeler ise bize aittir.

---

## 3. Ona verdiğimiz girdi

Tek girdi [`pipeline/research_task.md`](pipeline/research_task.md) idi — sistemi, mimariyi, elimizdeki
ampirik sayıları ve istediğimiz çerçeveyi anlatan bir sayfalık bir brief. Yanında, ajanın idealize
edilmiş bir sistem yerine gerçekten var olan sistem hakkında yazması için deponun kendi `README.md`,
`MODEL_RAPORU.md`, `PLAN.md` ve `TODOS.md` dosyalarını bağlam olarak verdik.

Bu brief sonra [`pipeline/vision.md`](pipeline/vision.md) dosyasına dondurulur — hattın üzerine
yazmasına izin verilmeyen, salt-okunur bir "vizyon kilidi". Sonraki her aşamadaki her persona,
herhangi bir öneriyi değerlendirmeden önce orijinal brief'i okur; böylece koşu, gerçekte istediğimiz
şeyden sessizce uzaklaşamaz. Bu önemliydi: hat, koşunun sonunda o brief'teki çerçeveye *karşı* argüman
üretiyordu ve bu anlaşmazlığı görünmez değil okunabilir kılan şey tam da o kilit.

---

## 4. Hattın aşamaları

Makine tarafından okunabilir tam kayıt [`pipeline/state.json`](pipeline/state.json); zaman damgalı
faz zaman çizelgesi [`pipeline/token_summary.json`](pipeline/token_summary.json). Yaklaşık yirmi altı
saatlik takvim süresi içinde kırk dört ajan çağrısı.

### 4.1 Persona konseyi (3 tur)

Üç düşmanca hakem personası — **pratik**, **titizlik (rigor)** ve **anlatı** — öneriyi bağımsız
olarak eleştirdi, ardından bir sentez turu geldi; bu üçü de `ACCEPT` dönene kadar üç tur tekrarlandı.
Tam metinleri [`pipeline/personas/`](pipeline/personas/) altında.

Hasarı veren, titizlik personasıdır. Makalenin merkezî iddiasının orijinal brief'imizdekinden daha
dar olmasının sebebi odur.

### 4.2 Düşmanca literatür taraması

Tek geçiş, 31 atıf ve asıl önemli sayı: **iddialarımızın 11'i çürütüldü ya da zayıflatıldı.**

Manşet sonuç hem rahatsız ediciydi hem de doğruydu: deterministik bir kural motorunun bir LLM'in
şiddet kararı üzerinde nihai yetkiyi elinde tuttuğu "özgün" çift katmanlı mimarimiz `EQUIVALENT_KNOWN`
olarak sınıflandırıldı. Bu, Safety Instrumented Systems kalıbıdır (IEC 61508 / 61511), RL shielding'dir
ve sektörün standart LLM-guardrail düzenlemesidir. Yerleşik bir fikre bağımsız olarak varmıştık ve
onu yeni diye sunmak üzereydik.

Taramanın önerisi "makaleyi bırakın" değildi. Katkıyı **katmanlar arası tutarlılık kompozisyonu**
(cross-layer consistency composition) olarak yeniden çerçevelemekti — makale şu anda tam olarak bunu
savunuyor. Bkz. [`pipeline/literature_review.md`](pipeline/literature_review.md) ve
[`pipeline/novelty_flags.json`](pipeline/novelty_flags.json).

### 4.3 Beyin fırtınası ve hedeflerin formalizasyonu

48 aday yaklaşım üretildi ([`pipeline/brainstorm.md`](pipeline/brainstorm.md)) ve ön kayıtlı başarı
ölçütleriyle birlikte **11 biçimsel araştırma hedefine** damıtıldı. Bunlara ön kayıtlı *yedek*
bulgular da dâhildi: bir hipotezin güçlü hâli tutmazsa ne rapor edileceği
([`pipeline/research_goals.json`](pipeline/research_goals.json)). Ayrışma kapısı, işin teorik değil
ampirik olduğuna karar verdi; bu yüzden teori hattı hiç koşmadı.

**İnsan kontrol noktası #1.** Hat burada durdu ve deneylere işlem gücü harcamadan önce hedefleri
onaylamamızı istedi. Ampirik hattı onayladık.

Ön kayıt, bir sonraki bölüme dişini veren şeydir: yedek bulgular deneyler koşmadan *önce* yazıldığı
için, hat hayal kırıklığı yaratan bir sonucu sonradan "zaten aradığımız buydu" diye yeniden
çerçeveleyemedi.

### 4.4 On bir deney

[`experiments/experiment_design.json`](experiments/experiment_design.json) içinde tasarlandı, gerçek
kod tabanımız üzerinde üç paralel grup hâlinde yürütüldü; EXP10 ve EXP11 en sonda bir finalizasyon
geçişi olarak koşturuldu. Her birinin ham betiği, stdout logu ve sonuç dosyaları
`experiments/EXP01/` … `experiments/EXP11/` altında.

### 4.5 Bağımsız doğrulama

Ayrı bir doğrulayıcı ajan, özetlere güvenmek yerine her manşet metriği diskteki ham çıktı
dosyalarından yeniden hesapladı — **8 PASS, 3 PARTIAL, 0 FAIL**
([`experiments/verification_report.md`](experiments/verification_report.md)). Örneklem küçük olduğu
yerlerde (n=8, n=9, n=98) doğrulayıcı bunu satır içinde söylüyor; sayıyı niteliksiz bırakmıyor.

Tamamlanma oranı **0.95**, tavsiye `COMPLETE`
([`pipeline/verify_completion.json`](pipeline/verify_completion.json)).

### 4.6 Yazım, hakemlik ve revizyon

Yazıma geçmeden *önce* ikinci bir persona konseyi koştu, bir anlatı-ses geçişi tonu belirledi,
ardından iki tam yazım döngüsü, redaksiyon ve simüle edilmiş bir hakem değerlendirmesi geldi. Hakem
makaleyi **10 üzerinden 8** puanladı — sağlamlık 3, sunum 4, katkı 3, açıklık 4, özlülük 3 —
`ai_voice_risk: low`, **sıfır sert engel** ve tek bir zorunlu düzeltme
([`pipeline/review_verdict.json`](pipeline/review_verdict.json), tam rapor:
[`pipeline/review_report.pdf`](pipeline/review_report.pdf)).

O tek zorunlu düzeltme, doğrulayıcının ne işe yaradığının iyi bir örneği: giriş bölümü eskimiş bir
sayının "düzeltmeden haftalar sonra" fark edildiğini iddia ediyordu; §6.6 ve Bilinen Kısıtlar ise
"43 dakikalık commit farkı" diyordu. Hakem gerçek git log'una baktı, `0e8b414` ve `9a260af`
commit'lerinin aynı gün 43 dakika arayla atıldığını buldu ve girişi yalnızca tutarsız değil, olgusal
olarak yanlış diye işaretledi. Düzeltildi.

Son bir hakemlik-sonrası persona konseyi iki tur boyunca üç personadan da `ACCEPT` döndü, sıfır
anlatı vetosuyla. Hattın beş kapısının tamamı — fizibilite, hat ayrıştırma, ikilik, hakem kalitesi,
hakemlik-sonrası personalar — geçildi.

---

## 5. Deneyler gerçekte ne buldu

Asıl okunmaya değer bölüm burası. Birkaç sonuç, brief'i yazarken inandığımız şeyle çelişiyor.

| # | Soru | Bulgu |
|---|---|---|
| **EXP01** | RAG erişimi gerçek mi, yoksa 8 belgelik küçücük bir korpusun yan ürünü mü? | Gerçek. `e5-small`, rastgele referans çizgisini **hit@1 +0.586** (0.793'e karşı 0.207) ve **MRR +0.438** ile geçiyor. Yapılandırılmış 0.85 eşiğinin, F1-argmax olan 0.84'e karşı kesinlik-lehine olduğu doğrulandı. |
| **EXP02** | Değerlendirme koşum hattı ile çalışma zamanı yolu *aynı* kuralları mı işletiyor? | Evet — çıktı karşılaştırmasıyla değil, modül-kimliği kontrolüyle kanıtlandı. 8/8 senaryo uyumu. |
| **EXP03** | **Çift katmanlı sistem gerçekte nasıl davranıyor?** | **Merkezî sonuç ve beklediğimiz sonuç değil.** 8 senaryoda: kural motoru LLM'in düşük tahminini gerçekten **1 vakada (%12)** yakaladı; **4 vakada (%50)** ise modelin çıktısı ayrıştırılamadığı için güvenli tarafa düştü. Baskın güvenlik mekanizması hata düzeltme değil — bozuk çıktıda güvenli varsayılana düşmek. Dahası: **8 gerekçe metninden 6'sı**, girdide hiç bulunmayan **uydurulmuş sensör değerleri** içeriyordu; bunlara modelin nihai kararının kurallarla *uyuştuğu* kova da dâhil. Yalnızca çıktıya bakan bir değerlendirme bunu göremez. |
| **EXP04** | Daha büyük AQUA-7B modeli araç seçimini daha iyi mi yapıyor? | Hayır. Düşmanca bir yeniden koşumun ardından **9/9 bağımsız senaryoda** sürekli aynı ilk aracı seçiyor. Korunmuş bir negatif sonuç. |
| **EXP05** | Görüntü veri setinde eğitim/doğrulama sızıntısı var mı? | Algısal karma (perceptual hash) ile **32 yakın-kopya kare çifti** bulundu (14'ü komşu indeksli). `PARTIAL` işaretlendi — sayıldı ama henüz düzeltilmiş bir manşet metriğe dönüştürülmedi. |
| **EXP06** | ONNX/TorchScript dışa aktarımları doğruluk kaybediyor mu? | Hayır. Görünen kayıp, **ortak son-işleme kaynaklı bir yapaylık** — 98 tespitin 0'ı anlamlı biçimde farklıydı. |

| # | Soru | Bulgu |
|---|---|---|
| **EXP07** | Manşet recall değeri, gerçekte çalıştığımız recall mı? | **Hayır.** Yapılandırılmış çalışma noktası (conf=0.20) **recall 0.782** veriyor; yaygın olarak alıntılanan 0.719 ise F1-argmax optimumu. İkisi de doğru; farklı sorulara cevap veriyorlar ve makale artık ikisini ayrı ayrı raporluyor. Doğrulama seti ayrıca **hiç seyrek (k=1, k=2) kare içermiyor** — tümüyle test edilmemiş bir rejim. |
| **EXP08** | Eşit genişlikli PSI kutulaması kesinlikle daha mı iyi? | **Hayır — iddiamızın düzeltilmesi gerekti.** Küçük dağılım kaymalarında *daha az* duyarlı, büyüklerinde ise belirli bir kutu boşaldığı için *daha patlayıcı*. Monotonik değil. |
| **EXP09** | `twin_bridge` sağlam mı? | Mevcut 19 testin 18'i geçiyor; tek hata bir test yardımcısındaki bug. Git'te takip edilmiyordu, commit geçmişi yoktu. |
| **EXP10** | Makalenin merkezî iddiası bu hâliyle savunulabilir mi? | Daraltılması önerildi. Yükseltme işlevi koşulsuz güvenli-varsayılana düşmedir, sofistike hata düzeltme değil; ve **uydurulmuş-ama-kararı-doğru gerekçelere karşı sıfır koruma** var. |
| **EXP11** | Sistemdeki sayılar makaledeki sayılarla tutarlı mı? | **Canlı bir veri bütünlüğü hatası.** `llm-service/knowledge/06-davranis-ve-refah-gostergeleri.md:58` hâlâ recall ≈ 0.695 diyor — aşılmış bir değer — ve bu dosya **RAG vektör deposuna gerçekten besleniyor**; yani erişim katmanı eskimiş bir sayıyı servis edebilir. Toplamda altı eskimiş veya tutarsız değer kataloglandı. |

Makalenin özeti artık orijinal çerçevemizi değil EXP03 ve EXP10'u yansıtıyor. Öne sürdüğü iddia
bilinçli olarak dar ve yanlışlanabilir: böyle bir hat, güvenilmez bir modele karşı güvenli hâle
getirilebilir — *ancak doğrulayıcısı tek bir sayılabilir alandan fazlasını okumuyorsa ve her zaman
muhafazakâr varsayılana düşüyorsa.* Bu, arayüz tasarımı hakkında bir iddiadır; modelin güvenilir
kılındığı iddiası değil.

---

## 6. Hat bittikten sonra kendimizin yaptığı düzeltmeler

Hat tamamlandı ve tüm kapılarını geçti. Sonrasında makaleyi yeniden açtık ve onun kendi başına
yapamayacağı düzeltmeleri yaptık; çünkü bunlar yalnızca bizim bildiğimiz olgulara dayanıyordu.
Tamamı [`pipeline/state.json`](pipeline/state.json) içinde `post_completion_human_revision` altında
kayıtlı.

**Makale geneline yayılmış olgusal bir aşırı-iddia.** Taslak, S.U.R.E.'ün canlı, sahaya kurulmuş bir
sistem olduğunu ima ediyordu. Değil. Şu maddeler artık Giriş'te, Deneysel Kurulum'da ve Bilinen
Kısıtlar'ın ilk maddesi olarak açıkça belirtiliyor:

- **Hiçbir test gerçek fiziksel sensör veya çalışan bir RAS tesisi kullanmadı.** Böyle bir sensör
  donanımı mevcut değil. Tüm deneylerdeki her sensör okuması **sentetik olarak üretildi**, kaydedilmedi.
- **510 görüntülük görüntü veri seti gerçek** — fiziksel düzeneğin kamera görüntüleri, elle
  etiketlenmiş — ama kasıtlı olarak küçük; genişletilmesi planlanıyor.
- **TEKNOFEST'e katılmadık** — S.U.R.E.'ün kendisi için geliştirildiği yarışma — ve ön değerlendirme
  turunu geçemedik.
- **Asıl katkı bir fizibilite ve kaynak yönetimi gösterimidir** — bu biçimdeki çok bileşenli bir
  hattın uç (edge) donanımın bellek ve işlem bütçesine sığıp sığmadığını sınamak — **karar
  doğruluğunun saha validasyonu değil.**

"Deployed", "production" ve "real-world" ifadelerinin her kullanımı on bir bölümün tamamında yeniden
okundu. Bir *yapılandırma parametresi değerine* yapılan meşru atıflar korundu; canlı saha operasyonu
ima eden her şey "implemented" veya "offline, bench-level evaluation" olarak düzeltildi.

**Üç şekil render hatası.** Şekil 2'de çakışan açıklamalar, Şekil 3'te y eksenini bozan ve bir eksen
etiketinin üzerine çizen menzil dışı bir açıklama, Şekil 4'te eşik etiketlerinin üstünden geçen PSI
eğrileri — hepsi [`paper/figures/make_figures.py`](paper/figures/make_figures.py) içinde açık eksen
sınırları, beyaz metin kutuları ve birbirine çok yakın noktalar için ayrık kılavuz oklarıyla
düzeltildi; her şekil öncesi ve sonrasıyla render edilip gözle kontrol edilerek doğrulandı.

Düzeltilmiş makale 32 sayfa olarak, sıfır hatayla yeniden derleniyor.

---

## 7. Yöntem hakkında dürüst bir değerlendirme

**Nerede açıkça işe yaradı.** Düşmanca literatür taraması, bilinen bir kalıbı özgün diye
yayımlamamızı engelledi. Ön kayıtlı yedek bulgular sayesinde EXP03'ün hayal kırıklığı yaratan sonucu
sessizce yeniden çerçevelenmek yerine bulgu olarak raporlandı. Bağımsız doğrulama — özetleri okumak
yerine ham dosyalardan yeniden hesap yapan ikinci bir ajan — kendi içinde tutarlı bir taslağın
yayına kadar taşıyacağı "haftalar" / "43 dakika" hatasını yakaladı. EXP11 ise makale yazmakla hiç
ilgisi olmayan, canlı kod tabanındaki gerçek ve düzeltilmemiş bir hatayı buldu.

**İnsanın vazgeçilmez olduğu yer.** §6'daki düzeltmelerin tamamı bizden geldi. Hattın; sensörlerimizin
sentetik olduğunu, donanımın hiç var olmadığını ya da yarışmaya hiç katılmadığımızı bilmesinin bir
yolu yoktu, çünkü depoda bunu söyleyen hiçbir şey yoktu — ve o boşluğun etrafına kendinden emin, iyi
kaynaklandırılmış, kendi içinde tutarlı bir makale yazdı. Bir araştırma ajanı, ona verdiğiniz
öncülleri sadakatle uzatır. Öncülleri denetlemek, devredilebilecek bir adım değildir.

**Sınırları.** Örneklem, en çok ağırlık taşıyan yerlerde küçük: merkezî davranışsal sonuç n=8. Üç
deney `PARTIAL` ve EXP05'in sızıntı bulgusu sayıldı ama henüz düzeltilmiş bir manşet görüntü
metriğine yansıtılmadı — açık bir görev ve makalede üstü örtülmek yerine böyle ifade ediliyor.

---

## 8. Yeniden üretme ve yeniden kontrol

```bash
# Makaleyi kaynaktan yeniden derle (bir TeX dağıtımı gerekir)
cd research/paper
pdflatex final_paper.tex && bibtex final_paper && pdflatex final_paper.tex && pdflatex final_paper.tex

# Beş şekli yeniden üret
cd research/paper/figures && python make_figures.py
```

[`experiments/`](experiments/) altındaki her deney dizini, koşturulan betiği, stdout logunu ve sonuç
dosyalarını içerir. Doğrulayıcının her manşet sayıyı bağımsız olarak yeniden hesaplaması
[`experiments/verification_report.md`](experiments/verification_report.md) içindedir.

Boyut nedeniyle tek bir dosya dışarıda bırakıldı: `EXP05/near_duplicate_pairs_full.json`
(2.4 MB, tam algısal-karma çift dökümü). Toplulaştırılmış değerleri `EXP05/exp05_summary.json`
içinde ve onu üreten denetim betiği `EXP05/exp05_leakage_audit.py` depoya işlenmiş durumda.

---

## 9. Atıf

S.U.R.E. sisteminin kendisi — backend, görüntü servisi, LLM servisi, MLOps ve dijital ikiz köprüsü —
yazarların kendi çalışmasıdır ve bu makaleden öncedir.

Makale, MIT'de Mahmoud Abdelmoneum, Pierfrancesco Beneventano ve Tomaso Poggio tarafından
geliştirilen **pAI/MSc** araştırma ajanıyla üretilmiştir ve makalenin kaynakçasında ve teşekkür
bölümünde bu şekilde belirtilmiştir. Derlenmiş PDF'in her sayfasındaki arka plan filigranı, o aracın
atıf gerekliliğinin bir parçasıdır.

> Abdelmoneum, M., Beneventano, P., & Poggio, T. (2026). *pAI/MSc: ML Theory Research with Humans on
> the Loop.* MIT Technical Report v0. <https://dspace.mit.edu/handle/1721.1/165377>

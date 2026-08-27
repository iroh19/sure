# Araştırma

[🇬🇧 English](README.md)

S.U.R.E.'ün akademik makalesi ve nasıl üretildiğinin eksiksiz kaydı.

Makale, MIT kaynaklı ajan tabanlı bir araştırma hattı olan **pAI/MSc** ile
([Abdelmoneum, Beneventano & Poggio, 2026](https://dspace.mit.edu/handle/1721.1/165377)) ve biz
insanlar döngünün üzerinde kalarak yazıldı. Hattın ürettiği her ara çıktı burada — yalnızca bitmiş
makale değil.

## Buradan başlayın

| | |
|---|---|
| 📄 **[SURE-paper.pdf](SURE-paper.pdf)** | Makale. 32 sayfa, 56 kaynak, 5 şekil. |
| 📘 **[SURE-arastirma-sureci.pdf](SURE-arastirma-sureci.pdf)** · [markdown](RESEARCH_PROCESS.tr.md) | **Araştırmanın gerçekte nasıl yapıldığı** — hat, deneylerin bulduğu şeyler ve sonradan düzeltmek zorunda kaldıklarımız. |
| 📘 [SURE-research-process.pdf](SURE-research-process.pdf) · [markdown](RESEARCH_PROCESS.md) | Yukarıdakinin İngilizce sürümü. |

## Burada ne var

```
research/
├── SURE-paper.pdf              makale
├── SURE-arastirma-sureci.pdf   nasıl üretildi (TR) — kaynak: RESEARCH_PROCESS.tr.md
├── SURE-research-process.pdf   nasıl üretildi (EN) — kaynak: RESEARCH_PROCESS.md
├── paper/                      LaTeX kaynağı, bölüm dosyaları, references.bib, şekiller
├── pipeline/                   pAI/MSc koşu kaydı
│   ├── research_task.md        ona verdiğimiz bir sayfalık brief
│   ├── vision.md               dondurulmuş, salt-okunur "vizyon kilidi"
│   ├── state.json              tam faz geçmişi, kapılar, kararlar
│   ├── literature_review.md    31 atıf, iddialarımızın 11'i çürütüldü
│   ├── research_goals.json     yedek bulgularıyla birlikte 11 ön kayıtlı hedef
│   ├── review_report.pdf       simüle hakem değerlendirmesi — 10 üzerinden 8
│   └── personas/               her turdaki düşmanca hakem eleştirileri
└── experiments/                EXP01–EXP11: betikler, ham loglar, sonuçlar
    └── verification_report.md  bağımsız yeniden hesap — 8 PASS, 3 PARTIAL, 0 FAIL
```

## Makaleyi okumadan önce bilinmesi gereken üç şey

**Kapsam, sistemin adının çağrıştırdığından dardır.** S.U.R.E. hiçbir zaman çalışan bir su ürünleri
tesisinde koşmadı. Fiziksel sensör donanımı mevcut değil; tüm deneylerdeki her sensör okuması
sentetik olarak üretildi. 510 görüntülük veri seti, fiziksel düzeneğin elle etiketlenmiş gerçek
kamera görüntüleridir; ama kasıtlı olarak küçüktür. Katkı, bir saha validasyonu değil, fizibilite ve
kaynak yönetimi gösterimidir. Bu, makalenin Giriş, Deneysel Kurulum ve Bilinen Kısıtlar bölümlerinde
açıkça belirtiliyor.

**Merkezî bulgu, ilk hipotezimizle çelişiyor.** Deterministik kural motorunun değerinin, LLM'in
yanlış kararlarını yakalamasından geleceğini bekliyorduk. Ölçüldüğünde (EXP03), 8 vakanın 1'inde
gerçek bir düşük tahmini yakaladı — buna karşılık 8 vakanın 4'ünde modelin ayrıştırılamayan çıktısı
nedeniyle güvenli varsayılana düştü. Baskın güvenlik mekanizması hata düzeltme değil, güvenli
varsayılana düşmedir. Ayrıca 8 gerekçe metninden 6'sı, yalnızca çıktıya bakan bir değerlendirmenin
göremeyeceği uydurulmuş sensör değerleri içeriyordu.

**Hat, bu depoda gerçek bir hata buldu.** EXP11,
`llm-service/knowledge/06-davranis-ve-refah-gostergeleri.md:58` satırını işaretledi: burada hâlâ
aşılmış bir recall değeri (≈0.695) duruyor ve bu dosya RAG vektör deposuna gerçekten besleniyor —
yani erişim katmanı eskimiş bir sayı servis edebilir. Denetim salt-okunur bir koruma altında
koştuğu için sessizce düzeltilmek yerine belgelendi.

## Yeniden derleme

```bash
cd research/paper
pdflatex final_paper.tex && bibtex final_paper && pdflatex final_paper.tex && pdflatex final_paper.tex
```

Boyut nedeniyle tek bir çıktı dışarıda bırakıldı: `experiments/EXP05/near_duplicate_pairs_full.json`
(2.4 MB). Toplulaştırılmış değerleri ve onu üreten betik depoya işlenmiş durumda.

## Atıf

S.U.R.E. sisteminin kendisi yazarların çalışmasıdır ve makaleden öncedir. Makale pAI/MSc ile
üretilmiş ve buna uygun şekilde atıf verilmiştir; PDF'in her sayfasındaki arka plan filigranı o
aracın atıf gerekliliğinin bir parçasıdır.

> Abdelmoneum, M., Beneventano, P., & Poggio, T. (2026). *pAI/MSc: ML Theory Research with Humans on
> the Loop.* MIT Technical Report v0. <https://dspace.mit.edu/handle/1721.1/165377>

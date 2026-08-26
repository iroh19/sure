"""
Labelled evaluation set for retrieval.

Query -> expected document. Chunking strategy and embedding model are chosen by
measuring against this set.

Queries are written the way an operator would actually type them: short,
elliptical, occasionally misspelled, and avoiding the wording of the document
headings. Queries that echo the headings make retrieval look better than it is.

`relevant` is a set because some questions are answerable from more than one
document (an oxygen crash appears both in the parameter doc and in emergency
procedures). A hit counts if any of them ranks first.

Queries stay in Turkish: they exercise a Turkish corpus.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvalQuery:
    query: str
    relevant: frozenset[str]


def _q(query: str, *relevant: str) -> EvalQuery:
    return EvalQuery(query, frozenset(relevant))


EVAL_QUERIES: tuple[EvalQuery, ...] = (
    # Oxygen
    _q("oksijen 5.2 ye düştü ne yapayım", "cozunmus-oksijen", "acil-mudahale"),
    _q("balıklar yüzeye çıkıp ağzıyla hava alıyor", "davranis-ve-refah", "cozunmus-oksijen"),
    _q("yemlemeden sonra neden oksijen düşüyor", "cozunmus-oksijen"),
    _q("çok fazla oksijen vermek zararlı mı", "cozunmus-oksijen"),
    _q("prob temiz değilse ölçüm yanıltır mı", "cozunmus-oksijen", "acil-mudahale"),

    # Temperature
    _q("su kaç derece olmalı", "sicaklik"),
    _q("yazın tank fazla ısınıyor ne yapmalı", "sicaklik"),
    _q("sıcaklık artınca oksijen neden azalıyor", "sicaklik", "cozunmus-oksijen"),
    _q("su değişiminde ani soğuma tehlikeli mi", "sicaklik"),

    # pH / alkalinity
    _q("ph sürekli aşağı gidiyor sebebi ne", "ph-ve-alkalinite"),
    _q("karbonat sertliği ne kadar olmalı", "ph-ve-alkalinite"),
    _q("soda eklerken dikkat edilecek şey", "ph-ve-alkalinite"),
    _q("co2 birikirse ne olur", "ph-ve-alkalinite"),

    # Nitrogen cycle
    _q("amonyak kaç olmalı", "amonyak-nitrit-nitrat"),
    _q("nitrit yüksek çıktı tuz atmalı mıyım", "amonyak-nitrit-nitrat", "acil-mudahale"),
    _q("yeni kurulan sistemde ilk haftalar neye dikkat", "amonyak-nitrit-nitrat"),
    _q("biyofiltre bozulunca ilk ne fark edilir", "amonyak-nitrit-nitrat", "acil-mudahale"),

    # TDS
    _q("iletkenlik değeri yükseliyor ne anlama gelir", "tds-ve-iletkenlik"),
    _q("su çok yumuşak olursa sorun olur mu", "tds-ve-iletkenlik"),
    _q("tds 480 çıktı", "tds-ve-iletkenlik"),

    # Behaviour
    _q("balıklar dipte kıpırdamıyor", "davranis-ve-refah"),
    _q("kamera hiç balık görmüyor alarm verdi", "davranis-ve-refah", "acil-mudahale"),
    _q("yem yemeyi bıraktılar ama su değerleri normal", "davranis-ve-refah", "amonyak-nitrit-nitrat"),
    _q("hareket ölçümü ne kadar güvenilir", "davranis-ve-refah"),

    # Emergencies
    _q("elektrik kesildi ne kadar zamanım var", "acil-mudahale"),
    _q("jeneratör yok acil ne yapabilirim", "acil-mudahale"),

    # Decision logic
    _q("sistem neden kritik dedi ama model iyi diyordu", "karar-mantigi"),
    _q("sensör bağlı değilken karar nasıl üretiliyor", "karar-mantigi"),
    _q("uyarı seviyesi nasıl belirleniyor", "karar-mantigi"),
)


# ── Negatives: questions the knowledge base cannot answer ────────────────────
#
# Bi-encoder retrieval returns the nearest chunk for every query, relevant or
# not. Feeding irrelevant context to a 1B model hands it material to answer a
# question it should decline — that invites hallucination rather than reducing it.
#
# These are adjacent to aquaculture but outside the corpus (breeding, regulation,
# procurement, pricing). Obviously unrelated questions would make the separation
# artificially easy, so these are hard negatives.
#
# `rag/calibrate.py` compares their similarity distribution against the positives
# to pick RAG_MIN_SIMILARITY by measurement.

NEGATIVE_QUERIES: tuple[str, ...] = (
    "mersin balığı kaç yaşında yumurtlar",
    "havyar nasıl işlenir ve saklanır",
    "yavru mersin balığını nereden temin edebilirim",
    "su ürünleri yetiştiricilik ruhsatı nasıl alınır",
    "canlı balığı başka tesise nasıl taşırım",
    "hangi marka su pompası daha dayanıklı",
    "balık yemi kilo fiyatı ne kadar",
    "tesisin elektrik faturasını nasıl düşürebilirim",
    "mantar enfeksiyonu için hangi ilacı vermeliyim",
    "tankın hacmini nasıl hesaplarım",
    "ihracat için hangi sertifika gerekiyor",
    "personel vardiya planını nasıl kurmalıyım",
)


# ── Metrics ──────────────────────────────────────────────────────────────────

def hit_at_k(ranked_doc_ids: list[str], relevant: frozenset[str], k: int) -> bool:
    return any(d in relevant for d in ranked_doc_ids[:k])


def reciprocal_rank(ranked_doc_ids: list[str], relevant: frozenset[str]) -> float:
    for i, doc_id in enumerate(ranked_doc_ids, start=1):
        if doc_id in relevant:
            return 1.0 / i
    return 0.0

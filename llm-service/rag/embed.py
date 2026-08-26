"""
Embedding models. Which one ships is decided by `rag/bench.py`.

``e5-small``  intfloat/multilingual-e5-small, 384 dims. Trained for asymmetric
              retrieval, so queries and passages must carry different prefixes
              ("query: " / "passage: "). Skipping the prefix puts the model
              outside its training distribution and quietly costs accuracy.
``tr-bert``   emrecan/bert-base-turkish-cased-mean-nli-stsb-tr, 768 dims. A
              symmetric sentence-similarity model (NLI/STS); takes no prefix.

Vectors are L2-normalised and searched with cosine distance. Without
normalisation, longer chunks rank higher on magnitude alone.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class ModelSpec:
    key: str
    hf_name: str
    dim: int
    query_prefix: str = ""
    passage_prefix: str = ""


MODELS: dict[str, ModelSpec] = {
    "e5-small": ModelSpec(
        key="e5-small",
        hf_name="intfloat/multilingual-e5-small",
        dim=384,
        query_prefix="query: ",
        passage_prefix="passage: ",
    ),
    "tr-bert": ModelSpec(
        key="tr-bert",
        hf_name="emrecan/bert-base-turkish-cased-mean-nli-stsb-tr",
        dim=768,
    ),
}

DEFAULT_MODEL = "e5-small"


class Embedder:
    """sentence-transformers wrapper handling prefixes and normalisation."""

    def __init__(self, model_key: str = DEFAULT_MODEL, device: str | None = None):
        if model_key not in MODELS:
            raise ValueError(f"Unknown embedding model: {model_key!r}. Options: {sorted(MODELS)}")
        self.spec = MODELS[model_key]
        self._device = device
        self._model = None  # lazy: import cost only when actually used

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.spec.hf_name, device=self._device)
        return self._model

    @property
    def dim(self) -> int:
        return self.spec.dim

    def encode_passages(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        vecs = self.model.encode(
            [self.spec.passage_prefix + t for t in texts],
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [v.tolist() for v in vecs]

    def encode_query(self, text: str) -> list[float]:
        vec = self.model.encode(
            self.spec.query_prefix + text,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vec.tolist()

    def verify_dim(self) -> None:
        """Dimensions in MODELS are hand-written; a mismatch surfaces as an
        opaque pgvector INSERT error, so fail early and clearly instead."""
        actual = len(self.encode_query("dimension check"))
        if actual != self.spec.dim:
            raise RuntimeError(
                f"{self.spec.key}: MODELS says {self.spec.dim} dims, model produced {actual}."
            )


@lru_cache(maxsize=4)
def get_embedder(model_key: str = DEFAULT_MODEL) -> Embedder:
    """Cached — the benchmark walks eight collections."""
    return Embedder(model_key)

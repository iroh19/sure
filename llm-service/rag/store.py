"""
pgvector-backed chunk store.

**One table per dimension.** `vector(N)` is fixed width, so 384- and 768-dim
models cannot share a column; the table name is derived from the dimension and a
`collection` column (`<model>:<strategy>`) separates collections inside it.

**HNSW with a filter.** Search filters on `collection`, which HNSW cannot use as
a pre-filter — pgvector walks neighbours and then discards. Irrelevant at a few
hundred chunks. At tens of thousands the fix is a table or partial index per
collection; doing it now would be premature.

**Idempotent.** `(collection, doc_id, chunk_index)` is unique and upserted, so
re-running ingest does not duplicate.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass

from .chunk import Chunk

DEFAULT_DSN = os.getenv("RAG_DATABASE_URL", "postgresql:///sure_rag")


@dataclass(frozen=True)
class SearchHit:
    doc_id: str
    chunk_index: int
    heading: str | None
    content: str
    distance: float

    @property
    def similarity(self) -> float:
        return 1.0 - self.distance


def table_for(dim: int) -> str:
    return f"rag_chunks_{dim}"


def collection_name(model_key: str, strategy: str) -> str:
    return f"{model_key}:{strategy}"


class VectorStore:
    def __init__(self, dim: int, dsn: str = DEFAULT_DSN):
        self.dim = dim
        self.dsn = dsn
        self.table = table_for(dim)

    @contextmanager
    def _conn(self):
        import psycopg
        from pgvector.psycopg import register_vector

        with psycopg.connect(self.dsn) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            register_vector(conn)
            yield conn

    def ensure_schema(self) -> None:
        with self._conn() as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table} (
                    id          BIGSERIAL PRIMARY KEY,
                    collection  TEXT      NOT NULL,
                    doc_id      TEXT      NOT NULL,
                    chunk_index INT       NOT NULL,
                    heading     TEXT,
                    content     TEXT      NOT NULL,
                    word_count  INT       NOT NULL,
                    embedding   vector({self.dim}) NOT NULL,
                    UNIQUE (collection, doc_id, chunk_index)
                )
            """)
            conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {self.table}_hnsw
                ON {self.table} USING hnsw (embedding vector_cosine_ops)
            """)
            conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {self.table}_collection
                ON {self.table} (collection)
            """)
            conn.commit()

    def clear(self, collection: str) -> int:
        with self._conn() as conn:
            cur = conn.execute(f"DELETE FROM {self.table} WHERE collection = %s", (collection,))
            conn.commit()
            return cur.rowcount

    def upsert(self, collection: str, chunks: list[Chunk],
               embeddings: list[list[float]]) -> int:
        if len(chunks) != len(embeddings):
            raise ValueError("chunk and embedding counts differ")
        rows = [
            (collection, c.doc_id, c.chunk_index, c.heading, c.content, c.word_count, e)
            for c, e in zip(chunks, embeddings)
        ]
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.executemany(
                    f"""
                    INSERT INTO {self.table}
                        (collection, doc_id, chunk_index, heading, content,
                         word_count, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (collection, doc_id, chunk_index) DO UPDATE SET
                        heading    = EXCLUDED.heading,
                        content    = EXCLUDED.content,
                        word_count = EXCLUDED.word_count,
                        embedding  = EXCLUDED.embedding
                    """,
                    rows,
                )
            conn.commit()
        return len(rows)

    def search(self, collection: str, query_vec: list[float], k: int = 5) -> list[SearchHit]:
        import numpy as np

        vec = np.array(query_vec, dtype=np.float32)
        with self._conn() as conn:
            rows = conn.execute(
                f"""
                SELECT doc_id, chunk_index, heading, content,
                       embedding <=> %s AS distance
                FROM {self.table}
                WHERE collection = %s
                ORDER BY distance
                LIMIT %s
                """,
                (vec, collection, k),
            ).fetchall()
        return [SearchHit(*r) for r in rows]

    def count(self, collection: str) -> int:
        with self._conn() as conn:
            row = conn.execute(
                f"SELECT count(*) FROM {self.table} WHERE collection = %s", (collection,)
            ).fetchone()
        return row[0] if row else 0

    def collections(self) -> list[tuple[str, int]]:
        with self._conn() as conn:
            return conn.execute(
                f"SELECT collection, count(*) FROM {self.table} "
                f"GROUP BY collection ORDER BY collection"
            ).fetchall()

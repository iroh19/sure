"""
Document loading and chunking for the knowledge base.

Chunking strategy drives retrieval quality, so it is a parameter rather than a
constant and is chosen by `rag/bench.py`, not by assumption.

Standard library only, so `test_knowledge.py` can import this in a CI image with
no torch and no psycopg.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    path: Path
    meta: dict[str, str]
    body: str


@dataclass(frozen=True)
class Chunk:
    doc_id: str
    chunk_index: int
    heading: str | None
    content: str

    @property
    def word_count(self) -> int:
        return len(self.content.split())


_FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse the `key: value` block between `---` fences.

    Deliberately not PyYAML: frontmatter is kept flat so this module has no
    dependencies and the rule-engine consistency test needs no extra install.
    """
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    meta: dict[str, str] = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, text[m.end():]


def load_documents(directory: Path | None = None) -> list[Document]:
    directory = directory or KNOWLEDGE_DIR
    docs: list[Document] = []
    for path in sorted(directory.glob("*.md")):
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        docs.append(
            Document(
                doc_id=meta.get("doc_id") or path.stem,
                title=meta.get("title", path.stem),
                path=path,
                meta=meta,
                body=body.strip(),
            )
        )
    if not docs:
        raise FileNotFoundError(f"Knowledge base is empty: {directory}")
    return docs


_HEADING_RE = re.compile(r"^##\s+(.*)$", re.MULTILINE)


def _split_by_heading(doc: Document) -> list[tuple[str | None, str]]:
    matches = list(_HEADING_RE.finditer(doc.body))
    if not matches:
        return [(None, doc.body)]

    sections: list[tuple[str | None, str]] = []
    preamble = doc.body[: matches[0].start()].strip()
    preamble = re.sub(r"^#\s+.*$", "", preamble, flags=re.MULTILINE).strip()

    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(doc.body)
        content = doc.body[m.end():end].strip()
        if i == 0 and preamble:
            content = f"{preamble}\n\n{content}"
        if content:
            sections.append((m.group(1).strip(), content))
    return sections


def _windows(words: list[str], size: int, overlap: int) -> list[list[str]]:
    if size <= 0:
        raise ValueError("chunk size must be positive")
    step = max(1, size - overlap)
    out: list[list[str]] = []
    for start in range(0, len(words), step):
        window = words[start:start + size]
        if not window:
            break
        out.append(window)
        if start + size >= len(words):
            break
    return out


def chunk_document(doc: Document, strategy: str) -> list[Chunk]:
    """Split a document.

    ``heading``    — one chunk per `##` section. Respects markdown structure;
                     boundaries fall in meaningful places. The section heading is
                     prefixed into the content because it is a strong retrieval
                     signal.
    ``fixed-<N>w`` — sliding N-word window over the body with 15% overlap.
                     Deliberately ignores structure: headings become plain text
                     and boundaries can cut a sentence.

    The contrast between the two is the point of the benchmark. Making the fixed
    strategy respect section boundaries turns it into a copy of `heading` — which
    is exactly the bug the first version had: sections average ~60 words, so the
    120/240/480 windows never engaged and all four strategies produced the same
    44 chunks.
    """
    if strategy == "heading":
        return [
            Chunk(doc.doc_id, i, heading,
                  f"{doc.title} — {heading}\n\n{content}" if heading
                  else f"{doc.title}\n\n{content}")
            for i, (heading, content) in enumerate(_split_by_heading(doc))
        ]

    m = re.fullmatch(r"fixed-(\d+)w", strategy)
    if not m:
        raise ValueError(f"Unknown chunking strategy: {strategy!r}")

    size = int(m.group(1))
    flat = _HEADING_RE.sub(lambda mm: mm.group(1), doc.body)
    flat = re.sub(r"^#\s+", "", flat, flags=re.MULTILINE)

    return [
        # Document title is kept — retrieval needs to know the source. The
        # section heading is unknown to a fixed-size chunker by construction.
        Chunk(doc.doc_id, i, None, f"{doc.title}\n\n{' '.join(window)}")
        for i, window in enumerate(_windows(flat.split(), size, max(1, round(size * 0.15))))
    ]


def chunk_all(strategy: str, directory: Path | None = None) -> list[Chunk]:
    out: list[Chunk] = []
    for doc in load_documents(directory):
        out.extend(chunk_document(doc, strategy))
    return out


STRATEGIES = ("heading", "fixed-120w", "fixed-240w", "fixed-480w")

"""Chunking utilities for preparing documents for FAISS indexing.

Includes lightweight and LangChain-based splitters with metadata helpers."""

from __future__ import annotations

import re
import os
import json as _json
from dataclasses import dataclass
from hashlib import md5
from pathlib import Path
from typing import Iterable, List, Literal

from langchain_core.documents import Document
from src.service.rag_service.models import DocumentChunk, RawDocument
from src.service.rag_service.utils import Logger

logger = Logger.get_logger(__name__)

try:
    from langchain_text_splitters import (
        RecursiveCharacterTextSplitter,
        CharacterTextSplitter,
        MarkdownHeaderTextSplitter,
        RecursiveJsonSplitter,
    )
except ImportError:
    logger.warning(
        "Install 'langchain-text-splitters' for modern splitters:\n"
        "  pip install -U langchain-text-splitters"
    )
    RecursiveCharacterTextSplitter = None
    CharacterTextSplitter = None
    MarkdownHeaderTextSplitter = None
    RecursiveJsonSplitter = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    logger.warning(
        "bs4 package not installed, use `pip install beautifulsoup4` to install. Falling back to manual extraction of html tags from Markdown"
    )
    BeautifulSoup = None


@dataclass
class ChunkingConfig:
    """Holds chunking hyperparameters.

    Controls size, overlap, normalisation, and base strategies."""

    chunk_size: int = 800
    chunk_overlap: int = 160
    normalize_whitespace: bool = True
    base_char_strategy: Literal["recursive", "character"] = "recursive"


class TextChunker:
    """Simple whitespace-normalising chunker for RawDocuments.

    Uses deterministic chunk IDs and minimal dependencies."""

    def __init__(self, *, config: ChunkingConfig | None = None) -> None:
        """Initialise the chunker and validate configuration."""
        self.config = config or ChunkingConfig()
        if self.config.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.config.chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if self.config.chunk_overlap >= self.config.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

    def chunk_documents(self, documents: Iterable[RawDocument]) -> List[DocumentChunk]:
        """Split each RawDocument into DocumentChunks.

        Returns a flat list ready for FAISS ingestion."""
        chunks: List[DocumentChunk] = []
        for document in documents:
            chunks.extend(self._chunk_single_document(document))
        return chunks

    # ------------------------------------------------------------------ #
    def _chunk_single_document(self, document: RawDocument) -> List[DocumentChunk]:
        """Chunk a single document according to the configured window."""
        cleaned = self._normalise_text(document.text)
        if not cleaned:
            return []

        results: List[DocumentChunk] = []
        cursor = 0
        index = 0
        size = self.config.chunk_size
        overlap = self.config.chunk_overlap

        while cursor < len(cleaned):
            end = min(len(cleaned), cursor + size)
            snippet = cleaned[cursor:end].strip()
            if snippet:
                unique = md5(str(document.path).encode("utf-8")).hexdigest()[:12]
                chunk_id = f"{document.document_type}-{unique}-{index}"
                metadata = {
                    "document_type": document.document_type,
                    "source": str(document.path),
                    "chunk_index": index,
                }
                results.append(
                    DocumentChunk(
                        case_id=document.case_id,
                        chunk_id=chunk_id,
                        text=snippet,
                        metadata=metadata,
                    )
                )
            index += 1
            if end >= len(cleaned):
                break
            cursor = max(0, end - overlap)
        return results

    def _normalise_text(self, text: str) -> str:
        """Collapse whitespace so chunk boundaries stay predictable."""
        return re.sub(r"\s+", " ", text).strip()


class TextChunkerSplit:
    """LangChain-based chunker with markdown/json awareness.

    Provides richer metadata and smarter splitting heuristics."""

    def __init__(self, *, config: ChunkingConfig | None = None) -> None:
        """Prepare all optional splitters based on the supplied config."""
        self.config = config or ChunkingConfig()
        if self.config.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.config.chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if self.config.chunk_overlap >= self.config.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        # base char splitter
        if self.config.base_char_strategy == "recursive":
            if RecursiveCharacterTextSplitter is None:
                raise RuntimeError(
                    "RecursiveCharacterTextSplitter unavailable. Install langchain-text-splitters."
                )
            self.base_char_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
                separators=["\n\n", "\n", " ", ""],
                is_separator_regex=False,
            )
        else:
            if CharacterTextSplitter is None:
                raise RuntimeError(
                    "CharacterTextSplitter unavailable. Install langchain-text-splitters."
                )
            self.base_char_splitter = CharacterTextSplitter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
                separator=" ",  # or "" for strict char windows
            )

        # optional, only used when available
        self.md_header_splitter = None
        if MarkdownHeaderTextSplitter is not None:
            self.md_header_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=[
                    ("#", "h1"),
                    ("##", "h2"),
                    ("###", "h3"),
                    ("####", "h4"),
                ]
            )

        self.json_splitter = None
        if RecursiveJsonSplitter is not None:
            self.json_splitter = RecursiveJsonSplitter(
                max_chunk_size=self.config.chunk_size
            )

    # -------------------- public API -------------------- #

    def chunk_documents(self, documents: Iterable[RawDocument]) -> List[DocumentChunk]:
        """Split the provided documents using type-aware strategies."""
        chunks: List[DocumentChunk] = []
        for document in documents:
            chunks.extend(self._chunk_single_document(document))
        return chunks

    # -------------------- internals --------------------- #
    def _chunk_single_document(self, document: RawDocument) -> List[DocumentChunk]:
        """Route a document through markdown, JSON, or plain pipelines."""
        doc_type = self._infer_type(document)
        text = document.text or ""
        if self.config.normalize_whitespace:
            text = self._normalise_text(text)
        if not text:
            return []
        name = os.path.basename(document.path)
        if "_parsed.txt" in name:
            return []

        if doc_type == "markdown" and self.md_header_splitter is not None:
            splits = self._split_markdown(text, document)
        elif doc_type == "json" and self.json_splitter is not None:
            splits = self._split_json(text, document)
        else:
            splits = self._split_plain(text, document, doc_type)

        # Convert LangChain Documents -> DocumentChunk with IDs + metadata
        unique = md5(str(document.path).encode("utf-8")).hexdigest()[:12]
        results: List[DocumentChunk] = []
        for idx, d in enumerate(splits):
            chunk_id = f"{document.document_type}-{unique}-{idx}"
            meta = dict(d.metadata or {})
            meta.update(
                {
                    "document_type": document.document_type,
                    "source": str(document.path),
                    "chunk_index": idx,
                }
            )
            results.append(
                DocumentChunk(
                    case_id=document.case_id,
                    chunk_id=chunk_id,
                    text=d.page_content.strip(),
                    metadata=meta,
                )
            )
        return results

    def _normalize_md_with_html(self, text: str) -> str:
        """Convert HTML tables in markdown to textual tables."""
        # If no HTML table tags present, return as-is
        if (
            "<table" not in text
            and "<td" not in text
            and "<tr" not in text
            and "<th" not in text
        ):
            return text

        if BeautifulSoup is None:
            # Minimal fallback: turn rows/cells into a crude pipe table
            import re as _re

            t = _re.sub(r"</tr\s*>", "\n", text, flags=_re.I)
            t = _re.sub(r"<tr[^>]*>", "", t, flags=_re.I)
            t = _re.sub(r"</t[hd]\s*>", " | ", t, flags=_re.I)
            t = _re.sub(r"<t[hd][^>]*>", "", t, flags=_re.I)
            t = _re.sub(r"</?table[^>]*>", "\n", t, flags=_re.I)
            return t

        soup = BeautifulSoup(text, "html.parser")

        def table_to_md(table) -> str:
            rows = []
            for tr in table.find_all("tr"):
                cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
                if cells:
                    rows.append(cells)
            if not rows:
                return ""
            header = rows[0]
            md = "| " + " | ".join(header) + " |\n"
            md += "| " + " | ".join(["---"] * len(header)) + " |\n"
            for r in rows[1:]:
                # pad rows to header length
                if len(r) < len(header):
                    r = r + [""] * (len(header) - len(r))
                md += "| " + " | ".join(r) + " |\n"
            return "\n" + md + "\n"

        # replace each <table>...</table> with markdown table text
        for tbl in soup.find_all("table"):
            md_tbl = table_to_md(tbl)
            tbl.replace_with(md_tbl)

        return str(soup)

    def _split_markdown(self, text: str, document: RawDocument) -> List[Document]:
        """Split markdown into header sections then normalise chunk sizes."""
        # 1) split by headers to preserve sections
        text = self._normalize_md_with_html(text)
        header_docs = self.md_header_splitter.split_text(text)  # type: ignore
        for d in header_docs:
            d.metadata.update({"document_type": "markdown_section"})
        # 2) size-normalize sections
        return self.base_char_splitter.split_documents(header_docs)

    def _split_json(self, text: str, document: RawDocument) -> List[Document]:
        """Break JSON payloads into manageable serialized segments."""

        try:
            data = _json.loads(text) if isinstance(text, str) else text
        except Exception:
            # fall back to plain if not valid JSON
            return self._split_plain(self._normalise_text(text), document, "text")

        segments = self.json_splitter.split_json(data)  # type: ignore

        json_docs: List[Document] = []
        for seg in segments:
            if not isinstance(seg, str):
                try:
                    seg = _json.dumps(seg, ensure_ascii=False)
                except Exception:
                    seg = str(seg)
            json_docs.append(
                Document(
                    page_content=self._normalise_text(seg), metadata={"json": True}
                )
            )

        return self.base_char_splitter.split_documents(json_docs)

    def _split_plain(
        self, text: str, document: RawDocument, doc_type: str
    ) -> List[Document]:
        """Fallback splitter for plain-text or unsupported formats."""
        doc = Document(page_content=text, metadata={"document_type": doc_type})
        return self.base_char_splitter.split_documents([doc])

    def _infer_type(self, document: RawDocument) -> str:
        """Guess the document type based on metadata or suffix."""
        # Prefer explicit document_type; otherwise infer from suffix
        if document.document_type:
            t = document.document_type.lower()
            if t in {"markdown", "md"}:
                return "markdown"
            if t in {"json"}:
                return "json"
        try:
            suffix = Path(str(document.path)).suffix.lower()
        except Exception:
            suffix = ""
        if suffix in {".md", ".markdown"}:
            return "markdown"
        if suffix == ".json":
            return "json"
        return "text"

    def _normalise_text(self, text: str) -> str:
        """Normalise any string-like input to a one-line representation."""
        return re.sub(r"\s+", " ", text).strip()

    def _normalise_text(self, text) -> str:
        """Compat helper for legacy callers expecting implicit conversion."""
        if not isinstance(text, str):
            try:
                if isinstance(text, (dict, list)):
                    text = _json.dumps(text, ensure_ascii=False)
                else:
                    text = str(text)
            except Exception:
                text = str(text)
        import re as _re

        return _re.sub(r"\s+", " ", text).strip()

"""LangChain FAISS storage wrapper used by the RAG service."""

from __future__ import annotations

import json
import shutil
import datetime
from pathlib import Path
from typing import Iterable, List

from langchain_community.vectorstores import FAISS as LCFAISS

from src.service.rag_service.core import (
    DEFAULT_EMBED_MODEL,
    get_embeddings,
    index_dir_for,
)
from src.service.rag_service.models import DocumentChunk, RetrievedChunk
from src.service.rag_service.utils import Logger

logger = Logger.get_logger(__name__)


class ChunkFaissStore:
    """Persistence helper around the langchain-community FAISS store.

    Keeps compatibility with the existing ingest/ask flow."""

    def __init__(
        self,
        case_id: str,
        *,
        index_root: str = "rag_index",
        model_name: str = DEFAULT_EMBED_MODEL,
    ) -> None:
        self.case_id = case_id
        self.model_name = model_name
        self.index_dir: Path = index_dir_for(case_id, index_root=index_root)
        self.meta_path = self.index_dir / "meta.json"
        self.embedding = get_embeddings(model_name)
        self._store: LCFAISS | None = self._load_store()

    # ------------------------------------------------------------------ #
    def reset(self) -> None:
        """Remove any previously stored index/metadata for this case.

        Ensures a clean slate before re-ingesting."""
        if self.index_dir.exists():
            shutil.rmtree(self.index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self._store = None

    def upsert_chunks(self, chunks: Iterable[DocumentChunk]) -> int:
        """Encode, store, and persist the supplied chunks.

        Returns the number of chunks written to FAISS."""
        chunk_list = list(chunks)
        if not chunk_list:
            return 0

        texts: List[str] = []
        metadatas: List[dict] = []
        ids: List[str] = []
        for chunk in chunk_list:
            texts.append(chunk.text)
            meta = {
                "case_id": chunk.case_id,
                "chunk_id": chunk.chunk_id,
                **(chunk.metadata or {}),
            }
            metadatas.append(meta)
            ids.append(chunk.chunk_id)

        logger.info(
            "Indexing %d chunks for case %s using langchain-community FAISS",
            len(chunk_list),
            self.case_id,
        )
        self._store = LCFAISS.from_texts(
            texts,
            embedding=self.embedding,
            metadatas=metadatas,
            ids=ids,
        )
        self._store.save_local(self.index_dir)
        self._write_meta(len(chunk_list))
        return len(chunk_list)

    # ------------------------------------------------------------------ #
    def similarity_search(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        """Search the FAISS index and return the top matches."""
        store = self._ensure_store()
        if store is None:
            return []

        results = store.similarity_search_with_score(query, k=top_k)
        matches: List[RetrievedChunk] = []
        for doc, score in results:
            metadata = dict(doc.metadata or {})
            chunk_id = metadata.pop("chunk_id", "")
            case_id = metadata.get("case_id", self.case_id)
            chunk = DocumentChunk(
                case_id=case_id,
                chunk_id=chunk_id or f"chunk-{len(matches)}",
                text=doc.page_content,
                metadata=metadata,
            )
            matches.append(RetrievedChunk(chunk=chunk, score=float(score)))
        return matches

    # ------------------------------------------------------------------ #
    def _ensure_store(self) -> LCFAISS | None:
        """Load the FAISS store from disk if necessary."""
        if self._store is None:
            self._store = self._load_store()
        return self._store

    def _load_store(self) -> LCFAISS | None:
        """Attempt to load the FAISS artefacts and embedding model."""
        try:
            return LCFAISS.load_local(
                self.index_dir,
                embeddings=self.embedding,
                allow_dangerous_deserialization=True,
            )
        except (ValueError, FileNotFoundError, RuntimeError):
            logger.info(
                "No FAISS index found for case %s at %s. Run ingest first.",
                self.case_id,
                self.index_dir,
            )
            return None

    def _write_meta(self, chunk_count: int) -> None:
        """Persist lightweight metadata about the stored chunks."""
        meta = {
            "case_id": self.case_id,
            "model_name": self.model_name,
            "chunks_indexed": chunk_count,
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
        }
        self.meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

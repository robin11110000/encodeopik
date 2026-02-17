"""High-level RAG agent that chunks cases and answers questions."""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Dict, List, Optional

from src.service.rag_service.chunker import TextChunker, TextChunkerSplit
from src.service.rag_service.embedding_store import ChunkFaissStore
from src.service.rag_service.llm_responder import LLMResponder
from src.service.rag_service.main import CaseDocumentLoader
from src.service.rag_service.memory import ConversationMemory
from src.service.rag_service.models import AllDocument, RawDocument, RetrievedChunk
from src.service.rag_service.utils import Logger

logger = Logger.get_logger(__name__)


class RAGAgent:
    """Coordinates ingestion, retrieval, and response generation per case.

    Owns the chunker, FAISS store, memory, and LLM client."""

    def __init__(
        self,
        case_id: str,
        *,
        chunk_size: int = 800,
        chunk_overlap: int = 160,
        top_k: int = 5,
    ) -> None:
        self.case_id = case_id
        self.top_k = top_k
        self.loader = CaseDocumentLoader()
        try:
            self.chunker = TextChunkerSplit()
        except Exception as e:
            logger.warning(f"Falling back to TextChunker due to: {e}")
            self.chunker = TextChunker()
        self.store = ChunkFaissStore(case_id)
        self.llm = None  # Lazily initialised to honour API key validation
        self.memory = ConversationMemory(case_id=case_id)

    # ------------------------------------------------------------------ #
    def ingest(self) -> Dict[str, int]:
        """Load, chunk, and index case documents plus KPI definitions.

        Returns bookkeeping stats for chunks/documents stored."""
        # all_docs = self.loader.load_case_all_documents(self.case_id)
        # raw_docs = self._build_raw_documents(all_docs)
        raw_docs = self.loader.load_case_documents(self.case_id)
        kpi_reference = self.loader.load_kpi_definitions(self.case_id)
        if kpi_reference is not None:
            raw_docs.append(kpi_reference)
            logger.info(
                "Appended KPI definitions reference to case %s corpus.", self.case_id
            )
        logger.info(
            "Prepared %d combined documents for case %s",
            len(raw_docs),
            self.case_id,
        )
        chunks = self.chunker.chunk_documents(raw_docs)
        logger.info("Generated %d chunks for case %s", len(chunks), self.case_id)
        if not chunks:
            raise ValueError(f"No text chunks produced for case {self.case_id}.")

        self.store.reset()
        stored = self.store.upsert_chunks(chunks)
        return {
            "case_id": self.case_id,
            "documents_indexed": len(raw_docs),
            "chunks_indexed": stored,
        }

    # ------------------------------------------------------------------ #
    def ask(self, query: str, *, top_k: Optional[int] = None) -> Dict[str, object]:
        """Answer a query using FAISS retrieval, memory, and the LLM.

        Returns the response along with matches and updated memory."""
        logger.info("Processing query for case %s: %s", self.case_id, query)
        query = (query or "").strip()
        if not query:
            raise ValueError("Query must not be blank.")

        k = top_k or self.top_k
        logger.info("Retrieving top-%d relevant chunks for query.", k)
        matches = self.store.similarity_search(query, top_k=k)
        if not matches:
            raise ValueError(
                "No indexed context available. Build the index for this case first."
            )
        raw_docs = self.loader.load_case_documents(self.case_id)
        kpis_definitions = self.loader.load_kpi_definitions(self.case_id).text
        final = self.loader.select_named_documents(
            raw_docs,
            wanted=["final_decision.json", "kpis_final.json"],
            document_type="final_output",
        )
        logger.info("Reading Final KPIs and Decision documents for context.")
        final_kpis = final_decision = dict()
        if final:
            if os.path.basename(final[0].path) == "final_decision.json":
                final_decision = final[0].text
                final_kpis = final[1].text
            else:
                final_decision = final[1].text
                final_kpis = final[0].text
        contexts = [match.chunk.text for match in matches]
        memory_contexts = self.memory.as_context()
        responder = self._ensure_llm()
        logger.info("Answering query using LLM with %d context chunks.", len(contexts))
        answer_payload = responder.answer(
            query,
            contexts,
            final_kpis=final_kpis,
            final_decision=final_decision,
            kpi_definitions=kpis_definitions,
            memory=memory_contexts,
        )

        self.memory.append(query, answer_payload.get("answer", ""))

        return {
            "case_id": self.case_id,
            "query": query,
            "answer": answer_payload.get("answer", ""),
            "used_context": answer_payload.get("used_context", ""),
            "matches": [self._format_match(match) for match in matches],
            "memory": self.memory.as_list(),
        }

    # ------------------------------------------------------------------ #
    def _ensure_llm(self) -> LLMResponder:
        """Instantiate the responder lazily to avoid needless API checks.

        Prevents repeated API-key validation churn."""
        if self.llm is None:
            self.llm = LLMResponder()
        return self.llm

    def _format_match(self, match: RetrievedChunk) -> Dict[str, object]:
        """Convert an internal RetrievedChunk into a serialisable dict.

        Helps the API surface consistent metadata to clients."""
        data = {
            "chunk_id": match.chunk.chunk_id,
            "score": match.score,
            "text": match.chunk.text,
            "metadata": match.chunk.metadata,
        }
        return data

    def _build_raw_documents(self, all_docs: AllDocument) -> List[RawDocument]:
        """Legacy helper for merging KPIs + markdown into synthetic docs.

        Used when the case pipeline needs virtual text files."""
        documents: List[RawDocument] = []

        base_path: Path
        if all_docs.path and isinstance(all_docs.path, Path):
            base_path = all_docs.path
        elif all_docs.path:
            base_path = Path(all_docs.path)
        else:
            try:
                base_path = self.loader.resolve_case_dir(self.case_id)
            except FileNotFoundError:
                base_path = Path(".")

        for doc_type, payload in all_docs.docs.items():
            kpis_payload = payload.get("kpis")
            md_payload = payload.get("md")

            parts: List[str] = []
            if kpis_payload:
                if isinstance(kpis_payload, (dict, list)):
                    parts.append(json.dumps(kpis_payload, indent=2))
                else:
                    parts.append(str(kpis_payload))

            if md_payload:
                if isinstance(md_payload, (dict, list)):
                    parts.append(json.dumps(md_payload, indent=2))
                else:
                    parts.append(str(md_payload))

            combined = "\n\n".join(p.strip() for p in parts if str(p).strip())
            if not combined:
                continue

            fake_path = base_path / f"{doc_type}.txt"
            documents.append(
                RawDocument(
                    case_id=self.case_id,
                    document_type=doc_type,
                    path=fake_path,
                    text=combined,
                )
            )

        return documents

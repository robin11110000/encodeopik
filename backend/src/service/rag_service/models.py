"""Data structures shared across the RAG service modules."""

from pathlib import Path
from typing import Any, Dict
from dataclasses import dataclass, field


@dataclass
class RawDocument:
    """Represents a single source artifact loaded from disk."""
    case_id: str
    document_type: str
    path: Path
    text: str


@dataclass
class AllDocument:
    """Bundle of all documents plus reference path for a case."""
    case_id: str
    docs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    path: Path | None = None


@dataclass
class DocumentChunk:
    """Chunk of text plus metadata ready for FAISS storage."""
    case_id: str
    chunk_id: str
    text: str
    metadata: Dict[str, Any]


@dataclass
class RetrievedChunk:
    """Wrapper linking a chunk with its similarity score."""
    chunk: DocumentChunk
    score: float

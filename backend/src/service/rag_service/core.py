"""Core helpers for the RAG service.

Provides embedding factories and index directory utilities."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from src.service.rag_service.utils import Logger

# from langchain_aws import BedrockEmbeddings
# from src.service.rag_service.utils import Config

logger = Logger.get_logger(__name__)
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    logger.warning(
        "⚠️ The package 'langchain-huggingface' is not installed. "
        "Please install it using: pip install -U langchain-huggingface"
    )
    logger.warning(
        "⚠️ Falling back to 'langchain_community.embeddings.HuggingFaceEmbeddings'"
    )
    from langchain_community.embeddings import HuggingFaceEmbeddings


DEFAULT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# DEFAULT_EMBED_MODEL = "amazon.titan-embed-text-v1"


@lru_cache(maxsize=4)
def get_embeddings(model_name: str = DEFAULT_EMBED_MODEL) -> HuggingFaceEmbeddings:
    """Return a cached HuggingFace embedding model.

    Avoids reloading weights for repeated queries."""
    logger.info("Loaded sentence-transformer model '%s'", model_name)
    return HuggingFaceEmbeddings(model_name=model_name)


def index_dir_for(case_id: str, index_root: str = "rag_index") -> Path:
    """Resolve and create the on-disk FAISS index directory.

    Ensures the per-case path exists before writing files."""
    base_dir = Path(__file__).resolve().parent
    target = base_dir / index_root / case_id
    target.mkdir(parents=True, exist_ok=True)
    return target

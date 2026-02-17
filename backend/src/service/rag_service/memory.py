"""Lightweight conversation memory persisted per RAG case."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from src.service.rag_service.utils import Logger

logger = Logger.get_logger(__name__)


@dataclass
class MemoryEntry:
    """Single user/assistant exchange with timestamp metadata."""
    query: str
    answer: str
    timestamp: str


class ConversationMemory:
    """File-backed store retaining the last N exchanges per case.

    Persists JSON under rag_index/<case_id>/memory.json."""

    def __init__(
        self, case_id: str, max_entries: int = 10, index_root: str = "rag_index"
    ) -> None:
        """Initialise the memory location and ensure directories exist."""
        self.case_id = case_id
        self.max_entries = max_entries
        base_dir = Path(__file__).resolve().parent
        self.memory_path = base_dir / index_root / case_id / "memory.json"
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    def load(self) -> List[MemoryEntry]:
        """Read the memory file and return the most recent entries."""
        if not self.memory_path.exists():
            return []
        try:
            raw = json.loads(self.memory_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning(
                "Corrupted memory file for case %s; resetting.", self.case_id
            )
            return []
        entries: List[MemoryEntry] = []
        for item in raw[-self.max_entries :]:
            if isinstance(item, dict):
                entries.append(
                    MemoryEntry(
                        query=item.get("query", ""),
                        answer=item.get("answer", ""),
                        timestamp=item.get("timestamp", ""),
                    )
                )
        return entries

    def append(self, query: str, answer: str) -> List[MemoryEntry]:
        """Add a new exchange to memory and persist it to disk."""
        entries = self.load()
        entries.append(
            MemoryEntry(
                query=query,
                answer=answer,
                timestamp=datetime.utcnow().isoformat() + "Z",
            )
        )
        entries = entries[-self.max_entries :]
        payload = [asdict(entry) for entry in entries]
        self.memory_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return entries

    def as_context(self) -> List[str]:
        """Return stored exchanges formatted as light-weight context snippets."""
        entries = self.load()
        if not entries:
            return []
        formatted = []
        for idx, entry in enumerate(entries, start=1):
            text = (
                f"Conversation #{idx} | {entry.timestamp}\n"
                f"User: {entry.query}\n"
                f"Assistant: {entry.answer}"
            )
            formatted.append(text)
        return formatted

    def as_list(self) -> List[Dict[str, Any]]:
        """Return the memory contents as serialisable dictionaries."""
        return [asdict(entry) for entry in self.load()]

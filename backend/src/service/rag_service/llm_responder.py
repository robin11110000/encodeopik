"""LLM responder that crafts prompts and fetches answers from Bedrock."""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.service.rag_service.utils import Config, Logger
from src.service.rag_service.main import KPIReferenceLoader

logger = Logger.get_logger(__name__)


class LLMResponder:
    """Wraps prompt construction, Bedrock invocation, and intent enrichment."""

    def __init__(
        self,
        *,
        model: str = "amazon.nova-pro-v1:0",
        style: str = "concise",
        max_context_chars: int = 12000,
        api_key: Optional[str] = None,
    ) -> None:
        """Store model settings and supporting helpers (config + KPI loader)."""
        self.model = model
        self.style = style
        self.max_context_chars = max_context_chars
        self.config = Config()
        self.kpis = KPIReferenceLoader()

    def answer(
        self,
        query: str,
        contexts: Iterable[str],
        final_kpis: Optional[Dict[str]] = None,
        final_decision: Optional[Dict[str]] = None,
        kpi_definitions: Optional[Dict[str]] = None,
        *,
        memory: Optional[Iterable[str]] = None,
    ) -> Dict[str, str]:
        """Generate an answer using the supplied contexts and memories."""
        stitched = self._build_context(contexts)
        memory_block = self._build_memory(memory)
        intent = self.kpis.detect_intents(question=query)
        logger.info(intent)
        if intent["decision_intent"]:
            stitched += (
                "\n\n--- FINAL DECISION ---\n"
                + str(final_decision)
                + "\n\n --- FINAL KPIs ---\n"
                + str(final_kpis)
            )
        if intent["kpi_intent"]:
            stitched += (
                "\n\n if user asks about indicators or definitions use these KPIs information:\n\n--- KPIs Definitions ---\n"
                + str(kpi_definitions)
            )

        system_template = """You are an intelligent retrieval-augmented assistant.
        Use ONLY the information in CONTEXT to answer.
        Use MEMORY only to resolve pronouns/references; do not add new facts from memory.
        If the answer is not present in CONTEXT, reply exactly:
        I couldn't find that information in the provided documents.
        Never give generic reasons or background explanations. Respond in one concise paragraph.

        GREETING OVERRIDE:
        If the user greets you (e.g., "hi", "hello", "hey"), respond EXACTLY:
        Hello, how can I help you with your documents?
        Do not add any other text.
        """
        user_template = """--- CONTEXT START ---
        {context}
        --- CONTEXT END ---

        --- MEMORY (use only for resolving references) ---
        {memory}

        User question: {question}
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_template),
                ("user", user_template),
            ]
        )
        llm = ChatBedrock(
            model_id=self.model,
            region="us-east-1",
            aws_access_key_id=self.config.aws_access_key,
            aws_secret_access_key=self.config.aws_secret_key,
            temperature=0.3,
        )
        chain = prompt | llm | StrOutputParser()
        variables = {
            "context": stitched,
            "memory": memory_block,
            "question": query,
        }
        answer = chain.invoke(variables)
        logger.info("Generated answer with Bedrock model %s", self.model)
        return {"answer": answer, "query": query, "used_context": stitched}

    # ------------------------------------------------------------------ #
    def _build_context(self, contexts: Iterable[str]) -> str:
        """Concatenate context snippets while enforcing the char budget."""
        bucket: List[str] = []
        total_chars = 0
        for idx, ctx in enumerate(contexts, start=1):
            snippet = ctx.strip()
            if not snippet:
                continue
            block = f"[{idx}]\n{snippet}\n"
            if total_chars + len(block) > self.max_context_chars:
                break
            bucket.append(block)
            total_chars += len(block)
        return "\n".join(bucket)

    def _build_memory(self, memory: Optional[Iterable[str]]) -> str:
        """Format conversational memory for reference-only usage."""
        if not memory:
            return ""
        bucket: List[str] = []
        total_chars = 0
        for idx, item in enumerate(memory, start=1):
            snippet = str(item).strip()
            if not snippet:
                continue
            block = f"[{idx}] {snippet}"
            if total_chars + len(block) > self.max_context_chars:
                break
            bucket.append(block)
            total_chars += len(block)
        return "\n".join(bucket)

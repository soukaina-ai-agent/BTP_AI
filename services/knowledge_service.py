"""Built-in DTU knowledge loading for the FastAPI MVP."""

import logging
import os

from knowledge import get_all_knowledge_chunks
from services.rag_service import RAGService

logger = logging.getLogger(__name__)


def autoload_knowledge(rag: RAGService) -> int:
    if os.getenv("SKIP_DTU_AUTOLOAD", "").lower() in ("1", "true", "yes"):
        return 0

    stats = rag.get_stats()
    has_builtin = any(
        "[BASE DTU]" in doc.get("source", "")
        for doc in stats.get("documents", [])
    )
    if has_builtin:
        return 0

    chunks = get_all_knowledge_chunks()
    count = rag.add_documents(chunks)
    logger.info("[FastAPI] Autoloaded %s DTU chunks", count)
    return count

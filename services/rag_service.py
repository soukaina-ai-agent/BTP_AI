"""RAG service used by the FastAPI backend."""

import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from retriever import EmbeddingEngine, LLMEngine, TOP_K
from services.vector_store import ChromaVectorStore

load_dotenv()
logger = logging.getLogger(__name__)


class RAGService:
    """Chroma-backed RAG pipeline with metadata filters."""

    def __init__(self):
        self.embedder = EmbeddingEngine()
        self.store = ChromaVectorStore()
        self.llm = LLMEngine()

    def add_documents(self, chunks: List[Dict[str, Any]]) -> int:
        if not chunks:
            return 0

        texts = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        embeddings = self.embedder.embed(texts)
        self.store.add(texts, embeddings, metadatas)
        return len(chunks)

    def retrieve(
        self,
        question: str,
        k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        embedding = self.embedder.embed([question])[0]
        return self.store.search(embedding, k or TOP_K, where=self._build_where(filters))

    def query(
        self,
        question: str,
        k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if self.store.total_documents == 0:
            return {
                "answer": "Aucun document n'est encore indexe.",
                "sources": [],
            }

        chunks = self.retrieve(question, k=k, filters=filters)
        if not chunks:
            return {
                "answer": "Aucune information pertinente trouvee pour cette question.",
                "sources": [],
            }

        answer = self.llm.generate(question, chunks)
        return {"answer": answer, "sources": self._sources_from_chunks(chunks)}

    def get_stats(self) -> Dict[str, Any]:
        docs = self.store.documents
        seen = {}
        for doc in docs:
            meta = doc["metadata"]
            source = meta.get("source", "?")
            if source not in seen:
                seen[source] = {
                    "source": source,
                    "project": meta.get("project", ""),
                    "lot": meta.get("lot", ""),
                    "auteur": meta.get("auteur", ""),
                    "criticite": meta.get("criticite", "Normale"),
                    "file_type": meta.get("file_type", ""),
                    "ingested_at": meta.get("ingested_at", ""),
                    "chunk_count": 0,
                }
            seen[source]["chunk_count"] += 1

        return {
            "total_chunks": len(docs),
            "total_documents": len(seen),
            "projects": sorted({d["project"] for d in seen.values() if d["project"]}),
            "documents": list(seen.values()),
            "vector_store": "chroma",
            "collection_path": os.getenv("CHROMA_PATH", "chroma_store"),
        }

    def reset(self):
        self.store.reset()

    @staticmethod
    def _build_where(filters: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not filters:
            return None
        clean = {key: value for key, value in filters.items() if value not in ("", None)}
        if not clean:
            return None
        if len(clean) == 1:
            return clean
        return {"$and": [{key: value} for key, value in clean.items()]}

    @staticmethod
    def _sources_from_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        sources = []
        seen = set()
        for chunk in chunks:
            meta = chunk.get("metadata", {})
            source = meta.get("source", "Unknown")
            key = (source, meta.get("chunk_index", ""))
            if key in seen:
                continue
            seen.add(key)
            text = chunk.get("text", "")
            sources.append({
                "filename": source,
                "project": meta.get("project", ""),
                "lot": meta.get("lot", ""),
                "criticite": meta.get("criticite", "Normale"),
                "file_type": meta.get("file_type", ""),
                "relevance_score": round(float(chunk.get("score", 0)), 3),
                "excerpt": text[:500] + "..." if len(text) > 500 else text,
                "metadata": meta,
            })
        return sources

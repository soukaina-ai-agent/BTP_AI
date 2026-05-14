"""
Chroma-backed vector store for the deployable FastAPI MVP.

The existing Flask app can continue using FAISS. This service gives the
portfolio version persistent metadata filtering and a cleaner deployment path.
"""

import hashlib
import logging
import os
from typing import Any, Dict, List, Optional

import numpy as np

from services.storage_paths import persistent_path

logger = logging.getLogger(__name__)

CHROMA_PATH = persistent_path("CHROMA_PATH", "chroma_store")
CHROMA_COLLECTION = "btp_documents"


def _stable_id(text: str, metadata: Dict[str, Any]) -> str:
    source = metadata.get("source", "")
    chunk_index = metadata.get("chunk_index", "")
    payload = f"{source}:{chunk_index}:{text[:2000]}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _to_chroma_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    clean: Dict[str, Any] = {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            clean[key] = "" if value is None else value
        else:
            clean[key] = str(value)
    return clean


class ChromaVectorStore:
    """Small wrapper around a persistent Chroma collection."""

    def __init__(
        self,
        persist_path: str = CHROMA_PATH,
        collection_name: str = CHROMA_COLLECTION,
    ):
        try:
            import chromadb
        except ImportError as e:
            raise RuntimeError("Chroma support requires chromadb. Install requirements.txt.") from e

        os.makedirs(persist_path, exist_ok=True)
        logger.info("[Chroma] Using persistent path: %s", persist_path)
        self._client = chromadb.PersistentClient(path=persist_path)
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def total_documents(self) -> int:
        return self._collection.count()

    @property
    def documents(self) -> List[Dict[str, Any]]:
        data = self._collection.get(include=["documents", "metadatas"])
        docs = data.get("documents") or []
        metas = data.get("metadatas") or []
        return [
            {"text": doc or "", "metadata": meta or {}}
            for doc, meta in zip(docs, metas)
        ]

    def add(self, texts: List[str], embeddings: np.ndarray, metadatas: List[dict]):
        if not texts:
            return

        ids = [_stable_id(text, meta) for text, meta in zip(texts, metadatas)]
        clean_metas = [_to_chroma_metadata(meta) for meta in metadatas]
        self._collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings.astype("float32").tolist(),
            metadatas=clean_metas,
        )
        logger.info("[Chroma] Upserted %s chunks", len(texts))

    def search(
        self,
        query_embedding: np.ndarray,
        k: int,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if self.total_documents == 0:
            return []

        result = self._collection.query(
            query_embeddings=[query_embedding.astype("float32").tolist()],
            n_results=min(k, self.total_documents),
            where=where or None,
            include=["documents", "metadatas", "distances"],
        )

        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        hits = []
        for doc, meta, distance in zip(docs, metas, distances):
            hits.append({
                "text": doc or "",
                "metadata": meta or {},
                "score": float(1 - distance),
            })
        return hits

    def reset(self):
        ids = self._collection.get().get("ids", [])
        if ids:
            self._collection.delete(ids=ids)
        logger.info("[Chroma] Cleared collection")

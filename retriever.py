"""
BTP AI - RAG Pipeline (Retrieval-Augmented Generation)
Handles embeddings, FAISS vector store, and LLM-based Q&A.
"""

import os
import json
import logging
import hashlib
import pickle
from typing import List, Dict, Any, Optional

import numpy as np
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
VECTOR_STORE_PATH = "vector_store"
INDEX_FILE = os.path.join(VECTOR_STORE_PATH, "faiss.index")
DOCS_FILE = os.path.join(VECTOR_STORE_PATH, "documents.pkl")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
TOP_K = int(os.getenv("TOP_K", "5"))
BASE_URL = os.getenv("BASE_URL", "https://api.openai.com/v1")
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", os.getenv("OPENAI_MODEL", "gpt-4.1"))
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
USE_OPENAI_EMBEDDINGS = os.getenv("USE_OPENAI_EMBEDDINGS", "").strip().lower()


def _openai_client():
    from openai import OpenAI

    return OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
    )


def _has_openai_key() -> bool:
    """Return True only for a real OpenAI-compatible API key."""
    key = (API_KEY or "").strip()
    if not key:
        return False
    placeholders = {
        "sk-your-openai-key-here",
        "sk-your-key-here",
        "your-openai-api-key",
        "your-api-key",
    }
    return key not in placeholders


class EmbeddingEngine:
    """Wraps SentenceTransformers (local) or OpenAI embeddings."""

    def __init__(self):
        self._model = None
        if USE_OPENAI_EMBEDDINGS in {"1", "true", "yes"}:
            self._use_openai = _has_openai_key()
        elif USE_OPENAI_EMBEDDINGS in {"0", "false", "no"}:
            self._use_openai = False
        else:
            self._use_openai = _has_openai_key()

    def _load(self):
        if self._model is not None:
            return
        if self._use_openai:
            logger.info("Using OpenAI embeddings")
            self._model = _openai_client()
        else:
            logger.info(f"Loading SentenceTransformer: {EMBEDDING_MODEL}")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(EMBEDDING_MODEL)

    def embed(self, texts: List[str]) -> np.ndarray:
        """Return embedding matrix of shape (N, dim)."""
        self._load()
        if self._use_openai:
            return self._embed_openai(texts)
        else:
            return self._model.encode(texts, show_progress_bar=False, normalize_embeddings=True)

    def _embed_openai(self, texts: List[str]) -> np.ndarray:
        response = self._model.embeddings.create(
            model=OPENAI_EMBEDDING_MODEL,
            input=texts
        )
        vecs = [item.embedding for item in response.data]
        arr = np.array(vecs, dtype="float32")
        # L2-normalize
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        return arr / np.maximum(norms, 1e-9)


class FAISSStore:
    """Simple FAISS-backed vector store with persistence."""

    def __init__(self):
        os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
        self.index = None
        self.documents: List[Dict[str, Any]] = []  # parallel list of {text, metadata}
        self._dim: Optional[int] = None
        self._load_from_disk()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, texts: List[str], embeddings: np.ndarray, metadatas: List[dict]):
        """Add new embeddings to the index."""
        import faiss
        embeddings = embeddings.astype("float32")

        if self.index is None:
            self._dim = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(self._dim)  # Inner-product (cosine with normalized vecs)

        self.index.add(embeddings)
        for text, meta in zip(texts, metadatas):
            self.documents.append({"text": text, "metadata": meta})

        self._save_to_disk()

    def search(self, query_embedding: np.ndarray, k: int = TOP_K) -> List[Dict[str, Any]]:
        """Return top-k most similar documents."""
        if self.index is None or self.index.ntotal == 0:
            return []

        query_embedding = query_embedding.astype("float32").reshape(1, -1)
        k = min(k, self.index.ntotal)
        scores, indices = self.index.search(query_embedding, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0:
                doc = self.documents[idx].copy()
                doc["score"] = float(score)
                results.append(doc)
        return results

    def reset(self):
        """Clear all data."""
        self.index = None
        self.documents = []
        self._dim = None
        for path in [INDEX_FILE, DOCS_FILE]:
            if os.path.exists(path):
                os.remove(path)
        logger.info("FAISS store cleared")

    @property
    def total_documents(self) -> int:
        return len(self.documents)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save_to_disk(self):
        try:
            import faiss
            if self.index is not None:
                faiss.write_index(self.index, INDEX_FILE)
            with open(DOCS_FILE, "wb") as f:
                pickle.dump(self.documents, f)
        except Exception as e:
            logger.warning(f"Could not persist vector store: {e}")

    def _load_from_disk(self):
        try:
            import faiss
            if os.path.exists(INDEX_FILE) and os.path.exists(DOCS_FILE):
                self.index = faiss.read_index(INDEX_FILE)
                with open(DOCS_FILE, "rb") as f:
                    self.documents = pickle.load(f)
                self._dim = self.index.d
                logger.info(f"Loaded {len(self.documents)} chunks from disk")
        except Exception as e:
            logger.warning(f"Could not load vector store from disk: {e}")


class LLMEngine:
    """Wraps OpenAI ChatCompletion (or a local fallback)."""

    def __init__(self):
        self._use_openai = _has_openai_key()
        self._openai_model = MODEL

    def generate(self, question: str, context_chunks: List[Dict[str, Any]]) -> str:
        """Generate an answer grounded in the provided context chunks."""
        context = self._build_context(context_chunks)

        system_prompt = (
            "Tu es BTP AI, un assistant expert en construction et génie civil (Bâtiment et Travaux Publics). "
            "Tu maîtrises les DTU (Documents Techniques Unifiés), les normes NF EN, les Eurocodes, "
            "la réglementation française (RE 2020, Code du Travail, sécurité incendie, amiante) "
            "et les bonnes pratiques métier BTP. "
            "\n\n"
            "RÈGLES ABSOLUES :\n"
            "1. Réponds UNIQUEMENT à partir des documents de contexte fournis.\n"
            "2. Si l'information n'est pas dans le contexte, dis clairement : "
            "'Cette information n'est pas disponible dans les documents chargés.'\n"
            "3. Cite toujours la référence du document source (ex: DTU 13.1, NF C 15-100, RE 2020).\n"
            "4. Sois précis, professionnel et structuré (utilise des listes à puces ou étapes numérotées).\n"
            "5. Pour les valeurs numériques (dimensions, résistances, températures), cite-les exactement.\n"
            "6. Réponds en français."
        )

        user_prompt = (
            f"Context documents:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Provide a clear and detailed answer based solely on the context above."
        )

        if self._use_openai:
            return self._openai_generate(system_prompt, user_prompt)
        else:
            return self._fallback_generate(question, context_chunks)

    def _openai_generate(self, system: str, user: str) -> str:
        client = _openai_client()
        response = client.chat.completions.create(
            model=self._openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
            max_tokens=1200,
        )
        return response.choices[0].message.content.strip()

    def _fallback_generate(self, question: str, chunks: List[Dict[str, Any]]) -> str:
        """
        Fallback extractif quand aucune clé API n'est configurée.
        Retourne directement les passages les plus pertinents.
        """
        if not chunks:
            return "Aucune information pertinente trouvée dans les documents chargés."

        answer_parts = [
            "⚠️  Aucune clé API LLM configurée — passages extraits directement :\n"
        ]
        for i, chunk in enumerate(chunks[:3], 1):
            source = chunk["metadata"].get("source", "Inconnu")
            answer_parts.append(f"**Passage {i}** (source : {source}) :\n{chunk['text']}\n")

        return "\n".join(answer_parts)

    @staticmethod
    def _build_context(chunks: List[Dict[str, Any]]) -> str:
        parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk["metadata"].get("source", "Unknown")
            project = chunk["metadata"].get("project", "")
            parts.append(
                f"[Document {i} | Source: {source} | Project: {project}]\n{chunk['text']}"
            )
        return "\n\n---\n\n".join(parts)


class RAGPipeline:
    """Orchestrates the full RAG workflow."""

    def __init__(self):
        self.embedder = EmbeddingEngine()
        self.store = FAISSStore()
        self.llm = LLMEngine()

    def add_documents(self, chunks: List[Dict[str, Any]]):
        """Embed and store a list of chunk dicts from the ingestor."""
        if not chunks:
            return

        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        embeddings = self.embedder.embed(texts)
        self.store.add(texts, embeddings, metadatas)
        logger.info(f"[RAG] Added {len(chunks)} chunks to vector store")

    def query(self, question: str) -> Dict[str, Any]:
        """Full RAG query: embed → retrieve → generate."""
        if self.store.total_documents == 0:
            return {
                "answer": "No documents have been uploaded yet. Please upload construction documents first.",
                "sources": [],
            }

        # 1. Embed the question
        q_embedding = self.embedder.embed([question])[0]

        # 2. Retrieve top-k relevant chunks
        relevant_chunks = self.store.search(q_embedding, k=TOP_K)

        if not relevant_chunks:
            return {
                "answer": "No relevant information found for your question.",
                "sources": [],
            }

        # 3. Generate answer with LLM
        answer = self.llm.generate(question, relevant_chunks)

        # 4. Build deduplicated source references
        seen = set()
        sources = []
        for chunk in relevant_chunks:
            meta = chunk["metadata"]
            source_key = meta.get("source", "Unknown")
            if source_key not in seen:
                seen.add(source_key)
                sources.append({
                    "filename":        source_key,
                    "project":         meta.get("project", ""),
                    "file_type":       meta.get("file_type", ""),
                    "relevance_score": round(chunk["score"], 3),
                    "excerpt":         chunk["text"][:300] + "..." if len(chunk["text"]) > 300 else chunk["text"],
                    "metadata": {
                        "lot":       meta.get("lot", ""),
                        "auteur":    meta.get("auteur", ""),
                        "criticite": meta.get("criticite", "Normale"),
                    }
                })

        logger.info(f"[RAG] Query answered using {len(relevant_chunks)} chunks from {len(sources)} sources")
        return {"answer": answer, "sources": sources}

    def get_stats(self) -> Dict[str, Any]:
        """Return system statistics with per-document metadata."""
        docs = self.store.documents
        sources = list({d["metadata"].get("source", "?") for d in docs})
        projects = list({d["metadata"].get("project", "?") for d in docs})

        # Build one row per unique source document
        seen = {}
        for d in docs:
            meta = d["metadata"]
            src = meta.get("source", "?")
            if src not in seen:
                seen[src] = {
                    "source":      src,
                    "project":     meta.get("project", ""),
                    "lot":         meta.get("lot", ""),
                    "auteur":      meta.get("auteur", ""),
                    "criticite":   meta.get("criticite", "Normale"),
                    "file_type":   meta.get("file_type", ""),
                    "ingested_at": meta.get("ingested_at", ""),
                    "chunk_count": 0,
                }
            seen[src]["chunk_count"] += 1

        return {
            "total_chunks":    len(docs),
            "total_documents": len(sources),
            "projects":        projects,
            "sources":         sources,
            "documents":       list(seen.values()),
        }

    def reset(self):
        """Clear the vector store."""
        self.store.reset()

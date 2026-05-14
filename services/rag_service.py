"""RAG service used by the FastAPI backend."""

import logging
import re
import unicodedata
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from retriever import EmbeddingEngine, LLMEngine, TOP_K
from services.vector_store import CHROMA_PATH, ChromaVectorStore

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
        limit = k or TOP_K
        semantic_hits = self.store.search(
            embedding,
            min(max(limit * 3, limit), self.store.total_documents),
            where=self._build_where(filters),
        )
        lexical_hits = self._lexical_hits(question, filters=filters, k=limit)
        return self._merge_hits(semantic_hits, lexical_hits, k=limit)

    def query(
        self,
        question: str,
        k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self._is_btp_related(question):
            return {
                "answer": "Je peux seulement repondre aux questions liees au BTP et aux documents indexes.",
                "sources": [],
            }

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
            "collection_path": CHROMA_PATH,
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

    def _lexical_hits(
        self,
        question: str,
        filters: Optional[Dict[str, Any]],
        k: int,
    ) -> List[Dict[str, Any]]:
        tokens = self._tokens(question)
        if not tokens:
            return []

        hits = []
        for doc in self.store.documents:
            meta = doc.get("metadata", {})
            if not self._matches_filters(meta, filters):
                continue

            source = meta.get("source", "")
            lot = meta.get("lot", "")
            reference = meta.get("reference", "")
            title = meta.get("titre", "")
            haystack = self._normalize_text(
                " ".join([
                    doc.get("text", ""),
                    source,
                    meta.get("project", ""),
                    lot,
                    reference,
                    title,
                    meta.get("file_type", ""),
                ])
            )
            source_norm = self._normalize_text(source)
            lot_norm = self._normalize_text(lot)
            reference_norm = self._normalize_text(reference)

            score = 0.0
            for token in tokens:
                if token in haystack:
                    score += 1.0
                if token in source_norm:
                    score += 1.0
                if token in lot_norm:
                    score += 1.5
                if token in reference_norm:
                    score += 2.0

            if "dtu" in tokens and "dtu" in haystack:
                score += 2.0

            if score > 0:
                hits.append({
                    "text": doc.get("text", ""),
                    "metadata": meta,
                    "score": score / max(len(tokens), 1),
                })

        return sorted(hits, key=lambda item: item["score"], reverse=True)[:k]

    @staticmethod
    def _merge_hits(
        semantic_hits: List[Dict[str, Any]],
        lexical_hits: List[Dict[str, Any]],
        k: int,
    ) -> List[Dict[str, Any]]:
        merged: Dict[tuple, Dict[str, Any]] = {}
        for hit in semantic_hits:
            meta = hit.get("metadata", {})
            key = (meta.get("source", ""), meta.get("chunk_index", ""))
            merged[key] = hit

        for hit in lexical_hits:
            meta = hit.get("metadata", {})
            key = (meta.get("source", ""), meta.get("chunk_index", ""))
            current = merged.get(key)
            if current is None or hit.get("score", 0) > current.get("score", 0):
                merged[key] = hit

        return sorted(merged.values(), key=lambda item: item.get("score", 0), reverse=True)[:k]

    @staticmethod
    def _matches_filters(metadata: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> bool:
        if not filters:
            return True
        for key, value in filters.items():
            if value in ("", None):
                continue
            if metadata.get(key, "") != value:
                return False
        return True

    @staticmethod
    def _normalize_text(text: Any) -> str:
        normalized = unicodedata.normalize("NFKD", str(text).lower())
        return "".join(char for char in normalized if not unicodedata.combining(char))

    @classmethod
    def _tokens(cls, text: str) -> List[str]:
        tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", cls._normalize_text(text))
        stopwords = {
            "quelles", "quelle", "quels", "quel", "sont", "pour", "les", "des",
            "dans", "avec", "sur", "une", "un", "du", "de", "la", "le", "et",
            "aux", "au", "en", "a", "l", "d",
        }
        return [token for token in tokens if token not in stopwords and len(token) > 1]

    @staticmethod
    def _is_btp_related(question: str) -> bool:
        text = RAGService._normalize_text(question)
        keywords = [
            "btp", "construction", "chantier", "travaux", "batiment", "bâtiment",
            "genie civil", "génie civil", "ouvrage", "vrd", "dtu", "norme",
            "eurocode", "cctp", "ccap", "plan", "plans", "devis", "facture",
            "beton", "béton", "armature", "ferraillage", "fondation", "dalle",
            "poteau", "poutre", "mur", "maconnerie", "maçonnerie", "toiture",
            "etancheite", "étanchéité", "isolation", "plomberie", "electricite",
            "électricité", "hvac", "chauffage", "ventilation", "securite",
            "sécurité", "conformite", "conformité", "risque", "reserve",
            "réserve", "bim", "ifc", "maquette", "document", "documents",
            "fichier", "fichiers", "email", "mail", "source", "projet", "lot",
            "civil engineering", "building", "site", "works", "contractor",
            "subcontractor", "drawing", "specification", "concrete", "rebar",
            "foundation", "slab", "beam", "column", "masonry", "roof",
            "waterproofing", "compliance", "inspection", "handover",
        ]
        keywords.extend(["masonnerie", "maconnerie", "maçonnerie"])
        return any(keyword in text for keyword in keywords)

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

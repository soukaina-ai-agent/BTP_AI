"""Regulatory intelligence service backed by the shared Chroma RAG store."""

import json
from typing import Any, Dict, List

from retriever import API_KEY, MODEL, _openai_client
from services.rag_service import RAGService


REGULATORY_SEARCH_SYSTEM_PROMPT = """
Tu es un ingénieur réglementaire BTP senior spécialisé DTU, NF, EN, ISO,
Eurocodes, CCTP et contrôle chantier.

Tu réponds uniquement à partir des extraits fournis par la base documentaire IA.
Tu n'inventes jamais une valeur, une norme, une épaisseur, une tolérance ou une
obligation absente des extraits. Si les extraits ne suffisent pas, indique
clairement que les documents indexés ne permettent pas de conclure.

Retourne un JSON strict avec:
{
  "short_answer": "...",
  "control_points": ["..."],
  "required_evidence": ["..."],
  "limits": "...",
  "confidence": "low|medium|high",
  "conformity_score": 0
}

Le conformity_score est un entier de 0 à 100 qui reflète la solidité de la
réponse au regard des preuves disponibles. Les control_points doivent être
actionnables sur chantier ou en bureau d'études. Les required_evidence doivent
être des pièces concrètes à demander: plan, note de calcul, PV, fiche technique,
attestation, extrait CCTP, visa, photo, etc. Réponds en français professionnel
et concis.
"""


REGULATORY_DECISION_SYSTEM_PROMPT = """
Tu es un auditeur technique BTP senior. Tu croises une situation chantier avec
les extraits documentaires fournis par la base documentaire IA.

Objectif: produire une fiche décision opérationnelle pour un conducteur travaux,
ingénieur travaux ou bureau de contrôle. Analyse uniquement les extraits fournis.
N'invente aucune référence réglementaire. Si une preuve manque, signale-la.

Retourne un JSON strict avec:
{
  "decision": "conforme probable|à vérifier|action prioritaire|blocage recommandé",
  "overall_severity": "low|medium|high|critical",
  "conformity_score": 0,
  "summary": "...",
  "evidence": ["..."],
  "risks": [
    {
      "title": "...",
      "severity": "low|medium|high|critical",
      "why_it_matters": "...",
      "recommendation": "...",
      "source": "..."
    }
  ],
  "required_evidence": ["..."],
  "limits": "..."
}

Le conformity_score est un entier de 0 à 100. La décision doit être prudente:
si les extraits sont insuffisants, choisis "à vérifier" et explique les preuves
manquantes.
"""


class RegulatoryService:
    """Normative search and decision workflows using the shared RAG store."""

    def __init__(self, rag: RAGService):
        self.rag = rag

    def stats(self) -> Dict[str, Any]:
        documents = self.rag.get_stats().get("documents", [])
        regulatory_docs = [doc for doc in documents if self._is_regulatory_doc(doc)]
        return {
            "total_references": len(regulatory_docs),
            "total_chunks": sum(int(doc.get("chunk_count", 0)) for doc in regulatory_docs),
            "documents": regulatory_docs,
            "vector_store": "chroma",
        }

    def search(
        self,
        question: str,
        top_k: int = 6,
        project: str = "",
        lot: str = "",
    ) -> Dict[str, Any]:
        chunks = self.rag.retrieve(question, k=top_k, filters=self._filters(project, lot))
        sources = self.rag._sources_from_chunks(chunks)
        if not chunks:
            return {
                "short_answer": "Aucun extrait pertinent n'a ete trouve dans la base indexee.",
                "control_points": [],
                "required_evidence": [],
                "limits": "Indexez des references techniques ou elargissez les filtres.",
                "confidence": "low",
                "conformity_score": 0,
                "sources": [],
            }

        payload = self._llm_json(
            REGULATORY_SEARCH_SYSTEM_PROMPT,
            f"Question: {question}\n\nExtraits:\n{self._format_context(chunks)}",
            fallback=self._fallback_search(chunks),
        )
        payload.setdefault("short_answer", "")
        payload.setdefault("control_points", [])
        payload.setdefault("required_evidence", [])
        payload.setdefault("limits", "")
        payload.setdefault("confidence", "medium")
        payload.setdefault("conformity_score", self._score_from_confidence(payload["confidence"]))
        payload["sources"] = sources
        return payload

    def decision(
        self,
        scenario: str,
        top_k: int = 8,
        project: str = "",
        lot: str = "",
    ) -> Dict[str, Any]:
        chunks = self.rag.retrieve(scenario, k=top_k, filters=self._filters(project, lot))
        sources = self.rag._sources_from_chunks(chunks)
        if not chunks:
            return {
                "decision": "à vérifier",
                "overall_severity": "low",
                "conformity_score": 0,
                "summary": "Aucun extrait pertinent n'a été trouvé pour produire une fiche décision.",
                "evidence": [],
                "risks": [],
                "required_evidence": [
                    "Ajouter ou indexer les normes, CCTP, plans et notes techniques concernes."
                ],
                "limits": "Analyse impossible sans documents sources.",
                "sources": [],
            }

        payload = self._llm_json(
            REGULATORY_DECISION_SYSTEM_PROMPT,
            f"Situation: {scenario}\n\nExtraits:\n{self._format_context(chunks)}",
            fallback=self._fallback_decision(chunks),
        )
        payload.setdefault("decision", "à vérifier")
        payload.setdefault("overall_severity", "medium")
        payload.setdefault("conformity_score", self._score_from_severity(payload["overall_severity"]))
        payload.setdefault("summary", "")
        payload.setdefault("evidence", [])
        payload.setdefault("risks", [])
        payload.setdefault("required_evidence", [])
        payload.setdefault("limits", "")
        payload["sources"] = sources
        return payload

    @staticmethod
    def upload_metadata(family: str, domain: str, source: str) -> Dict[str, Any]:
        return {
            "project": "Base normative",
            "lot": f"{family} - {domain}",
            "auteur": source,
            "criticite": "Elevee",
            "extra_metadata": {
                "knowledge_domain": "regulatory",
                "regulatory_family": family,
                "regulatory_domain": domain,
            },
        }

    @staticmethod
    def _filters(project: str = "", lot: str = "") -> Dict[str, str]:
        filters: Dict[str, str] = {}
        if project:
            filters["project"] = project
        if lot:
            filters["lot"] = lot
        return filters

    @staticmethod
    def _format_context(chunks: List[Dict[str, Any]]) -> str:
        parts = []
        for index, chunk in enumerate(chunks, 1):
            meta = chunk.get("metadata", {})
            parts.append(
                f"[Extrait {index} | Source: {meta.get('source', '?')} | "
                f"Projet: {meta.get('project', '')} | Lot: {meta.get('lot', '')} | "
                f"Famille: {meta.get('regulatory_family', '')}]\n"
                f"{chunk.get('text', '')}"
            )
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def _is_regulatory_doc(doc: Dict[str, Any]) -> bool:
        haystack = " ".join(
            str(doc.get(key, ""))
            for key in ("source", "project", "lot", "auteur", "file_type")
        ).lower()
        keywords = ("dtu", "nf", "iso", "eurocode", "norme", "reglement", "reglementaire")
        return doc.get("project") == "Base normative" or any(keyword in haystack for keyword in keywords)

    @staticmethod
    def _fallback_search(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        first = chunks[0]
        source = first.get("metadata", {}).get("source", "source inconnue")
        return {
            "short_answer": "LLM indisponible: voici les extraits les plus pertinents à vérifier.",
            "control_points": [chunk.get("text", "")[:260] for chunk in chunks[:3]],
            "required_evidence": [
                "Extrait normatif applicable",
                "Plan ou CCTP du lot concerne",
                "Note de calcul ou fiche technique si disponible",
            ],
            "limits": f"Analyse extractive sans génération LLM. Première source: {source}.",
            "confidence": "low",
            "conformity_score": 35,
        }

    @staticmethod
    def _fallback_decision(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        risks = []
        for chunk in chunks[:4]:
            meta = chunk.get("metadata", {})
            risks.append({
                "title": "Point documentaire à vérifier",
                "severity": "medium",
                "why_it_matters": chunk.get("text", "")[:320],
                "recommendation": (
                    "Vérifier la correspondance entre l'extrait, le CCTP, "
                    "les plans et la situation chantier."
                ),
                "source": meta.get("source", "Unknown"),
            })
        return {
            "decision": "à vérifier",
            "overall_severity": "medium",
            "conformity_score": 45,
            "summary": "LLM indisponible: fiche décision extractive générée à partir des passages retrouvés.",
            "evidence": [risk["source"] for risk in risks],
            "risks": risks,
            "required_evidence": ["Plans", "CCTP", "note de calcul", "PV ou fiche technique"],
            "limits": "La conclusion doit être confirmée par un responsable technique.",
        }

    @staticmethod
    def _score_from_confidence(confidence: str) -> int:
        return {"low": 40, "medium": 70, "high": 90}.get(str(confidence).lower(), 60)

    @staticmethod
    def _score_from_severity(severity: str) -> int:
        return {"low": 88, "medium": 65, "high": 42, "critical": 18}.get(
            str(severity).lower(),
            60,
        )

    @staticmethod
    def _llm_json(system_prompt: str, user_prompt: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        if not API_KEY:
            return fallback

        try:
            client = _openai_client()
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except Exception:
            return fallback

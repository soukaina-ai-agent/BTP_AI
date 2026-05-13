"""BTP compliance and risk analysis service."""

import json
from typing import Any, Dict, List, Optional

from retriever import _openai_client, MODEL, API_KEY
from services.rag_service import RAGService


COMPLIANCE_SYSTEM_PROMPT = """
Tu es un auditeur technique BTP senior. Analyse uniquement les extraits fournis.
Objectif: detecter les risques de non-conformite, omissions, incoherences et points
qui meritent une verification chantier ou bureau d'etudes.

Retourne un JSON strict avec:
{
  "summary": "...",
  "overall_severity": "low|medium|high|critical",
  "risks": [
    {
      "title": "...",
      "severity": "low|medium|high|critical",
      "evidence": "...",
      "recommendation": "...",
      "source": "..."
    }
  ]
}
Si les extraits ne permettent pas de conclure, dis-le dans le summary et limite les risques.
"""


class ComplianceService:
    """Creates a portfolio-friendly BTP risk/compliance analysis."""

    def __init__(self, rag: RAGService):
        self.rag = rag

    def analyze(
        self,
        question: str = "Analyse les risques de non-conformite BTP dans les documents indexes.",
        project: str = "",
        lot: str = "",
        k: int = 8,
    ) -> Dict[str, Any]:
        filters = {}
        if project:
            filters["project"] = project
        if lot:
            filters["lot"] = lot

        chunks = self.rag.retrieve(question, k=k, filters=filters)
        sources = self.rag._sources_from_chunks(chunks)
        if not chunks:
            return {
                "summary": "Aucun extrait pertinent n'a ete trouve pour realiser l'analyse.",
                "overall_severity": "low",
                "risks": [],
                "sources": [],
            }

        if not API_KEY:
            return self._fallback_analysis(chunks, sources)

        context = self._format_context(chunks)
        client = _openai_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": COMPLIANCE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Question d'analyse: {question}\n\nExtraits:\n{context}",
                },
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            result = {
                "summary": content,
                "overall_severity": "medium",
                "risks": [],
            }

        result.setdefault("summary", "")
        result.setdefault("overall_severity", "medium")
        result.setdefault("risks", [])
        result["sources"] = sources
        return result

    @staticmethod
    def _format_context(chunks: List[Dict[str, Any]]) -> str:
        parts = []
        for idx, chunk in enumerate(chunks, 1):
            meta = chunk.get("metadata", {})
            parts.append(
                f"[Extrait {idx} | Source: {meta.get('source', '?')} | "
                f"Projet: {meta.get('project', '')} | Lot: {meta.get('lot', '')}]\n"
                f"{chunk.get('text', '')}"
            )
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def _fallback_analysis(
        chunks: List[Dict[str, Any]],
        sources: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        keywords = {
            "critical": ["amiante", "incendie", "effondrement", "danger", "non conforme"],
            "high": ["obligatoire", "interdit", "risque", "securite", "fondation"],
            "medium": ["verification", "controle", "norme", "dtu", "reserve"],
        }
        risks = []
        for chunk in chunks[:5]:
            text = chunk.get("text", "")
            lower = text.lower()
            severity = "low"
            for level, terms in keywords.items():
                if any(term in lower for term in terms):
                    severity = level
                    break
            meta = chunk.get("metadata", {})
            risks.append({
                "title": "Point technique a verifier",
                "severity": severity,
                "evidence": text[:400] + "..." if len(text) > 400 else text,
                "recommendation": "Verifier ce point avec les documents contractuels, DTU applicables et le responsable technique.",
                "source": meta.get("source", "Unknown"),
            })

        return {
            "summary": "Analyse extractive generee sans cle LLM configuree.",
            "overall_severity": risks[0]["severity"] if risks else "low",
            "risks": risks,
            "sources": sources,
        }

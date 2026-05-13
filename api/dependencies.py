"""Shared FastAPI service instances."""

from services.compliance_service import ComplianceService
from services.rag_service import RAGService

rag_service = RAGService()
compliance_service = ComplianceService(rag_service)


def get_rag_service() -> RAGService:
    return rag_service


def get_compliance_service() -> ComplianceService:
    return compliance_service

"""Question-answering routes."""

from fastapi import APIRouter, Depends

from api.dependencies import get_rag_service
from api.schemas import QueryRequest, QueryResponse
from services.rag_service import RAGService

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
def query(request: QueryRequest, rag: RAGService = Depends(get_rag_service)):
    filters = {
        "project": request.project,
        "lot": request.lot,
        "file_type": request.file_type,
    }
    return rag.query(request.question, k=request.top_k, filters=filters)

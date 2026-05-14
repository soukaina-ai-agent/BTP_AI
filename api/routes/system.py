"""System routes."""

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from api.dependencies import get_rag_service
from services.rag_service import RAGService

router = APIRouter(tags=["system"])


@router.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@router.get("/health")
def health():
    return {"status": "ok", "service": "btp-ai-fastapi"}


@router.get("/stats")
def stats(rag: RAGService = Depends(get_rag_service)):
    return rag.get_stats()


@router.post("/reset")
def reset(rag: RAGService = Depends(get_rag_service)):
    rag.reset()
    return {"status": "success", "message": "Vector store cleared"}

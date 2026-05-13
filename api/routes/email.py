"""FastAPI email ingestion routes.

This module promotes the legacy Flask email connector into the FastAPI path:
IMAP source -> parsed email chunks -> metadata enrichment -> Chroma indexing.
"""

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from api.dependencies import get_rag_service
from api.schemas import EmailConfigureRequest, EmailFetchRequest, EmailFoldersRequest
from connectors.email_connector import email_connector
from services.rag_service import RAGService

router = APIRouter(prefix="/email", tags=["email"])


@router.post("/configure")
async def configure_email(request: EmailConfigureRequest):
    """Configure and test an IMAP email provider."""
    provider = request.provider.lower()

    if provider == "gmail":
        result = await run_in_threadpool(
            email_connector.configure_gmail,
            request.email,
            request.password,
        )
    else:
        result = await run_in_threadpool(
            email_connector.configure_outlook,
            request.email,
            request.password,
            request.server_type,
        )

    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "Email connection failed"))

    return {
        "status": "configured",
        "provider": provider,
        **result,
    }


@router.get("/status")
def email_status():
    """Return configured email providers."""
    return {
        "configured": email_connector.configured_providers,
        "gmail": email_connector.is_configured("gmail"),
        "outlook": email_connector.is_configured("outlook"),
    }


@router.post("/fetch")
async def fetch_and_index_emails(
    request: EmailFetchRequest,
    rag: RAGService = Depends(get_rag_service),
):
    """Fetch provider emails, convert them to RAG chunks, and index them."""
    provider = request.provider.lower()
    if not email_connector.is_configured(provider):
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider}' is not configured. Call /email/configure first.",
        )

    try:
        chunks, stats = await run_in_threadpool(
            email_connector.fetch,
            provider,
            request.folder,
            request.days_back,
            request.max_emails,
            request.btp_only,
            request.project,
            request.lot,
            request.criticite,
        )
        indexed_chunks = await run_in_threadpool(rag.add_documents, chunks)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Email fetch failed: {e}") from e

    return {
        "status": "success",
        "provider": provider,
        "indexed_chunks": indexed_chunks,
        "stats": stats,
        "message": (
            f"{stats.get('indexed', 0)} emails indexed "
            f"({stats.get('skipped_non_btp', 0)} non-BTP skipped)"
        ),
    }


@router.post("/folders")
async def list_email_folders(request: EmailFoldersRequest):
    """List folders for a configured provider."""
    provider = request.provider.lower()
    if not email_connector.is_configured(provider):
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider}' is not configured. Call /email/configure first.",
        )

    connector = email_connector._connectors[provider]

    def _list_folders():
        connector.connect()
        try:
            return connector.list_folders() if hasattr(connector, "list_folders") else ["INBOX"]
        finally:
            connector.disconnect()

    try:
        folders = await run_in_threadpool(_list_folders)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not list folders: {e}") from e

    return {"provider": provider, "folders": folders}

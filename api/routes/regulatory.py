"""Regulatory intelligence routes."""

import os
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from werkzeug.utils import secure_filename

from api.dependencies import get_rag_service, get_regulatory_service
from api.schemas import RegulatoryDecisionRequest, RegulatorySearchRequest
from ingest import DocumentIngestor
from services.rag_service import RAGService
from services.regulatory_service import RegulatoryService
from services.storage_paths import persistent_path

router = APIRouter(prefix="/regulatory", tags=["regulatory"])

UPLOAD_FOLDER = persistent_path("UPLOAD_FOLDER", "uploads")
ALLOWED_EXTENSIONS = {"pdf", "txt", "docx", "png", "jpg", "jpeg"}


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@router.get("/stats")
def regulatory_stats(service: RegulatoryService = Depends(get_regulatory_service)):
    return service.stats()


@router.post("/upload")
async def upload_regulatory_documents(
    files: List[UploadFile] = File(...),
    family: str = Form("DTU"),
    domain: str = Form("Structure"),
    source: str = Form("Base reglementaire E-MPGT"),
    rag: RAGService = Depends(get_rag_service),
):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    ingestor = DocumentIngestor()
    metadata = RegulatoryService.upload_metadata(family=family, domain=domain, source=source)
    responses = []

    for upload in files:
        if not upload.filename or not _allowed(upload.filename):
            responses.append({
                "filename": upload.filename or "unknown",
                "chunks": 0,
                "status": "error",
                "message": "Unsupported file type",
            })
            continue

        filename = secure_filename(upload.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            with open(path, "wb") as f:
                f.write(await upload.read())

            chunks = ingestor.process_file(
                path,
                filename,
                project=metadata["project"],
                lot=metadata["lot"],
                auteur=metadata["auteur"],
                criticite=metadata["criticite"],
                extra_metadata=metadata["extra_metadata"],
            )
            count = rag.add_documents(chunks)
            responses.append({"filename": filename, "chunks": count, "status": "success"})
        except Exception as e:
            responses.append({"filename": filename, "chunks": 0, "status": "error", "message": str(e)})

    if not responses:
        raise HTTPException(status_code=400, detail="No files provided")
    return responses


@router.post("/search")
def search_regulatory(
    request: RegulatorySearchRequest,
    service: RegulatoryService = Depends(get_regulatory_service),
):
    return service.search(
        question=request.question,
        top_k=request.top_k,
        project=request.project,
        lot=request.lot,
    )


@router.post("/decision")
def regulatory_decision(
    request: RegulatoryDecisionRequest,
    service: RegulatoryService = Depends(get_regulatory_service),
):
    return service.decision(
        scenario=request.scenario,
        top_k=request.top_k,
        project=request.project,
        lot=request.lot,
    )

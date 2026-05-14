"""Document ingestion routes."""

import os
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from werkzeug.utils import secure_filename

from api.dependencies import get_rag_service
from api.schemas import UploadResponse
from ingest import DocumentIngestor
from services.rag_service import RAGService
from services.storage_paths import persistent_path

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_FOLDER = persistent_path("UPLOAD_FOLDER", "uploads")
ALLOWED_EXTENSIONS = {"pdf", "txt", "docx", "png", "jpg", "jpeg"}


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@router.post("/upload", response_model=List[UploadResponse])
async def upload_documents(
    files: List[UploadFile] = File(...),
    project: str = Form("Projet General"),
    lot: str = Form(""),
    auteur: str = Form(""),
    criticite: str = Form("Normale"),
    rag: RAGService = Depends(get_rag_service),
):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    ingestor = DocumentIngestor()
    responses = []

    for upload in files:
        if not upload.filename or not _allowed(upload.filename):
            responses.append(UploadResponse(
                filename=upload.filename or "unknown",
                chunks=0,
                status="error",
                message="Unsupported file type",
            ))
            continue

        filename = secure_filename(upload.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            with open(path, "wb") as f:
                f.write(await upload.read())

            chunks = ingestor.process_file(
                path,
                filename,
                project=project,
                lot=lot,
                auteur=auteur,
                criticite=criticite,
            )
            count = rag.add_documents(chunks)
            responses.append(UploadResponse(filename=filename, chunks=count, status="success"))
        except Exception as e:
            responses.append(UploadResponse(
                filename=filename,
                chunks=0,
                status="error",
                message=str(e),
            ))

    if not responses:
        raise HTTPException(status_code=400, detail="No files provided")
    return responses

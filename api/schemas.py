"""Pydantic schemas for the FastAPI backend."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: Optional[int] = Field(default=None, ge=1, le=20)
    project: str = ""
    lot: str = ""
    file_type: str = ""


class Source(BaseModel):
    filename: str
    project: str = ""
    lot: str = ""
    criticite: str = ""
    file_type: str = ""
    relevance_score: float = 0
    excerpt: str = ""
    metadata: Dict[str, Any] = {}


class QueryResponse(BaseModel):
    answer: str
    sources: List[Source] = []


class ComplianceRequest(BaseModel):
    question: str = "Analyse les risques de non-conformite BTP dans les documents indexes."
    project: str = ""
    lot: str = ""
    top_k: int = Field(default=8, ge=1, le=20)


class UploadResponse(BaseModel):
    filename: str
    chunks: int
    status: str
    message: str = ""


class EmailConfigureRequest(BaseModel):
    provider: str = Field(..., pattern="^(gmail|outlook)$")
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)
    server_type: str = "outlook.com"


class EmailFetchRequest(BaseModel):
    provider: str = Field(..., pattern="^(gmail|outlook)$")
    folder: str = "INBOX"
    days_back: int = Field(default=30, ge=1, le=365)
    max_emails: int = Field(default=50, ge=1, le=200)
    btp_only: bool = True
    project: str = ""
    lot: str = ""
    criticite: str = "Normale"


class EmailFoldersRequest(BaseModel):
    provider: str = Field(..., pattern="^(gmail|outlook)$")

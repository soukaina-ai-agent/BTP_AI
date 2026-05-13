"""FastAPI entry point for the BTP AI internship MVP."""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import rag_service
from api.routes import analysis, bim, documents, email, query, system
from services.knowledge_service import autoload_knowledge

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        autoload_knowledge(rag_service)
    except Exception as e:
        logger.warning("DTU autoload failed: %s", e)
    yield


app = FastAPI(
    title="BTP AI Intelligence Platform",
    description="RAG, OCR and compliance analysis for construction documents.",
    version="0.1.0",
    lifespan=lifespan,
)

origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "*").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router)
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(analysis.router)
app.include_router(email.router)
app.include_router(bim.router)

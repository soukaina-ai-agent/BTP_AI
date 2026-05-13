# BTP AI Intelligence Platform

Internship-grade MVP for construction document intelligence: OCR ingestion, RAG search, source-grounded answers, and BTP compliance/risk analysis.

## What It Shows

- FastAPI backend with interactive `/docs`
- Streamlit demo frontend for fast presentation
- PDF/DOCX/TXT/image ingestion with OCR fallback
- Chroma vector database for deployable semantic search
- OpenAI-compatible LLM configuration via `BASE_URL`, `OPENAI_API_KEY`, `MODEL`
- Built-in DTU/BTP knowledge base autoload
- Compliance and risk analysis endpoint: `POST /analyze/compliance`
- Legacy Flask UI kept in `app.py` for local comparison

## Architecture

```text
frontend/streamlit_app.py  ->  api/main.py  ->  services/
                                      |
                                      + ingest.py
                                      + Chroma vector store
                                      + OpenAI-compatible LLM
                                      + knowledge/ DTU base
```

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env`:

```env
BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-your-key-here
MODEL=gpt-4.1
CHROMA_PATH=chroma_store
API_URL=http://localhost:8000
```

OCR for screenshots and scanned PDFs requires the native Tesseract app. On Windows, install Tesseract and either add it to PATH or set:

```env
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
OCR_LANG=fra+eng
```

## Run The FastAPI Backend

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

```text
http://localhost:8000/docs
```

## Run The Streamlit Demo

```bash
streamlit run frontend/streamlit_app.py
```

## Main API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Service health check |
| `POST` | `/documents/upload` | Upload and index PDF/DOCX/TXT/images |
| `POST` | `/query` | Ask source-grounded questions |
| `POST` | `/analyze/compliance` | Detect BTP risks and recommended actions |
| `GET` | `/stats` | Indexed document stats |
| `POST` | `/reset` | Clear Chroma collection |

## Supported Files

| Format | Parser |
|---|---|
| `.pdf` | pdfplumber, PyPDF2, PyMuPDF, OCR fallback |
| `.docx` | python-docx |
| `.txt` | built-in text reader |
| `.png`, `.jpg`, `.jpeg` | Pillow + Tesseract OCR |

## Deployment Story

MVP:

```text
Railway: FastAPI + Chroma persistent volume + file uploads
Streamlit: demo UI
```

Production upgrade:

```text
Vercel React frontend
FastAPI backend
Weaviate or managed vector DB
S3/R2 object storage
Auth, audit logs, observability
```

## Portfolio Demo Flow

1. Upload a CCTP, chantier report, scanned PDF, or screenshot.
2. Show OCR and metadata indexing.
3. Ask a technical BTP question and show cited sources.
4. Run compliance analysis.
5. Explain the scale path from Chroma/Streamlit MVP to Weaviate/React production.

## Legacy Flask App

The original Flask interface still runs:

```bash
python app.py
```

Use the FastAPI + Streamlit path for the internship demo.

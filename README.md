# E-MPGT AI

E-MPGT AI is a BTP document intelligence MVP for construction, logistics, and
technical document workflows. It combines OCR ingestion, semantic search, a
source-grounded RAG chatbot, and compliance/risk analysis behind a FastAPI
backend with a Streamlit demo frontend.

## Current Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI |
| Frontend demo | Streamlit |
| Vector database | Chroma |
| OCR | Tesseract, pdfplumber, PyPDF2, PyMuPDF |
| LLM provider | OpenAI-compatible API via `BASE_URL`, `OPENAI_API_KEY`, `MODEL` |
| Deployment | Railway, with separate backend and frontend services |

## Main Features

- Upload and index PDF, DOCX, TXT, PNG, JPG, and JPEG files.
- Extract text with parser-first ingestion and OCR fallback for scans/images.
- Ask BTP questions using RAG with cited document sources.
- Filter chat retrieval by project, lot, document type, and number of excerpts.
- Run compliance and risk analysis with `POST /analyze/compliance`.
- Track indexed content with `/stats`.
- Keep uploaded files and Chroma data on a Railway persistent volume.

## Architecture

```text
frontend/streamlit_app.py
        |
        v
api/main.py  ->  api/routes/
        |
        v
services/
  storage_paths.py
  vector_store.py
  rag_service.py
  compliance_service.py
  knowledge_service.py
```

The original Flask interface remains in `app.py` for local comparison, but the
recommended path is FastAPI plus Streamlit.

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env`:

```env
BASE_URL=https://models.github.ai/inference
OPENAI_API_KEY=replace_with_your_token
MODEL=openai/gpt-4o-mini
USE_OPENAI_EMBEDDINGS=false
CHROMA_PATH=chroma_store
CHROMA_COLLECTION=btp_documents
UPLOAD_FOLDER=uploads
API_URL=http://localhost:8000
```

For OCR on Windows, install Tesseract and either add it to `PATH` or set:

```env
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
OCR_LANG=fra+eng
```

## Run Locally

Start the backend:

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Open the API docs:

```text
http://localhost:8000/docs
```

Start the frontend in another terminal:

```bash
streamlit run frontend/streamlit_app.py
```

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Service health check |
| `POST` | `/documents/upload` | Upload and index documents |
| `POST` | `/query` | Ask source-grounded questions |
| `POST` | `/analyze/compliance` | Analyze BTP compliance and risks |
| `GET` | `/stats` | Show indexed document stats |
| `POST` | `/reset` | Clear the Chroma collection |

## Railway Deployment

Deploy the project as two Railway services from the same GitHub repo.

### Backend Service

Use the root `Dockerfile`.

Important files:

```text
Dockerfile
Procfile
railway.json
```

Start command used by the container/Procfile:

```bash
uvicorn api.main:app --host 0.0.0.0 --port ${PORT}
```

Recommended health check:

```text
/health
```

Attach a Railway volume to the backend service. The app automatically uses
`RAILWAY_VOLUME_MOUNT_PATH` when Railway provides it. A typical volume mount is:

```text
/data
```

This stores:

```text
/data/chroma_store
/data/uploads
```

Backend Railway variables:

```env
BASE_URL=https://models.github.ai/inference
OPENAI_API_KEY=your_key_here
MODEL=openai/gpt-4o-mini
USE_OPENAI_EMBEDDINGS=false
CHROMA_COLLECTION=btp_documents
CORS_ORIGINS=*
SKIP_DTU_AUTOLOAD=true
```

### Frontend Service

Use `Dockerfile.frontend`.

Important files:

```text
Dockerfile.frontend
railway.frontend.json
frontend/streamlit_app.py
```

Railway settings:

```text
Builder: Dockerfile
Dockerfile path: /Dockerfile.frontend
Public target port: 8080
```

Custom start command:

```bash
sh -c 'unset STREAMLIT_SERVER_PORT; streamlit run frontend/streamlit_app.py --server.address 0.0.0.0 --server.port ${PORT:-8080} --server.headless true'
```

Frontend Railway variables:

```env
API_URL=https://your-backend-service.up.railway.app
```

Do not set this variable:

```env
STREAMLIT_SERVER_PORT=$PORT
```

Streamlit expects `STREAMLIT_SERVER_PORT` to be a real integer. If it receives
the literal string `$PORT`, Railway logs will show:

```text
Error: Invalid value for '--server.port' (env var: 'STREAMLIT_SERVER_PORT'): '$PORT' is not a valid integer.
```

The shell-wrapped start command above lets Railway expand `PORT` correctly and
falls back to `8080` when `PORT` is not present.

## Demo Flow

1. Open the Streamlit frontend.
2. Confirm the sidebar shows the connected backend API URL.
3. Upload a BTP document from the Documents page.
4. Ask a question in Chat RAG.
5. Use filters such as project, lot, type, and number of excerpts to narrow the
   search.
6. Expand Sources to verify which indexed documents supported the answer.
7. Use the dashboard/stats views to confirm indexed chunks.

## Notes

- Keep `.env` local and never push real API keys.
- Use `USE_OPENAI_EMBEDDINGS=false` with GitHub Models unless your provider also
  supports OpenAI-compatible embedding models.
- Use `SKIP_DTU_AUTOLOAD=true` on Railway for faster startup, then set it to
  `false` later if you want the built-in knowledge base loaded automatically.

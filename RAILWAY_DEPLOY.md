# Railway Deployment

This project deploys cleanly on Railway as a FastAPI backend service. The
Streamlit UI is a separate process, so deploy it as a second service if you want
the demo frontend online too.

## 1. Before Deploying

Rotate any token that was ever saved in `.env`. Do not push `.env` to GitHub.
This repo now ignores `.env`, local virtualenvs, uploads, logs, and local vector
stores.

## 2. Backend Service

Create a Railway service from this repo. Railway will use the root `Dockerfile`.
The app listens on the Railway-provided `PORT`:

```bash
uvicorn api.main:app --host 0.0.0.0 --port ${PORT}
```

Health check path:

```text
/health
```

## 3. Persistent Volume

Attach a Railway Volume to the backend service. Recommended mount path:

```text
/data
```

The code automatically uses `RAILWAY_VOLUME_MOUNT_PATH` when Railway provides
it, storing:

```text
/data/chroma_store
/data/uploads
```

You can also set these manually:

```env
CHROMA_PATH=/data/chroma_store
UPLOAD_FOLDER=/data/uploads
```

## 4. Required Variables

Set these in Railway Variables, not in `.env`:

```env
BASE_URL=https://models.github.ai/inference
OPENAI_API_KEY=your_key_here
MODEL=openai/gpt-4.1
USE_OPENAI_EMBEDDINGS=false
CHROMA_COLLECTION=btp_documents
CORS_ORIGINS=*
SKIP_DTU_AUTOLOAD=true
```

`USE_OPENAI_EMBEDDINGS=false` keeps embeddings local with SentenceTransformers.
This avoids failures when the chat provider does not support OpenAI embedding
models.

Set `SKIP_DTU_AUTOLOAD=false` later if you want the built-in knowledge base to
load at startup. Keeping it `true` makes Railway deployment startup faster.

## 5. Optional Streamlit Service

Create a second Railway service for Streamlit with the same repo and a start
command like:

```bash
streamlit run frontend/streamlit_app.py --server.address 0.0.0.0 --server.port $PORT
```

Set:

```env
API_URL=https://your-backend-service.up.railway.app
```

## 6. Test After Deploy

Open:

```text
https://your-backend-service.up.railway.app/health
https://your-backend-service.up.railway.app/docs
```

Then test:

1. Upload a small PDF or TXT.
2. Ask a question in `/docs` or Streamlit.
3. Check `/stats` to confirm chunks are indexed.

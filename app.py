"""
BTP AI - Construction Data Intelligence System
Main Flask Application
"""

import os
import logging
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from ingest import DocumentIngestor
from retriever import RAGPipeline
from knowledge import get_all_knowledge_chunks, KNOWLEDGE_SUMMARY
from connectors import email_connector

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("btp_ai.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max upload
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["ALLOWED_EXTENSIONS"] = {"pdf", "txt", "docx", "png", "jpg", "jpeg"}
app.secret_key = os.getenv("SECRET_KEY", "btp-ai-secret-key-2024")

# Ensure upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initialize components
ingestor = DocumentIngestor()
rag = RAGPipeline()


def _autoload_dtu_knowledge():
    """
    Charge automatiquement la base DTU au démarrage si elle n'est pas déjà présente.
    Peut être désactivé avec SKIP_DTU_AUTOLOAD=true dans .env
    """
    if os.getenv("SKIP_DTU_AUTOLOAD", "").lower() in ("1", "true", "yes"):
        logger.info("[DTU] Chargement automatique désactivé (SKIP_DTU_AUTOLOAD=true)")
        return

    stats = rag.get_stats()
    builtin = [d for d in stats.get("documents", []) if "[BASE DTU]" in d.get("source", "")]

    if builtin:
        logger.info(f"[DTU] Base de connaissances déjà présente ({len(builtin)} fiches)")
        return

    logger.info("[DTU] Chargement initial de la base DTU/Normes BTP...")
    chunks = get_all_knowledge_chunks()
    try:
        rag.add_documents(chunks)
        logger.info(f"[DTU] ✅ {len(chunks)} fiches de connaissances indexées")
    except Exception as e:
        logger.error(f"[DTU] Erreur lors du chargement : {e}")


# Auto-chargement au démarrage
_autoload_dtu_knowledge()


def allowed_file(filename):
    """Check if file extension is allowed."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


@app.route("/")
def index():
    """Render the main UI."""
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_files():
    """Handle file upload and ingestion."""
    if "files" not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist("files")
    if not files or all(f.filename == "" for f in files):
        return jsonify({"error": "No files selected"}), 400

    project_name = request.form.get("project", "Projet Général")
    lot          = request.form.get("lot", "")
    auteur       = request.form.get("auteur", "")
    criticite    = request.form.get("criticite", "Normale")
    results = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            logger.info(f"Saved file: {filename}")

            try:
                # Ingest the document with full metadata
                chunks = ingestor.process_file(
                    filepath, filename, project_name,
                    lot=lot, auteur=auteur, criticite=criticite
                )
                # Add to vector store
                rag.add_documents(chunks)

                results.append({
                    "filename": filename,
                    "status": "success",
                    "chunks": len(chunks)
                })
                logger.info(f"Ingested {len(chunks)} chunks from {filename}")
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
                results.append({
                    "filename": filename,
                    "status": "error",
                    "message": str(e)
                })
        else:
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": "File type not allowed"
            })

    success_count = sum(1 for r in results if r["status"] == "success")
    return jsonify({
        "message": f"Processed {success_count}/{len(results)} files successfully",
        "results": results
    })


@app.route("/query", methods=["POST"])
def query():
    """Handle a natural language question."""
    data = request.get_json()
    if not data or "question" not in data:
        return jsonify({"error": "No question provided"}), 400

    question = data["question"].strip()
    if not question:
        return jsonify({"error": "Question cannot be empty"}), 400

    logger.info(f"Query received: {question}")

    try:
        result = rag.query(question)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Query error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/stats", methods=["GET"])
def stats():
    """Return system stats."""
    try:
        return jsonify(rag.get_stats())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/knowledge", methods=["GET"])
def knowledge_info():
    """Return built-in DTU knowledge base summary."""
    return jsonify({
        "summary": KNOWLEDGE_SUMMARY,
        "categories": [
            {"key": "dtu_gros_oeuvre",       "label": "Gros Œuvre",            "count": KNOWLEDGE_SUMMARY["dtu_gros_oeuvre"]},
            {"key": "dtu_etancheite",         "label": "Étanchéité / Couverture","count": KNOWLEDGE_SUMMARY["dtu_etancheite"]},
            {"key": "dtu_isolation",          "label": "Isolation thermique",    "count": KNOWLEDGE_SUMMARY["dtu_isolation"]},
            {"key": "dtu_plomberie",          "label": "Plomberie / Sanitaires", "count": KNOWLEDGE_SUMMARY["dtu_plomberie"]},
            {"key": "dtu_electricite",        "label": "Électricité",            "count": KNOWLEDGE_SUMMARY["dtu_electricite"]},
            {"key": "dtu_cvc",                "label": "CVC / Chauffage",        "count": KNOWLEDGE_SUMMARY["dtu_cvc"]},
            {"key": "normes_reglementation",  "label": "Normes & Réglementation","count": KNOWLEDGE_SUMMARY["normes_reglementation"]},
            {"key": "dtu_vrd",                "label": "VRD / Voirie",           "count": KNOWLEDGE_SUMMARY["dtu_vrd"]},
            {"key": "dtu_incendie",           "label": "Sécurité Incendie",      "count": KNOWLEDGE_SUMMARY["dtu_incendie"]},
            {"key": "dtu_environnement",      "label": "Environnement / Acoustique","count": KNOWLEDGE_SUMMARY["dtu_environnement"]},
        ]
    })


@app.route("/reload-knowledge", methods=["POST"])
def reload_knowledge():
    """Force reload of the built-in DTU knowledge base."""
    try:
        # Remove existing built-in docs then re-add
        chunks = get_all_knowledge_chunks()
        rag.add_documents(chunks)
        logger.info(f"[DTU] Rechargement manuel : {len(chunks)} fiches")
        return jsonify({"message": f"{len(chunks)} fiches DTU rechargées avec succès"})
    except Exception as e:
        logger.error(f"[DTU] Erreur rechargement : {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/reset", methods=["POST"])
def reset():
    """Clear user documents from the vector store, then reload DTU knowledge."""
    try:
        rag.reset()
        # Clean uploads folder
        for f in os.listdir(app.config["UPLOAD_FOLDER"]):
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], f))
        # Reload built-in DTU knowledge automatically
        _autoload_dtu_knowledge()
        logger.info("System reset: uploads cleared, DTU base reloaded")
        return jsonify({"message": "Système réinitialisé. Base DTU rechargée automatiquement."})
    except Exception as e:
        logger.error(f"Reset error: {e}")
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════
# EMAIL CONNECTOR ROUTES
# ════════════════════════════════════════════════════════

@app.route("/email/configure", methods=["POST"])
def email_configure():
    """Configure a Gmail or Outlook connector and test the connection."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données manquantes"}), 400

    provider    = data.get("provider", "").lower()
    email_addr  = data.get("email", "").strip()
    password    = data.get("password", "").strip()
    server_type = data.get("server_type", "outlook.com")

    if not email_addr or not password:
        return jsonify({"error": "Email et mot de passe requis"}), 400

    try:
        if provider == "gmail":
            result = email_connector.configure_gmail(email_addr, password)
        elif provider == "outlook":
            result = email_connector.configure_outlook(email_addr, password, server_type)
        else:
            return jsonify({"error": "Provider invalide. Choisir 'gmail' ou 'outlook'"}), 400

        if result["ok"]:
            logger.info(f"[Email] Connecteur {provider} configuré : {email_addr}")
            return jsonify(result)
        else:
            return jsonify(result), 401

    except Exception as e:
        logger.error(f"[Email] Erreur configuration : {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/email/status", methods=["GET"])
def email_status():
    """Return which email providers are currently configured."""
    return jsonify({
        "configured": email_connector.configured_providers,
        "gmail":   email_connector.is_configured("gmail"),
        "outlook": email_connector.is_configured("outlook"),
    })


@app.route("/email/fetch", methods=["POST"])
def email_fetch():
    """Fetch emails from a configured provider and index them."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données manquantes"}), 400

    provider   = data.get("provider", "").lower()
    folder     = data.get("folder", "INBOX")
    days_back  = int(data.get("days_back", 30))
    max_emails = int(data.get("max_emails", 50))
    btp_only   = bool(data.get("btp_only", True))
    project    = data.get("project", "")
    lot        = data.get("lot", "")
    criticite  = data.get("criticite", "Normale")

    if not email_connector.is_configured(provider):
        return jsonify({"error": f"Provider '{provider}' non configuré. Connectez-vous d'abord."}), 400

    try:
        chunks, stats = email_connector.fetch(
            provider=provider,
            folder=folder,
            days_back=days_back,
            max_emails=max_emails,
            btp_only=btp_only,
            project=project,
            lot=lot,
            criticite=criticite,
        )

        if chunks:
            rag.add_documents(chunks)
            logger.info(f"[Email] {len(chunks)} emails indexés depuis {provider}")

        return jsonify({
            "message": f"{stats['indexed']} emails indexés ({stats['skipped_non_btp']} non-BTP ignorés)",
            "stats":   stats,
            "chunks":  len(chunks),
        })

    except Exception as e:
        logger.error(f"[Email] Erreur fetch : {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/email/folders", methods=["POST"])
def email_folders():
    """List available IMAP folders for a configured Gmail provider."""
    data     = request.get_json()
    provider = (data or {}).get("provider", "gmail").lower()

    if not email_connector.is_configured(provider):
        return jsonify({"error": "Provider non configuré"}), 400

    try:
        connector = email_connector._connectors[provider]
        connector.connect()
        folders   = connector.list_folders() if hasattr(connector, "list_folders") else ["INBOX"]
        connector.disconnect()
        return jsonify({"folders": folders})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    logger.info("Starting BTP AI Construction Intelligence System")
    app.run(debug=True, host="0.0.0.0", port=5000)

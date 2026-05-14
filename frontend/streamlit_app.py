"""Streamlit frontend for the BTP AI platform."""

import os
from typing import Dict

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="BTP AI",
    page_icon="BT",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1180px;
        padding-top: 1.25rem;
    }
    [data-testid="stSidebar"] {
        min-width: 245px;
    }
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        justify-content: flex-start;
        border-radius: 8px;
        min-height: 42px;
        border: 1px solid transparent;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        border-color: rgba(49, 91, 255, 0.32);
    }
    .main-title {
        font-size: 1.75rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .muted {
        color: rgba(49, 51, 63, 0.72);
        font-size: 0.94rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_post(path: str, **kwargs):
    response = requests.post(f"{API_URL}{path}", timeout=120, **kwargs)
    response.raise_for_status()
    return response.json()


def api_get(path: str):
    response = requests.get(f"{API_URL}{path}", timeout=30)
    response.raise_for_status()
    return response.json()


def metadata_filters(prefix: str = "filter") -> Dict[str, str]:
    with st.expander("Filtres de recherche", expanded=False):
        col1, col2, col3 = st.columns(3)
        return {
            "project": col1.text_input("Projet", key=f"{prefix}_project"),
            "lot": col2.text_input("Lot", key=f"{prefix}_lot"),
            "file_type": col3.selectbox(
                "Type",
                ["", "pdf", "docx", "txt", "png", "jpg", "jpeg", "knowledge", "email", "bim"],
                key=f"{prefix}_file_type",
            ),
        }


def sidebar_nav() -> str:
    pages = [
        ("Chat RAG", "chat"),
        ("Documents", "upload_file"),
        ("Tableau de bord", "dashboard"),
        ("Knowledge", "database"),
    ]
    if "page" not in st.session_state:
        st.session_state.page = pages[0][0]

    with st.sidebar:
        st.markdown("### BTP AI")
        st.caption("Assistant documents, emails et BIM")
        for label, icon in pages:
            is_active = st.session_state.page == label
            if st.button(
                label,
                icon=f":material/{icon}:",
                type="primary" if is_active else "secondary",
                key=f"nav_{label}",
            ):
                st.session_state.page = label
        st.divider()
        st.caption(f"API: {API_URL}")

    return st.session_state.page


def render_chat():
    st.markdown('<div class="main-title">Chat RAG BTP</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="muted">Questions basees sur la base intelligente: documents, emails, BIM et connaissances indexees.</div>',
        unsafe_allow_html=True,
    )

    filters = metadata_filters("chat")
    top_k = st.slider("Nombre d'extraits", 3, 20, 6, key="chat_top_k")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": "Bonjour. Posez une question BTP sur les documents indexes.",
                "sources": [],
            }
        ]

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message.get("sources"):
                with st.expander("Sources"):
                    for source in message["sources"]:
                        st.markdown(f"**{source['filename']}** | score {source['relevance_score']}")
                        st.write(source.get("excerpt", ""))

    question = st.chat_input("Question BTP...")
    if not question:
        return

    st.session_state.chat_messages.append({"role": "user", "content": question, "sources": []})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Recherche RAG et reponse LLM..."):
                result = api_post(
                    "/query",
                    json={
                        "question": question,
                        "top_k": top_k,
                        **filters,
                    },
                )
            answer = result.get("answer", "")
            sources = result.get("sources", [])
            st.write(answer)
            if sources:
                with st.expander("Sources"):
                    for source in sources:
                        st.markdown(f"**{source['filename']}** | score {source['relevance_score']}")
                        st.write(source.get("excerpt", ""))
            st.session_state.chat_messages.append(
                {"role": "assistant", "content": answer, "sources": sources}
            )
        except Exception as e:
            error = f"Erreur query: {e}"
            st.error(error)
            st.session_state.chat_messages.append(
                {"role": "assistant", "content": error, "sources": []}
            )


def render_documents():
    st.markdown('<div class="main-title">Documents</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">Indexer des PDF, DOCX, TXT, screenshots ou photos.</div>', unsafe_allow_html=True)

    files = st.file_uploader(
        "Fichiers",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )
    col1, col2, col3, col4 = st.columns(4)
    project = col1.text_input("Projet", "Projet Demo")
    lot = col2.text_input("Lot", "")
    auteur = col3.text_input("Auteur", "")
    criticite = col4.selectbox("Criticite", ["Normale", "Elevee", "Critique"])

    if st.button("Indexer", type="primary", disabled=not files):
        payload_files = [
            ("files", (file.name, file.getvalue(), file.type or "application/octet-stream"))
            for file in files
        ]
        data = {
            "project": project,
            "lot": lot,
            "auteur": auteur,
            "criticite": criticite,
        }
        try:
            with st.spinner("Extraction, OCR, embeddings et indexation..."):
                result = api_post("/documents/upload", files=payload_files, data=data)
            st.success("Indexation terminee")
            st.dataframe(result, use_container_width=True)
        except Exception as e:
            st.error(f"Erreur upload: {e}")


def render_analysis():
    st.subheader("Conformite et risques")
    col1, col2 = st.columns(2)
    analysis_project = col1.text_input("Projet a analyser", "", key="analysis_project")
    analysis_lot = col2.text_input("Lot a analyser", "", key="analysis_lot")
    analysis_question = st.text_area(
        "Objectif d'analyse",
        "Analyse les risques de non-conformite BTP, omissions, incoherences et actions recommandees.",
        height=100,
        key="analysis_question",
    )
    analysis_k = st.slider("Extraits analyses", 4, 20, 8, key="analysis_k")

    if st.button("Analyser les risques", type="primary"):
        try:
            with st.spinner("Analyse metier en cours..."):
                result = api_post(
                    "/analyze/compliance",
                    json={
                        "question": analysis_question,
                        "project": analysis_project,
                        "lot": analysis_lot,
                        "top_k": analysis_k,
                    },
                )
            st.metric("Severite globale", result.get("overall_severity", "medium"))
            st.write(result.get("summary", ""))
            for risk in result.get("risks", []):
                st.warning(f"{risk.get('severity', '').upper()} - {risk.get('title', '')}")
                st.write(risk.get("evidence", ""))
                st.info(risk.get("recommendation", ""))
                st.caption(f"Source: {risk.get('source', '')}")
            with st.expander("Sources utilisees"):
                st.json(result.get("sources", []))
        except Exception as e:
            st.error(f"Erreur analyse: {e}")


def render_email():
    st.subheader("Email")
    st.caption("IMAP -> extraction texte -> metadonnees -> embeddings -> Chroma")

    try:
        status = api_get("/email/status")
        configured = ", ".join(status.get("configured", [])) or "aucun"
        st.info(f"Providers configures: {configured}")
    except Exception as e:
        st.warning(f"Statut email indisponible: {e}")

    col1, col2 = st.columns(2)
    provider = col1.selectbox("Provider", ["gmail", "outlook"], key="email_provider")
    email_addr = col2.text_input("Adresse email", key="email_addr")
    password = st.text_input("Mot de passe / app password", type="password", key="email_password")
    server_type = "outlook.com"
    if provider == "outlook":
        server_type = st.selectbox(
            "Serveur Outlook",
            ["outlook.com", "office365", "exchange", "hotmail.com", "live.com"],
            key="email_server_type",
        )

    if st.button("Configurer email", type="primary", disabled=not email_addr or not password):
        try:
            result = api_post(
                "/email/configure",
                json={
                    "provider": provider,
                    "email": email_addr,
                    "password": password,
                    "server_type": server_type,
                },
            )
            st.success(f"{result.get('provider', provider)} configure")
            if result.get("folders"):
                st.caption("Dossiers: " + ", ".join(result["folders"][:8]))
        except Exception as e:
            st.error(f"Erreur configuration email: {e}")

    col1, col2, col3 = st.columns(3)
    folder = col1.text_input("Dossier IMAP", "INBOX", key="email_folder")
    days_back = col2.number_input("Jours a remonter", min_value=1, max_value=365, value=30)
    max_emails = col3.number_input("Max emails", min_value=1, max_value=200, value=20)

    col1, col2, col3 = st.columns(3)
    email_project = col1.text_input("Projet", key="email_project")
    email_lot = col2.text_input("Lot", key="email_lot")
    email_criticite = col3.selectbox("Criticite", ["Normale", "Elevee", "Critique"], key="email_criticite")
    btp_only = st.checkbox("Filtrer les emails non-BTP", value=True)

    if st.button("Importer les emails", disabled=not provider):
        try:
            with st.spinner("Recuperation IMAP, parsing, embeddings et indexation..."):
                result = api_post(
                    "/email/fetch",
                    json={
                        "provider": provider,
                        "folder": folder,
                        "days_back": int(days_back),
                        "max_emails": int(max_emails),
                        "btp_only": btp_only,
                        "project": email_project,
                        "lot": email_lot,
                        "criticite": email_criticite,
                    },
                )
            st.success(result.get("message", "Emails indexes"))
            st.json(result.get("stats", {}))
        except Exception as e:
            st.error(f"Erreur import email: {e}")


def render_bim():
    st.subheader("BIM")
    st.caption("IFC -> elements, quantites, metadonnees, embeddings")

    ifc_file = st.file_uploader(
        "Fichier IFC",
        type=["ifc"],
        accept_multiple_files=False,
        key="bim_ifc_file",
    )

    col1, col2, col3, col4 = st.columns(4)
    bim_project = col1.text_input("Projet", key="bim_project")
    bim_lot = col2.text_input("Lot", "BIM / Maquette", key="bim_lot")
    bim_auteur = col3.text_input("Auteur", key="bim_auteur")
    bim_criticite = col4.selectbox("Criticite", ["Normale", "Elevee", "Critique"], key="bim_criticite")

    col1, col2 = st.columns(2)
    if col1.button("Previsualiser IFC", disabled=not ifc_file):
        try:
            payload = {
                "file": (
                    ifc_file.name,
                    ifc_file.getvalue(),
                    ifc_file.type or "application/octet-stream",
                )
            }
            with st.spinner("Analyse IFC..."):
                result = api_post("/bim/ifc/summary", files=payload)
            st.json(result.get("summary", {}))
            st.dataframe(result.get("sample_elements", []), use_container_width=True)
        except Exception as e:
            st.error(f"Erreur BIM summary: {e}")

    if col2.button("Indexer IFC", type="primary", disabled=not ifc_file):
        try:
            payload = {
                "file": (
                    ifc_file.name,
                    ifc_file.getvalue(),
                    ifc_file.type or "application/octet-stream",
                )
            }
            data = {
                "project": bim_project,
                "lot": bim_lot,
                "auteur": bim_auteur,
                "criticite": bim_criticite,
            }
            with st.spinner("Extraction BIM, embeddings et indexation..."):
                result = api_post("/bim/ifc/upload", files=payload, data=data)
            st.success(result.get("message", "Maquette BIM indexee"))
            st.dataframe([result], use_container_width=True)
        except Exception as e:
            st.error(f"Erreur indexation BIM: {e}")


def render_dashboard():
    st.markdown('<div class="main-title">Tableau de bord</div>', unsafe_allow_html=True)

    try:
        stats = api_get("/stats")
        c1, c2, c3 = st.columns(3)
        c1.metric("Chunks", stats.get("total_chunks", 0))
        c2.metric("Documents", stats.get("total_documents", 0))
        c3.metric("Vector store", stats.get("vector_store", ""))
    except Exception as e:
        st.warning(f"Stats indisponibles: {e}")

    tabs = st.tabs(["Email", "Conformite", "BIM"])
    with tabs[0]:
        render_email()
    with tabs[1]:
        render_analysis()
    with tabs[2]:
        render_bim()


def render_knowledge():
    st.markdown('<div class="main-title">Knowledge</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">Vue des documents indexes dans la base intelligente.</div>', unsafe_allow_html=True)

    try:
        stats = api_get("/stats")
        c1, c2, c3 = st.columns(3)
        c1.metric("Chunks", stats.get("total_chunks", 0))
        c2.metric("Documents", stats.get("total_documents", 0))
        c3.metric("Vector store", stats.get("vector_store", ""))
        st.dataframe(stats.get("documents", []), use_container_width=True)
    except Exception as e:
        st.error(f"Impossible de charger les stats: {e}")

    if st.button("Reset vector store"):
        try:
            api_post("/reset")
            st.success("Vector store vide")
        except Exception as e:
            st.error(f"Erreur reset: {e}")


page = sidebar_nav()

if page == "Chat RAG":
    render_chat()
elif page == "Documents":
    render_documents()
elif page == "Tableau de bord":
    render_dashboard()
else:
    render_knowledge()

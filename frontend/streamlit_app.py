"""Streamlit frontend for the BTP AI platform."""

import os
from pathlib import Path
from typing import Dict

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")
APP_ROOT = Path(__file__).resolve().parents[1]
LOGO_PATH = APP_ROOT / "image.png"

st.set_page_config(
    page_title="E-MPGT AI",
    page_icon="EM",
    layout="wide",
    initial_sidebar_state="expanded",
)

if LOGO_PATH.exists():
    try:
        st.logo(str(LOGO_PATH), size="large")
    except Exception:
        pass

st.markdown(
    """
    <style>
    :root {
        --empgt-navy: #071f3d;
        --empgt-blue: #123d68;
        --empgt-green: #43a047;
        --empgt-green-dark: #2f7d32;
        --empgt-ink: #172033;
        --empgt-muted: #667085;
        --empgt-border: #d9e2ec;
        --empgt-bg: #f5f8fb;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background: var(--empgt-bg);
        color: var(--empgt-ink);
    }

    .block-container {
        max-width: 1220px;
        padding-top: 1.1rem;
        padding-bottom: 2.5rem;
    }

    header[data-testid="stHeader"] {
        background: rgba(245, 248, 251, 0.86);
        border-bottom: 1px solid rgba(217, 226, 236, 0.78);
        backdrop-filter: blur(10px);
    }

    [data-testid="stSidebar"] {
        min-width: 260px;
        background: #ffffff;
        border-right: 1px solid var(--empgt-border);
    }

    [data-testid="stSidebar"] [data-testid="stImage"] {
        margin-bottom: 0.35rem;
    }

    [data-testid="stSidebarHeader"] img,
    [data-testid="stSidebarNav"] img {
        max-height: 82px;
        width: auto;
    }

    [data-testid="stSidebar"] hr {
        margin: 1.05rem 0;
        border-color: var(--empgt-border);
    }

    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        justify-content: flex-start;
        border-radius: 7px;
        min-height: 43px;
        border: 1px solid transparent;
        color: var(--empgt-navy);
        background: transparent;
        font-weight: 600;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        border-color: rgba(67, 160, 71, 0.35);
        background: rgba(67, 160, 71, 0.08);
        color: var(--empgt-green-dark);
    }

    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        border-color: rgba(67, 160, 71, 0.35);
        background: rgba(67, 160, 71, 0.12);
        color: var(--empgt-green-dark);
    }

    .stButton > button[kind="primary"],
    .stDownloadButton > button[kind="primary"] {
        background: var(--empgt-green);
        border-color: var(--empgt-green);
        color: #ffffff;
        border-radius: 7px;
    }

    .stButton > button[kind="primary"]:hover,
    .stDownloadButton > button[kind="primary"]:hover {
        background: var(--empgt-green-dark);
        border-color: var(--empgt-green-dark);
        color: #ffffff;
    }

    .main-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        padding: 0.15rem 0 1rem 0;
        margin-bottom: 0.75rem;
        border-bottom: 1px solid var(--empgt-border);
    }

    .main-title-wrap {
        min-width: 0;
    }

    .main-title {
        color: var(--empgt-navy);
        font-size: 1.7rem;
        font-weight: 750;
        line-height: 1.15;
        margin: 0 0 0.22rem 0;
    }

    .muted {
        color: var(--empgt-muted);
        font-size: 0.94rem;
        line-height: 1.45;
    }

    .brand-eyebrow {
        color: var(--empgt-green-dark);
        font-size: 0.74rem;
        font-weight: 800;
        letter-spacing: 0;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }

    .brand-status {
        align-items: center;
        background: #ffffff;
        border: 1px solid var(--empgt-border);
        border-radius: 7px;
        color: var(--empgt-blue);
        display: inline-flex;
        font-size: 0.82rem;
        font-weight: 650;
        gap: 0.45rem;
        padding: 0.48rem 0.68rem;
        white-space: nowrap;
    }

    .brand-dot {
        background: var(--empgt-green);
        border-radius: 999px;
        display: inline-block;
        height: 0.55rem;
        width: 0.55rem;
    }

    .sidebar-brand {
        color: var(--empgt-navy);
        font-size: 0.98rem;
        font-weight: 800;
        margin-top: 0.35rem;
    }

    .sidebar-caption {
        color: var(--empgt-muted);
        font-size: 0.82rem;
        line-height: 1.35;
        margin-bottom: 0.75rem;
    }

    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid var(--empgt-border);
        border-radius: 8px;
        padding: 0.9rem 1rem;
    }

    div[data-testid="stMetricLabel"] p {
        color: var(--empgt-muted);
        font-weight: 650;
    }

    div[data-testid="stMetricValue"] {
        color: var(--empgt-navy);
    }

    [data-testid="stFileUploader"] section {
        background: #ffffff;
        border-color: rgba(18, 61, 104, 0.18);
        border-radius: 8px;
    }

    .stChatMessage {
        border-radius: 8px;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.35rem;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 7px;
        color: var(--empgt-blue);
        font-weight: 650;
        padding: 0.55rem 0.85rem;
    }

    @media (max-width: 720px) {
        .main-header {
            align-items: flex-start;
            flex-direction: column;
        }

        .brand-status {
            white-space: normal;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def page_header(title: str, subtitle: str, eyebrow: str = "E-MPGT AI") -> None:
    st.markdown(
        f"""
        <div class="main-header">
            <div class="main-title-wrap">
                <div class="brand-eyebrow">{eyebrow}</div>
                <div class="main-title">{title}</div>
                <div class="muted">{subtitle}</div>
            </div>
            <div class="brand-status"><span class="brand-dot"></span> API connectee</div>
        </div>
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
        st.markdown('<div class="sidebar-brand">E-MPGT AI</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sidebar-caption">Construction, logistique et documents intelligents.</div>',
            unsafe_allow_html=True,
        )
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
        st.caption(f"API connectee: {API_URL}")

    return st.session_state.page


def render_chat():
    page_header(
        "Chat RAG BTP",
        "Questions basees sur les documents, emails, BIM et connaissances indexees.",
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
    page_header(
        "Documents",
        "Indexez des PDF, DOCX, TXT, screenshots ou photos pour enrichir la base intelligente.",
    )

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
    page_header(
        "Tableau de bord",
        "Suivez l'etat de la base, les connecteurs et les analyses metier.",
    )

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
    page_header(
        "Knowledge",
        "Vue simple des documents indexes dans la base intelligente.",
    )

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

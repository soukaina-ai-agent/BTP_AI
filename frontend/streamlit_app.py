"""Streamlit demo frontend for the BTP AI internship MVP."""

import os
from typing import Dict

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="BTP AI Intelligence Platform",
    page_icon="🏗️",
    layout="wide",
)


def api_post(path: str, **kwargs):
    response = requests.post(f"{API_URL}{path}", timeout=120, **kwargs)
    response.raise_for_status()
    return response.json()


def api_get(path: str):
    response = requests.get(f"{API_URL}{path}", timeout=30)
    response.raise_for_status()
    return response.json()


def metadata_filters() -> Dict[str, str]:
    with st.expander("Filtres de recherche", expanded=False):
        col1, col2, col3 = st.columns(3)
        return {
            "project": col1.text_input("Projet", key="filter_project"),
            "lot": col2.text_input("Lot", key="filter_lot"),
            "file_type": col3.selectbox(
                "Type",
                ["", "pdf", "docx", "txt", "png", "jpg", "jpeg", "knowledge", "email", "bim"],
                key="filter_file_type",
            ),
        }


st.title("BTP AI Intelligence Platform")
st.caption("RAG + OCR + analyse de conformité pour documents BTP")

tabs = st.tabs(["Upload", "Question/Réponse", "Conformité & Risques", "Email", "BIM", "Knowledge Base"])

with tabs[0]:
    st.subheader("Indexer des documents")
    files = st.file_uploader(
        "PDF, DOCX, TXT, screenshots ou photos",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )
    col1, col2, col3, col4 = st.columns(4)
    project = col1.text_input("Projet", "Projet Démo")
    lot = col2.text_input("Lot", "")
    auteur = col3.text_input("Auteur", "")
    criticite = col4.selectbox("Criticité", ["Normale", "Élevée", "Critique"])

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
            with st.spinner("Extraction, OCR si nécessaire, embeddings et indexation..."):
                result = api_post("/documents/upload", files=payload_files, data=data)
            st.success("Indexation terminée")
            st.dataframe(result, use_container_width=True)
        except Exception as e:
            st.error(f"Erreur upload: {e}")

with tabs[1]:
    st.subheader("Interroger les documents")
    filters = metadata_filters()
    question = st.text_area(
        "Question",
        "Quels sont les points importants et les obligations techniques dans les documents ?",
        height=120,
    )
    top_k = st.slider("Nombre d'extraits", 3, 20, 6)
    if st.button("Rechercher", type="primary"):
        try:
            with st.spinner("Recherche sémantique et génération de réponse..."):
                result = api_post("/query", json={
                    "question": question,
                    "top_k": top_k,
                    **filters,
                })
            st.markdown("### Réponse")
            st.write(result["answer"])
            st.markdown("### Sources")
            for source in result.get("sources", []):
                with st.expander(f"{source['filename']} | score {source['relevance_score']}"):
                    st.write(source.get("excerpt", ""))
                    st.json(source.get("metadata", {}))
        except Exception as e:
            st.error(f"Erreur query: {e}")

with tabs[2]:
    st.subheader("Analyse conformité et risques")
    col1, col2 = st.columns(2)
    analysis_project = col1.text_input("Projet à analyser", "")
    analysis_lot = col2.text_input("Lot à analyser", "")
    analysis_question = st.text_area(
        "Objectif d'analyse",
        "Analyse les risques de non-conformité BTP, omissions, incohérences et actions recommandées.",
        height=100,
    )
    analysis_k = st.slider("Extraits analysés", 4, 20, 8)

    if st.button("Analyser les risques", type="primary"):
        try:
            with st.spinner("Analyse métier en cours..."):
                result = api_post("/analyze/compliance", json={
                    "question": analysis_question,
                    "project": analysis_project,
                    "lot": analysis_lot,
                    "top_k": analysis_k,
                })
            st.metric("Sévérité globale", result.get("overall_severity", "medium"))
            st.write(result.get("summary", ""))
            for risk in result.get("risks", []):
                st.warning(f"{risk.get('severity', '').upper()} - {risk.get('title', '')}")
                st.write(risk.get("evidence", ""))
                st.info(risk.get("recommendation", ""))
                st.caption(f"Source: {risk.get('source', '')}")
            with st.expander("Sources utilisées"):
                st.json(result.get("sources", []))
        except Exception as e:
            st.error(f"Erreur analyse: {e}")

with tabs[3]:
    st.subheader("Connecteur email")
    st.caption("IMAP -> extraction texte -> métadonnées -> embeddings -> Chroma")

    try:
        status = api_get("/email/status")
        configured = ", ".join(status.get("configured", [])) or "aucun"
        st.info(f"Providers configurés: {configured}")
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
            result = api_post("/email/configure", json={
                "provider": provider,
                "email": email_addr,
                "password": password,
                "server_type": server_type,
            })
            st.success(f"{result.get('provider', provider)} configuré")
            if result.get("folders"):
                st.caption("Dossiers: " + ", ".join(result["folders"][:8]))
        except Exception as e:
            st.error(f"Erreur configuration email: {e}")

    st.markdown("### Importer et indexer")
    col1, col2, col3 = st.columns(3)
    folder = col1.text_input("Dossier IMAP", "INBOX", key="email_folder")
    days_back = col2.number_input("Jours à remonter", min_value=1, max_value=365, value=30)
    max_emails = col3.number_input("Max emails", min_value=1, max_value=200, value=20)

    col1, col2, col3 = st.columns(3)
    email_project = col1.text_input("Projet", key="email_project")
    email_lot = col2.text_input("Lot", key="email_lot")
    email_criticite = col3.selectbox("Criticité", ["Normale", "Élevée", "Critique"], key="email_criticite")
    btp_only = st.checkbox("Filtrer les emails non-BTP", value=True)

    if st.button("Importer les emails", disabled=not provider):
        try:
            with st.spinner("Récupération IMAP, parsing, embeddings et indexation..."):
                result = api_post("/email/fetch", json={
                    "provider": provider,
                    "folder": folder,
                    "days_back": int(days_back),
                    "max_emails": int(max_emails),
                    "btp_only": btp_only,
                    "project": email_project,
                    "lot": email_lot,
                    "criticite": email_criticite,
                })
            st.success(result.get("message", "Emails indexés"))
            st.json(result.get("stats", {}))
        except Exception as e:
            st.error(f"Erreur import email: {e}")


with tabs[4]:
    st.subheader("Indexer une maquette BIM")
    st.caption("IFC -> extraction elements/quantites -> metadonnees -> embeddings -> Chroma")

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


with tabs[5]:
    st.subheader("Documents indexés")
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
            st.success("Vector store vidé")
        except Exception as e:
            st.error(f"Erreur reset: {e}")

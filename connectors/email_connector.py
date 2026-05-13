"""
BTP AI — Email Connector
=========================
Connecteur email pour Gmail et Outlook (Microsoft 365).
Supporte deux modes d'authentification :
  - Gmail   : OAuth2 (recommandé) ou IMAP + mot de passe d'application
  - Outlook : OAuth2 via Microsoft Graph API ou IMAP

Le module extrait les emails, nettoie le contenu HTML/texte,
détecte les projets BTP dans les sujets/corps, et retourne
des chunks prêts à être vectorisés.
"""

import os
import re
import email
import email.message
import email.header
import email.utils
import imaplib
import logging
import hashlib
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime

logger = logging.getLogger(__name__)

# ── Constantes ───────────────────────────────────────────

MAX_EMAIL_BODY_CHARS = 4000   # Tronquer les très longs emails
MAX_EMAILS_PER_FETCH = 50     # Limite par session
EMAIL_SOURCE_PREFIX  = "[EMAIL]"


# ════════════════════════════════════════════════════════
# Parseur de contenu email
# ════════════════════════════════════════════════════════

class EmailParser:
    """Extrait et nettoie le contenu textuel des messages email."""

    BTP_KEYWORDS = [
        "chantier", "projet", "travaux", "devis", "facture", "plan",
        "béton", "fondation", "maçonnerie", "électricité", "plomberie",
        "chauffage", "isolation", "toiture", "étanchéité", "DTU", "norme",
        "sécurité", "EPI", "réception", "livraison", "délai", "budget",
        "marché", "appel d'offres", "sous-traitant", "fournisseur",
        "maître d'ouvrage", "maître d'œuvre", "architecte", "bureau d'études",
        "construction", "rénovation", "permis", "urbanisme", "VRD",
        # English construction vocabulary, for mixed FR/EN inboxes.
        "project", "site", "construction", "works", "civil works", "building",
        "renovation", "permit", "planning permission", "building permit",
        "quote", "quotation", "invoice", "contract", "tender", "bid",
        "contractor", "subcontractor", "supplier", "architect", "engineer",
        "design office", "consultant", "client", "owner", "developer",
        "drawing", "drawings", "plan", "blueprint", "specification", "specs",
        "method statement", "inspection", "approval", "handover", "delivery",
        "schedule", "delay", "deadline", "milestone", "progress", "budget",
        "concrete", "reinforced concrete", "rebar", "reinforcement",
        "foundation", "footing", "masonry", "brickwork", "blockwork",
        "steel", "formwork", "slab", "beam", "column", "wall",
        "roof", "roofing", "waterproofing", "insulation", "facade",
        "electrical", "plumbing", "hvac", "heating", "ventilation",
        "drainage", "earthworks", "excavation", "roadworks", "utilities",
        "safety", "ppe", "risk", "compliance", "standard", "code",
        "regulation", "snag", "defect", "non-conformity", "nonconformity",
    ]

    def parse_message(self, raw_msg: email.message.Message) -> Dict[str, Any]:
        """Extraire toutes les métadonnées et le corps d'un message email."""
        subject  = self._decode_header_value(raw_msg.get("Subject", ""))
        sender   = raw_msg.get("From", "")
        to       = raw_msg.get("To", "")
        date_str = raw_msg.get("Date", "")
        msg_id   = raw_msg.get("Message-ID", "")

        # Nom et adresse expéditeur
        sender_name, sender_email = parseaddr(sender)
        sender_name = self._decode_header_value(sender_name)

        # Date normalisée
        try:
            date_obj = parsedate_to_datetime(date_str)
            date_iso = date_obj.isoformat()
        except Exception:
            date_iso = datetime.utcnow().isoformat()

        # Corps de l'email
        body = self._extract_body(raw_msg)
        body = self._clean_body(body)

        # Pièces jointes
        attachments = self._list_attachments(raw_msg)

        # Détection BTP
        btp_score    = self._btp_relevance_score(subject, body)
        project_hint = self._detect_project(subject, body)

        # Hash pour déduplication
        content_hash = hashlib.md5(
            (msg_id + subject + body[:200]).encode("utf-8", errors="ignore")
        ).hexdigest()[:12]

        return {
            "subject":      subject,
            "sender_name":  sender_name,
            "sender_email": sender_email,
            "to":           to,
            "date":         date_iso,
            "body":         body[:MAX_EMAIL_BODY_CHARS],
            "attachments":  attachments,
            "btp_score":    btp_score,
            "project_hint": project_hint,
            "msg_id":       msg_id,
            "hash":         content_hash,
        }

    # ── Private helpers ──────────────────────────────────

    def _decode_header_value(self, value: str) -> str:
        """Décoder les en-têtes encodés (RFC 2047)."""
        if not value:
            return ""
        parts = decode_header(value)
        decoded = []
        for part, charset in parts:
            if isinstance(part, bytes):
                try:
                    decoded.append(part.decode(charset or "utf-8", errors="replace"))
                except Exception:
                    decoded.append(part.decode("utf-8", errors="replace"))
            else:
                decoded.append(str(part))
        return " ".join(decoded).strip()

    def _extract_body(self, msg: email.message.Message) -> str:
        """Extraire le corps texte du message (préfère text/plain)."""
        body_plain = []
        body_html  = []

        if msg.is_multipart():
            for part in msg.walk():
                ct   = part.get_content_type()
                disp = str(part.get("Content-Disposition", ""))
                if "attachment" in disp:
                    continue
                payload = self._decode_payload(part)
                if ct == "text/plain":
                    body_plain.append(payload)
                elif ct == "text/html":
                    body_html.append(payload)
        else:
            ct      = msg.get_content_type()
            payload = self._decode_payload(msg)
            if ct == "text/plain":
                body_plain.append(payload)
            elif ct == "text/html":
                body_html.append(payload)

        if body_plain:
            return "\n".join(body_plain)
        if body_html:
            return self._html_to_text("\n".join(body_html))
        return ""

    def _decode_payload(self, part: email.message.Message) -> str:
        """Décoder le payload en tenant compte du charset."""
        charset = part.get_content_charset() or "utf-8"
        try:
            payload = part.get_payload(decode=True)
            if payload:
                return payload.decode(charset, errors="replace")
        except Exception:
            pass
        return ""

    def _html_to_text(self, html: str) -> str:
        """Conversion HTML → texte brut simple."""
        # Remplacer les balises de structure par sauts de ligne
        html = re.sub(r"<br\s*/?>|<p[^>]*>|</p>|<div[^>]*>|</div>|<tr[^>]*>", "\n", html, flags=re.IGNORECASE)
        html = re.sub(r"<li[^>]*>", "\n• ", html, flags=re.IGNORECASE)
        # Supprimer tous les tags HTML restants
        html = re.sub(r"<[^>]+>", " ", html)
        # Décoder les entités HTML courantes
        html = html.replace("&nbsp;", " ").replace("&amp;", "&")
        html = html.replace("&lt;", "<").replace("&gt;", ">")
        html = html.replace("&quot;", '"').replace("&#39;", "'")
        return html

    def _clean_body(self, text: str) -> str:
        """Nettoyer et normaliser le corps du message."""
        if not text:
            return ""
        # Supprimer les signatures (ligne contenant -- ou ___)
        text = re.split(r"\n--\s*\n|\n_{3,}\n", text)[0]
        # Supprimer les réponses citées (lignes commençant par >)
        lines = [l for l in text.splitlines() if not l.strip().startswith(">")]
        text = "\n".join(lines)
        # Normaliser les espaces
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    def _list_attachments(self, msg: email.message.Message) -> List[str]:
        """Lister les noms des pièces jointes."""
        attachments = []
        if msg.is_multipart():
            for part in msg.walk():
                disp     = str(part.get("Content-Disposition", ""))
                filename = part.get_filename()
                if filename or "attachment" in disp:
                    name = self._decode_header_value(filename or "inconnu")
                    attachments.append(name)
        return attachments

    def _btp_relevance_score(self, subject: str, body: str) -> int:
        """Score de pertinence BTP (0-10)."""
        text  = (subject + " " + body[:500]).lower()
        score = sum(1 for kw in self.BTP_KEYWORDS if kw.lower() in text)
        return min(score, 10)

    def _detect_project(self, subject: str, body: str) -> str:
        """Tenter de détecter le nom du projet depuis l'objet ou le corps."""
        # Patterns explicites uniquement. Un simple "Objet: Bonjour" ne doit
        # pas devenir un nom de projet.
        patterns = [
            r"\[(?:projet|chantier|opération|project|job|site)\s*:?\s*([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s\-_]{2,60})\]",
            r"(?:projet|chantier|opération|project|job|site)\s*:?\s*([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s\-_]{2,60}?)(?:\s*[-–|,]|\s*\n|$)",
            r"(?:réf|ref|référence|reference)\s+(?:projet|chantier|project|job|site)\s*:?\s*([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s\-_]{2,60}?)(?:\s*[-–|,]|\s*\n|$)",
        ]
        for pat in patterns:
            m = re.search(pat, subject + "\n" + body[:200], re.IGNORECASE)
            if m:
                candidate = m.group(1).strip(" -_:\n\t")[:60]
                first_word = candidate.lower().split(" ", 1)[0] if candidate else ""
                generic = {
                    "et", "de", "des", "du", "la", "le", "les", "un", "une",
                    "travaux", "btp", "construction", "validation", "réunion", "reunion",
                    "and", "of", "the", "a", "an", "works", "building", "approval",
                    "meeting", "inspection", "update", "status",
                }
                if candidate and first_word not in generic:
                    return candidate
        return ""


# ════════════════════════════════════════════════════════
# Convertisseur Email → Chunks RAG
# ════════════════════════════════════════════════════════

class EmailChunkBuilder:
    """Convertit un email parsé en chunk(s) pour le RAG."""

    def build(
        self,
        parsed: Dict[str, Any],
        provider: str,
        project: str = "",
        lot: str = "",
        criticite: str = "Normale",
    ) -> List[Dict[str, Any]]:
        """Construire un chunk RAG à partir d'un email parsé."""

        # Texte structuré du chunk
        project_name = (project or parsed.get("project_hint") or "").strip()
        source_id    = f"{EMAIL_SOURCE_PREFIX} {provider} — {parsed['hash']}"

        text = (
            f"EMAIL — {provider.upper()}\n"
            f"De      : {parsed['sender_name']} <{parsed['sender_email']}>\n"
            f"Objet   : {parsed['subject']}\n"
            f"Date    : {parsed['date'][:10]}\n"
            f"Projet  : {project_name}\n"
        )
        if parsed["attachments"]:
            text += f"PJ      : {', '.join(parsed['attachments'])}\n"
        text += f"\n{parsed['body']}"

        metadata = {
            "source":       source_id,
            "project":      project_name,
            "lot":          lot,
            "auteur":       parsed["sender_name"] or parsed["sender_email"],
            "criticite":    criticite,
            "file_type":    "email",
            "provider":     provider,
            "subject":      parsed["subject"],
            "sender_email": parsed["sender_email"],
            "date":         parsed["date"],
            "btp_score":    parsed["btp_score"],
            "attachments":  parsed["attachments"],
            "msg_hash":     parsed["hash"],
            "ingested_at":  datetime.utcnow().isoformat(),
            "total_chunks": 1,
            "chunk_index":  0,
            "is_email":     True,
        }

        return [{"text": text.strip(), "metadata": metadata}]


# ════════════════════════════════════════════════════════
# Connecteur Gmail (IMAP)
# ════════════════════════════════════════════════════════

class GmailIMAPConnector:
    """
    Connexion Gmail via IMAP avec mot de passe d'application Google.
    (Recommandé pour démarrage rapide sans OAuth2.)

    Prérequis Google :
      1. Activer IMAP dans Gmail → Paramètres → Transfert et POP/IMAP
      2. Activer la validation en deux étapes
      3. Créer un "Mot de passe d'application" (16 caractères)
      4. Utiliser ce mot de passe (pas le mot de passe principal)
    """

    IMAP_HOST = "imap.gmail.com"
    IMAP_PORT = 993

    def __init__(self, email_addr: str, app_password: str):
        self.email_addr   = email_addr
        self.app_password = app_password
        self._conn: Optional[imaplib.IMAP4_SSL] = None
        self.parser = EmailParser()
        self.builder = EmailChunkBuilder()

    def connect(self) -> bool:
        """Établir la connexion IMAP."""
        try:
            self._conn = imaplib.IMAP4_SSL(self.IMAP_HOST, self.IMAP_PORT)
            self._conn.login(self.email_addr, self.app_password)
            logger.info(f"[Gmail IMAP] Connecté : {self.email_addr}")
            return True
        except imaplib.IMAP4.error as e:
            logger.error(f"[Gmail IMAP] Erreur connexion : {e}")
            return False

    def disconnect(self):
        """Fermer la connexion proprement."""
        if self._conn:
            try:
                self._conn.logout()
            except Exception:
                pass
            self._conn = None

    def fetch_emails(
        self,
        folder: str = "INBOX",
        days_back: int = 30,
        max_emails: int = MAX_EMAILS_PER_FETCH,
        btp_only: bool = True,
        project: str = "",
        lot: str = "",
        criticite: str = "Normale",
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Récupérer et parser les emails du dossier spécifié.

        Returns:
            (chunks, stats) : liste de chunks RAG + rapport de session
        """
        if not self._conn:
            raise RuntimeError("Non connecté. Appeler connect() d'abord.")

        # Sélectionner le dossier
        status, _ = self._conn.select(folder)
        if status != "OK":
            raise RuntimeError(f"Impossible d'ouvrir le dossier : {folder}")

        # Construire le critère de recherche IMAP
        since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
        search_criteria = f'(SINCE "{since_date}")'

        _, msg_numbers = self._conn.search(None, search_criteria)
        all_ids = msg_numbers[0].split()

        # Limiter + ordre anti-chronologique (les plus récents en premier)
        email_ids = all_ids[-max_emails:][::-1]

        chunks     = []
        stats      = {"fetched": 0, "indexed": 0, "skipped_non_btp": 0, "errors": 0}
        seen_hashes: set = set()

        for eid in email_ids:
            try:
                _, data = self._conn.fetch(eid, "(RFC822)")
                raw     = data[0][1]
                msg     = email.message_from_bytes(raw)
                parsed  = self.parser.parse_message(msg)
                stats["fetched"] += 1

                # Déduplication
                if parsed["hash"] in seen_hashes:
                    continue
                seen_hashes.add(parsed["hash"])

                # Filtrer les emails non-BTP si demandé
                if btp_only and parsed["btp_score"] == 0:
                    stats["skipped_non_btp"] += 1
                    continue

                email_chunks = self.builder.build(parsed, "Gmail", project, lot, criticite)
                chunks.extend(email_chunks)
                stats["indexed"] += 1

            except Exception as e:
                logger.warning(f"[Gmail IMAP] Erreur sur email {eid} : {e}")
                stats["errors"] += 1

        logger.info(f"[Gmail IMAP] {stats}")
        return chunks, stats

    def list_folders(self) -> List[str]:
        """Lister les dossiers disponibles."""
        if not self._conn:
            return []
        _, folders = self._conn.list()
        result = []
        for f in folders:
            parts = f.decode().split('"/"')
            if parts:
                name = parts[-1].strip().strip('"')
                result.append(name)
        return result

    def test_connection(self) -> Dict[str, Any]:
        """Tester la connexion et retourner les informations de compte."""
        ok = self.connect()
        if not ok:
            return {"ok": False, "error": "Échec de la connexion IMAP"}
        folders = self.list_folders()
        self.disconnect()
        return {
            "ok": True,
            "email": self.email_addr,
            "provider": "Gmail",
            "folders": folders[:10],
        }


# ════════════════════════════════════════════════════════
# Connecteur Outlook / Microsoft 365 (IMAP)
# ════════════════════════════════════════════════════════

class OutlookIMAPConnector:
    """
    Connexion Outlook / Microsoft 365 via IMAP.

    Prérequis Microsoft :
      1. Activer IMAP dans Outlook.com : Paramètres → Mail → Synchronisation
      2. Pour Microsoft 365 Pro : l'admin IT doit activer IMAP dans Exchange Admin Center
      3. Utiliser le mot de passe du compte (ou un mot de passe d'application si MFA activé)

    Serveurs IMAP :
      - Outlook.com / Hotmail : imap-mail.outlook.com : 993
      - Microsoft 365 / Exchange Online : outlook.office365.com : 993
    """

    IMAP_HOSTS = {
        "outlook.com":  "imap-mail.outlook.com",
        "hotmail.com":  "imap-mail.outlook.com",
        "live.com":     "imap-mail.outlook.com",
        "office365":    "outlook.office365.com",
        "exchange":     "outlook.office365.com",
    }
    IMAP_PORT = 993

    def __init__(self, email_addr: str, password: str, server_type: str = "outlook.com"):
        self.email_addr  = email_addr
        self.password    = password
        self.imap_host   = self.IMAP_HOSTS.get(server_type, "outlook.office365.com")
        self._conn: Optional[imaplib.IMAP4_SSL] = None
        self.parser  = EmailParser()
        self.builder = EmailChunkBuilder()

    def connect(self) -> bool:
        """Établir la connexion IMAP Outlook."""
        try:
            self._conn = imaplib.IMAP4_SSL(self.imap_host, self.IMAP_PORT)
            self._conn.login(self.email_addr, self.password)
            logger.info(f"[Outlook IMAP] Connecté : {self.email_addr} via {self.imap_host}")
            return True
        except imaplib.IMAP4.error as e:
            logger.error(f"[Outlook IMAP] Erreur connexion : {e}")
            return False

    def disconnect(self):
        if self._conn:
            try:
                self._conn.logout()
            except Exception:
                pass
            self._conn = None

    def fetch_emails(
        self,
        folder: str = "INBOX",
        days_back: int = 30,
        max_emails: int = MAX_EMAILS_PER_FETCH,
        btp_only: bool = True,
        project: str = "",
        lot: str = "",
        criticite: str = "Normale",
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Récupérer et indexer les emails Outlook."""
        if not self._conn:
            raise RuntimeError("Non connecté. Appeler connect() d'abord.")

        # Outlook stocke la boîte de réception en anglais "INBOX" ou en français
        status, _ = self._conn.select(f'"{folder}"')
        if status != "OK":
            # Essai sans guillemets
            status, _ = self._conn.select(folder)
            if status != "OK":
                raise RuntimeError(f"Impossible d'ouvrir le dossier : {folder}")

        since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
        _, msg_numbers = self._conn.search(None, f'(SINCE "{since_date}")')
        all_ids = msg_numbers[0].split()
        email_ids = all_ids[-max_emails:][::-1]

        chunks = []
        stats  = {"fetched": 0, "indexed": 0, "skipped_non_btp": 0, "errors": 0}
        seen_hashes: set = set()

        for eid in email_ids:
            try:
                _, data = self._conn.fetch(eid, "(RFC822)")
                raw     = data[0][1]
                msg     = email.message_from_bytes(raw)
                parsed  = self.parser.parse_message(msg)
                stats["fetched"] += 1

                if parsed["hash"] in seen_hashes:
                    continue
                seen_hashes.add(parsed["hash"])

                if btp_only and parsed["btp_score"] == 0:
                    stats["skipped_non_btp"] += 1
                    continue

                email_chunks = self.builder.build(parsed, "Outlook", project, lot, criticite)
                chunks.extend(email_chunks)
                stats["indexed"] += 1

            except Exception as e:
                logger.warning(f"[Outlook IMAP] Erreur sur email {eid} : {e}")
                stats["errors"] += 1

        logger.info(f"[Outlook IMAP] {stats}")
        return chunks, stats

    def test_connection(self) -> Dict[str, Any]:
        ok = self.connect()
        if not ok:
            return {"ok": False, "error": "Échec de la connexion IMAP Outlook"}
        self.disconnect()
        return {
            "ok": True,
            "email": self.email_addr,
            "provider": "Outlook",
            "host": self.imap_host,
        }


# ════════════════════════════════════════════════════════
# Façade unifiée EmailConnector
# ════════════════════════════════════════════════════════

class EmailConnector:
    """
    Point d'entrée unique pour tous les connecteurs email.
    Gère Gmail et Outlook de manière transparente.
    """

    def __init__(self):
        self._connectors: Dict[str, Any] = {}

    def configure_gmail(self, email_addr: str, app_password: str) -> Dict[str, Any]:
        """Configurer et tester le connecteur Gmail."""
        connector = GmailIMAPConnector(email_addr, app_password)
        result = connector.test_connection()
        if result["ok"]:
            self._connectors["gmail"] = connector
            logger.info(f"[EmailConnector] Gmail configuré : {email_addr}")
        return result

    def configure_outlook(
        self,
        email_addr: str,
        password: str,
        server_type: str = "outlook.com"
    ) -> Dict[str, Any]:
        """Configurer et tester le connecteur Outlook."""
        connector = OutlookIMAPConnector(email_addr, password, server_type)
        result = connector.test_connection()
        if result["ok"]:
            self._connectors["outlook"] = connector
            logger.info(f"[EmailConnector] Outlook configuré : {email_addr}")
        return result

    def fetch(
        self,
        provider: str,
        folder: str = "INBOX",
        days_back: int = 30,
        max_emails: int = MAX_EMAILS_PER_FETCH,
        btp_only: bool = True,
        project: str = "",
        lot: str = "",
        criticite: str = "Normale",
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Récupérer les emails du provider spécifié.

        Args:
            provider    : "gmail" ou "outlook"
            folder      : dossier IMAP (INBOX, Sent, etc.)
            days_back   : nombre de jours à remonter
            max_emails  : nombre maximum d'emails à traiter
            btp_only    : filtrer les emails non-BTP
            project     : nom du projet à associer
            lot         : lot technique
            criticite   : niveau de criticité

        Returns:
            (chunks, stats)
        """
        key = provider.lower()
        if key not in self._connectors:
            raise ValueError(f"Provider '{provider}' non configuré.")

        connector = self._connectors[key]
        connector.connect()
        try:
            chunks, stats = connector.fetch_emails(
                folder=folder,
                days_back=days_back,
                max_emails=max_emails,
                btp_only=btp_only,
                project=project,
                lot=lot,
                criticite=criticite,
            )
        finally:
            connector.disconnect()

        return chunks, stats

    @property
    def configured_providers(self) -> List[str]:
        """Liste des providers actuellement configurés."""
        return list(self._connectors.keys())

    def is_configured(self, provider: str) -> bool:
        return provider.lower() in self._connectors


# ── Instance globale (utilisée par app.py) ──────────────
email_connector = EmailConnector()

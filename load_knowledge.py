"""
BTP AI — Script de chargement de la base DTU/Normes
====================================================
Exécuter UNE FOIS avant de lancer l'application :

    python load_knowledge.py

Ce script charge toute la base de connaissances BTP intégrée
(DTU, NF EN, réglementation, sécurité, environnement) dans
la base vectorielle FAISS locale.

Options :
    --reset    Réinitialise la base avant chargement
    --stats    Affiche uniquement les statistiques, sans charger
"""

import sys
import os
import time
import logging
import argparse

# ── Setup ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from knowledge.dtu_knowledge_base import get_all_knowledge_chunks, KNOWLEDGE_SUMMARY
from retriever import RAGPipeline


def print_banner():
    print("\n" + "═" * 60)
    print("  BTP AI — Chargement Base de Connaissances DTU / Normes")
    print("═" * 60)


def print_summary():
    print("\n📚 Contenu de la base de connaissances :")
    print(f"  {'Gros Œuvre (DTU 13/20/21/22/23)':<40} {KNOWLEDGE_SUMMARY['dtu_gros_oeuvre']:>3} fiches")
    print(f"  {'Étanchéité / Couverture (DTU 40/43)':<40} {KNOWLEDGE_SUMMARY['dtu_etancheite']:>3} fiches")
    print(f"  {'Isolation thermique (DTU 45)':<40} {KNOWLEDGE_SUMMARY['dtu_isolation']:>3} fiches")
    print(f"  {'Plomberie / Sanitaires (DTU 60)':<40} {KNOWLEDGE_SUMMARY['dtu_plomberie']:>3} fiches")
    print(f"  {'Électricité (NF C 15-100 / 14-100)':<40} {KNOWLEDGE_SUMMARY['dtu_electricite']:>3} fiches")
    print(f"  {'CVC / Chauffage (DTU 65)':<40} {KNOWLEDGE_SUMMARY['dtu_cvc']:>3} fiches")
    print(f"  {'Normes & Réglementation (RE2020/EC)':<40} {KNOWLEDGE_SUMMARY['normes_reglementation']:>3} fiches")
    print(f"  {'VRD / Voirie / ANC (DTU 64/70)':<40} {KNOWLEDGE_SUMMARY['dtu_vrd']:>3} fiches")
    print(f"  {'Sécurité Incendie (ERP / Euroclasse)':<40} {KNOWLEDGE_SUMMARY['dtu_incendie']:>3} fiches")
    print(f"  {'Environnement / Acoustique':<40} {KNOWLEDGE_SUMMARY['dtu_environnement']:>3} fiches")
    print(f"  {'─'*44}")
    print(f"  {'TOTAL':<40} {KNOWLEDGE_SUMMARY['total']:>3} fiches")
    print()


def load_knowledge(reset: bool = False):
    print_banner()
    print_summary()

    rag = RAGPipeline()

    if reset:
        print("🔄  Réinitialisation de la base vectorielle...")
        rag.reset()
        print("    Base réinitialisée.\n")

    # Vérifier si déjà chargée
    stats = rag.get_stats()
    builtin_docs = [d for d in stats.get("documents", []) if "[BASE DTU]" in d.get("source", "")]

    if builtin_docs and not reset:
        print(f"ℹ️  La base DTU est déjà chargée ({len(builtin_docs)} fiches indexées).")
        print("    Utilisez --reset pour recharger depuis zéro.\n")
        return

    # Charger les chunks
    chunks = get_all_knowledge_chunks()
    print(f"⚙️  Vectorisation de {len(chunks)} fiches de connaissances...")
    print("    (Premier lancement : téléchargement du modèle d'embeddings ~90 MB)\n")

    t0 = time.time()

    # Traitement par lots pour afficher la progression
    batch_size = 5
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        rag.add_documents(batch)
        done = min(i + batch_size, len(chunks))
        pct  = int(done / len(chunks) * 100)
        bar  = "█" * (pct // 5) + "░" * (20 - pct // 5)
        print(f"\r    [{bar}] {pct:3d}%  ({done}/{len(chunks)})", end="", flush=True)

    elapsed = time.time() - t0
    print(f"\n\n✅  Base chargée en {elapsed:.1f}s")

    # Stats finales
    final_stats = rag.get_stats()
    print(f"\n📊  Base vectorielle :")
    print(f"    Documents indexés : {final_stats['total_documents']}")
    print(f"    Chunks total      : {final_stats['total_chunks']}")
    print(f"\n🚀  Lancez maintenant : python app.py")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chargement base DTU BTP AI")
    parser.add_argument("--reset", action="store_true", help="Réinitialiser avant chargement")
    parser.add_argument("--stats", action="store_true", help="Afficher stats sans charger")
    args = parser.parse_args()

    if args.stats:
        print_banner()
        print_summary()
    else:
        load_knowledge(reset=args.reset)

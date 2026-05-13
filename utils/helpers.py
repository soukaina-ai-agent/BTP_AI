"""
BTP AI - Utility Helpers
"""

import os
import re
import hashlib
from typing import Optional


def truncate_text(text: str, max_chars: int = 300) -> str:
    """Truncate text to max_chars, ending at a word boundary."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > max_chars * 0.8:
        truncated = truncated[:last_space]
    return truncated + "..."


def file_hash(filepath: str) -> str:
    """Return MD5 hash of a file for deduplication."""
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sanitize_project_name(name: str) -> str:
    """Remove special characters from a project name."""
    return re.sub(r"[^\w\s\-]", "", name).strip() or "General"


def format_file_size(size_bytes: int) -> str:
    """Human-readable file size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def get_env_info() -> dict:
    """Return current configuration for diagnostics."""
    return {
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "embedding_model": os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        "openai_base_url": os.getenv("BASE_URL", "https://api.openai.com/v1"),
        "openai_model": os.getenv("MODEL", os.getenv("OPENAI_MODEL", "gpt-4.1")),
        "top_k": int(os.getenv("TOP_K", "5")),
    }

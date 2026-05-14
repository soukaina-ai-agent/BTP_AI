"""Storage path helpers for local development and Railway deployments."""

import os


def persistent_path(env_name: str, default_name: str) -> str:
    """Return a writable persistent path.

    Locally, relative paths like ``chroma_store`` remain in the repo.
    On Railway, relative paths are placed under the mounted volume so data
    survives container restarts.
    """
    configured = os.getenv(env_name)
    volume_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")

    if configured and os.path.isabs(configured):
        return configured

    name = configured or default_name
    if volume_path:
        return os.path.join(volume_path, name)
    return name

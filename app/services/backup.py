"""SQLite backups using the online backup API."""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime

from app.config import settings


def _sqlite_path(url: str) -> str:
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        return ""
    path = url[len(prefix):]
    if path.startswith("/"):
        return path
    # Relative to working directory.
    return path


def create_backup() -> str:
    """Create a safe online backup and return its path."""
    src = _sqlite_path(settings.database_url)
    if not src:
        raise RuntimeError("Backups are only supported for SQLite.")

    os.makedirs(settings.backup_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    dest = os.path.join(settings.backup_dir, f"training-{ts}.db")

    src_conn = sqlite3.connect(src)
    try:
        dest_conn = sqlite3.connect(dest)
        try:
            with dest_conn:
                src_conn.backup(dest_conn)
        finally:
            dest_conn.close()
    finally:
        src_conn.close()
    return dest


def list_backups() -> list[str]:
    if not os.path.isdir(settings.backup_dir):
        return []
    files = [f for f in os.listdir(settings.backup_dir) if f.endswith(".db")]
    return sorted(files, reverse=True)

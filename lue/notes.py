"""Markdown notes for books, stored in the system Documents folder.

One Markdown file per book, named after the book. Every appended note is
timestamped (12h am/pm or 24h, configurable via config.NOTES_TIME_FORMAT)
and can carry a reading-position reference.
"""

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

from . import config

_12H_PATTERNS = ("12", "12h", "ampm", "am/pm")


def get_documents_dir() -> Path:
    """Resolve the user's system Documents folder.

    Prefers the XDG user dir (localized, e.g. ~/Documentos), then
    ~/Documents, then the home directory.
    """
    try:
        result = subprocess.run(
            ["xdg-user-dir", "DOCUMENTS"],
            capture_output=True, text=True, timeout=2
        )
        docs = result.stdout.strip()
        if result.returncode == 0 and docs and os.path.isdir(docs):
            return Path(docs)
    except Exception:
        pass

    docs = Path.home() / "Documents"
    if docs.is_dir():
        return docs
    return Path.home()


def sanitize_book_title(book_title: str) -> str:
    """Sanitize a book title for use as a file name."""
    safe = re.sub(r'[^\w\s()-]', '', book_title).strip()
    safe = re.sub(r'\s+', ' ', safe)
    return safe or "Libro"


def get_notes_path(book_title: str, documents_dir=None) -> Path:
    """Build the Markdown notes file path for a book title."""
    base = Path(documents_dir) if documents_dir else get_documents_dir()
    return base / f"{sanitize_book_title(book_title)}.md"


def format_note_timestamp(now: datetime = None, time_format: str = None) -> str:
    """Format dd/mm/yyyy hh:mm:ss, with am/pm when the 12h format is set."""
    now = now or datetime.now()
    fmt = time_format or getattr(config, "NOTES_TIME_FORMAT", "24h")
    pattern = "%d/%m/%Y %I:%M:%S %p" if str(fmt).lower() in _12H_PATTERNS else "%d/%m/%Y %H:%M:%S"
    return now.strftime(pattern)


def append_note(path, note_text: str, position_label: str = "", timestamp_str: str = None):
    """Append a timestamped note entry, creating the file header on first use."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = timestamp_str or format_note_timestamp()

    entry = f"- **[{ts}]**"
    if position_label:
        entry += f" _({position_label})_"
    entry += f": {note_text.strip()}"

    if not path.exists():
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# Notas — {path.stem}\n\n")

    with open(path, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

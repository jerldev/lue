"""Reading bookmarks (save points), stored in <Documents>/LUE as JSON.

One JSON file per book (<book>.bookmarks.json) inside a single LUE
folder that is created on first use and never duplicated. Each entry
keeps the reading position triple (chapter, paragraph, sentence) plus
a timestamp so the list window can show and jump back to it.
"""

import json
import logging
from pathlib import Path

from . import notes

BOOKMARKS_FOLDER = "LUE"


def get_documents_dir() -> Path:
    """Delegate to the notes module's Documents resolution (XDG-aware)."""
    return notes.get_documents_dir()


def get_bookmarks_dir(documents_dir=None) -> Path:
    """Resolve <Documents>/LUE, creating it on first use (idempotent)."""
    base = Path(documents_dir) if documents_dir else get_documents_dir()
    folder = base / BOOKMARKS_FOLDER
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def get_bookmarks_path(book_title: str, documents_dir=None) -> Path:
    """Build the JSON bookmarks file path for a book title."""
    safe = notes.sanitize_book_title(book_title)
    return get_bookmarks_dir(documents_dir) / f"{safe}.bookmarks.json"


def load_bookmarks(book_title: str, documents_dir=None) -> list:
    """Load the bookmark list for a book; empty list when absent."""
    path = get_bookmarks_path(book_title, documents_dir)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, OSError) as e:
        logging.warning(f"Could not load bookmarks for '{book_title}': {e}")
        return []


def add_bookmark(book_title: str, chapter_idx: int, paragraph_idx: int,
                 sentence_idx: int, documents_dir=None) -> dict:
    """Append a bookmark at the given position and persist the file."""
    entries = load_bookmarks(book_title, documents_dir)
    entry = {
        "id": (entries[-1]["id"] + 1) if entries else 1,
        "c": chapter_idx,
        "p": paragraph_idx,
        "s": sentence_idx,
        "timestamp": notes.format_note_timestamp(),
    }
    entries.append(entry)
    path = get_bookmarks_path(book_title, documents_dir)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logging.warning(f"Could not save bookmark for '{book_title}': {e}")
        raise
    return entry

"""Tests for the Markdown notes feature.

Notes are stored as one Markdown file per book in the system Documents
folder. Each appended note carries a timestamp (12h or 24h, configurable)
and a reading-position reference.
"""

import re
from datetime import datetime
from pathlib import Path

from lue import notes


class TestNotesPath:
    def test_notes_path_uses_injected_documents_dir(self, tmp_path):
        path = notes.get_notes_path("Mi Libro", documents_dir=tmp_path)
        assert path.parent == tmp_path
        assert path.suffix == ".md"
        assert path.stem == "Mi Libro"

    def test_notes_path_sanitizes_invalid_filename_chars(self, tmp_path):
        path = notes.get_notes_path('Mi Libro: cap 1/2 "especial"?', documents_dir=tmp_path)
        assert "/" not in path.name
        assert ":" not in path.name
        assert path.suffix == ".md"

    def test_notes_path_keeps_readable_spacing(self, tmp_path):
        path = notes.get_notes_path("Mi  Libro", documents_dir=tmp_path)
        assert path.name == "Mi Libro.md"

    def test_unusable_title_falls_back_to_generic_name(self, tmp_path):
        path = notes.get_notes_path("///", documents_dir=tmp_path)
        assert path.name.endswith(".md")
        assert len(path.stem) > 0

    def test_notes_path_blocks_path_traversal(self, tmp_path):
        for hostile in ("../evil", "/etc/passwd", "..", "a/b/c"):
            path = notes.get_notes_path(hostile, documents_dir=tmp_path)
            resolved = path.resolve()
            assert resolved.parent == tmp_path.resolve(), f"escaped for {hostile!r}"
            assert path.name.endswith(".md")


class TestNoteTimestamp:
    def test_24h_format(self):
        ts = notes.format_note_timestamp(datetime(2024, 3, 5, 14, 30, 5), "24h")
        assert ts == "05/03/2024 14:30:05"

    def test_12h_format_with_am_pm(self):
        ts = notes.format_note_timestamp(datetime(2024, 3, 2, 13, 30, 5), "12h")
        assert ts == "02/03/2024 01:30:05 PM"

    def test_default_comes_from_config(self, monkeypatch):
        monkeypatch.setattr(notes.config, "NOTES_TIME_FORMAT", "12h")
        ts = notes.format_note_timestamp(datetime(2024, 3, 2, 13, 30, 5))
        assert ts.endswith("PM")


class TestAppendNote:
    def test_first_note_creates_file_with_header(self, tmp_path):
        path = tmp_path / "Mi Libro.md"
        notes.append_note(path, "Primera nota", "cap 1, párrafo 2", "05/03/2024 14:30:05")
        content = path.read_text(encoding="utf-8")
        assert content.startswith("# Notas")
        assert "- **[05/03/2024 14:30:05]** _(cap 1, párrafo 2)_: Primera nota" in content

    def test_second_note_appends_with_timestamp(self, tmp_path):
        path = tmp_path / "Mi Libro.md"
        notes.append_note(path, "Primera", "cap 1, párrafo 1", "05/03/2024 14:30:05")
        notes.append_note(path, "Segunda", "cap 3, párrafo 9", "05/03/2024 15:31:06")
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("- **")]
        assert len(lines) == 2
        assert "Segunda" in lines[1]

    def test_note_text_is_stripped_and_single_entry(self, tmp_path):
        path = tmp_path / "Mi Libro.md"
        notes.append_note(path, "  texto con espacios  ", "", "05/03/2024 14:30:05")
        entries = [l for l in path.read_text(encoding="utf-8").splitlines() if l.startswith("- **")]
        assert len(entries) == 1
        assert entries[0].endswith(": texto con espacios")


class TestNoteShortcut:
    def _shortcuts(self, name):
        return __import__("json").loads((Path(__file__).parent.parent / "lue" / name).read_text(encoding="utf-8"))

    def test_default_layout_registers_note_key(self):
        assert self._shortcuts("keys_default.json")["display_controls"]["add_note"] == "N"

    def test_vim_layout_registers_note_key(self):
        assert self._shortcuts("keys_vim.json")["display_controls"]["add_note"] == "N"

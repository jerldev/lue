"""Bookmark (save point) tests: quick marks with d, list window with f,
stored as JSON per book inside <Documents>/LUE, jump restores position."""

import asyncio
import json

import pytest
from rich.console import Console

from lue import audio, bookmarks, ui
from lue.reader import Lue


def make_reader(tmp_path):
    reader = Lue.__new__(Lue)
    reader.book_title = "Mi Libro"
    reader.file_path = "/tmp/Mi Libro.pdf"
    reader.tts_model = None
    reader.console = Console(file=open("/dev/null", "w"))
    reader.is_paused = True
    reader.running = True
    reader.first_sentence_jump = False
    reader.auto_scroll_enabled = False
    reader.show_recent_menu = False
    reader.show_chapter_index = False
    reader.show_search = False
    reader.show_voice_menu = False
    reader.note_input_mode = False
    reader.search_input_mode = False
    reader.show_bookmark_menu = False
    reader.bookmark_menu_selection_idx = 0
    reader.bookmark_menu_scroll_offset = 0
    reader.bookmarks = []
    reader.chapter_idx = reader.ui_chapter_idx = 0
    reader.paragraph_idx = reader.ui_paragraph_idx = 0
    reader.sentence_idx = reader.ui_sentence_idx = 0
    reader.chapters = [[["frase uno"], ["frase dos"]]]
    reader.status_message = ""
    reader.status_message_until = 0.0
    reader.status_seconds = 2.5
    reader.pending_restart_task = None

    async def no_clear(seconds):
        pass

    reader._clear_status_after = no_clear
    reader._save_extended_progress = lambda **k: None

    def fake_scroll(c, p, s):
        pass

    reader._scroll_to_position_immediate = fake_scroll
    return reader


@pytest.fixture
def docs(tmp_path, monkeypatch):
    monkeypatch.setattr(bookmarks, "get_documents_dir", lambda: tmp_path)
    return tmp_path


@pytest.fixture
def display_calls(monkeypatch):
    calls = []

    async def fake_display(reader):
        calls.append(reader)

    monkeypatch.setattr(ui, "display_ui", fake_display)
    return calls


class TestKeymaps:
    def test_both_keymaps_register_bookmark_keys(self):
        for path in ("lue/keys_default.json", "lue/keys_vim.json"):
            with open(path) as f:
                shortcuts = json.load(f)
            assert shortcuts["display_controls"]["add_bookmark"] == "d"
            assert shortcuts["display_controls"]["toggle_bookmark_menu"] == "f"

    def test_bookmark_keys_free_in_both_keymaps(self):
        # d and f must not be assigned anywhere else in either keymap
        for path in ("lue/keys_default.json", "lue/keys_vim.json"):
            with open(path) as f:
                sections = json.load(f)
            assigned = []
            for section in sections.values():
                for value in section.values():
                    if isinstance(value, list):
                        assigned.extend(value)
                    elif isinstance(value, str):
                        assigned.append(value)
            for key in ("d", "f"):
                owners = [name for section in sections.values()
                          for name, value in section.items() if value == key]
                assert len(owners) == 1 and owners[0] in ("add_bookmark", "toggle_bookmark_menu"), \
                    f"{key} collision in {path}: {owners}"


class TestBookmarksModule:
    def test_creates_lue_folder_once(self, docs):
        d1 = bookmarks.get_bookmarks_dir()
        d2 = bookmarks.get_bookmarks_dir()
        assert d1 == d2 == docs / "LUE"
        assert d1.is_dir()
        assert [p.name for p in docs.iterdir()] == ["LUE"]

    def test_load_missing_bookmarks_returns_empty(self, docs):
        assert bookmarks.load_bookmarks("Libro Inexistente") == []

    def test_add_bookmark_roundtrip(self, docs):
        entry = bookmarks.add_bookmark("Mi Libro", 2, 3, 1)
        assert entry["c"] == 2 and entry["p"] == 3 and entry["s"] == 1
        assert entry["id"] == 1
        assert entry["timestamp"]
        entries = bookmarks.load_bookmarks("Mi Libro")
        assert len(entries) == 1
        assert entries[0]["id"] == 1

    def test_add_bookmark_appends_with_unique_ids(self, docs):
        first = bookmarks.add_bookmark("Mi Libro", 0, 0, 0)
        second = bookmarks.add_bookmark("Mi Libro", 1, 1, 1)
        assert second["id"] == first["id"] + 1
        assert len(bookmarks.load_bookmarks("Mi Libro")) == 2

    def test_books_are_isolated(self, docs):
        bookmarks.add_bookmark("Libro A", 0, 0, 0)
        bookmarks.add_bookmark("Libro B", 1, 1, 1)
        assert len(bookmarks.load_bookmarks("Libro A")) == 1
        assert len(bookmarks.load_bookmarks("Libro B")) == 1


class TestAddBookmarkHandler:
    def test_add_saves_current_position_and_status(self, docs, display_calls):
        reader = make_reader(docs.parent)
        reader.chapter_idx = reader.paragraph_idx = reader.sentence_idx = 2
        asyncio.run(reader._handle_add_bookmark())
        entries = bookmarks.load_bookmarks("Mi Libro")
        assert entries[0]["c"] == 2 and entries[0]["p"] == 2 and entries[0]["s"] == 2
        assert "Marca" in reader.status_message

    def test_add_second_mark_increments(self, docs, display_calls):
        reader = make_reader(docs.parent)
        asyncio.run(reader._handle_add_bookmark())
        asyncio.run(reader._handle_add_bookmark())
        assert len(bookmarks.load_bookmarks("Mi Libro")) == 2


class TestBookmarkMenu:
    def test_toggle_opens_pauses_and_loads(self, docs, display_calls, monkeypatch):
        reader = make_reader(docs.parent)
        reader.is_paused = False
        reader.tts_model = object()
        bookmarks.add_bookmark("Mi Libro", 1, 0, 0)
        monkeypatch.setattr(reader, "_save_extended_progress", lambda **k: None)

        async def fake_stop(r):
            pass

        monkeypatch.setattr(audio, "stop_and_clear_audio", fake_stop)

        async def scenario():
            await reader._handle_toggle_bookmark_menu()

        asyncio.run(scenario())
        assert reader.show_bookmark_menu is True
        assert reader.is_paused is True
        assert reader.show_recent_menu is False
        assert reader.show_chapter_index is False
        assert reader.show_voice_menu is False
        assert reader.bookmarks[0]["c"] == 1

    def test_navigation_and_enter_jumps(self, docs, display_calls, monkeypatch):
        reader = make_reader(docs.parent)
        reader.show_bookmark_menu = True
        reader.bookmarks = [
            {"id": 1, "c": 0, "p": 0, "s": 0, "timestamp": "x"},
            {"id": 2, "c": 1, "p": 1, "s": 0, "timestamp": "y"},
        ]
        jumped = []

        async def fake_jump(entry):
            jumped.append(entry)

        monkeypatch.setattr(reader, "_jump_to_bookmark", fake_jump)

        async def scenario():
            assert await reader._handle_bookmark_menu_command("next_sentence") is True
            assert reader.bookmark_menu_selection_idx == 1
            assert await reader._handle_bookmark_menu_command("select_menu_item") is True
            assert jumped == [reader.bookmarks[1]]
            assert reader.show_bookmark_menu is False

        asyncio.run(scenario())

    def test_close_command(self, docs, display_calls):
        reader = make_reader(docs.parent)
        reader.show_bookmark_menu = True

        async def scenario():
            assert await reader._handle_bookmark_menu_command("toggle_bookmark_menu") is True
            assert reader.show_bookmark_menu is False

        asyncio.run(scenario())


class TestJumpToBookmark:
    def test_jump_restores_position(self, docs, display_calls, monkeypatch):
        reader = make_reader(docs.parent)
        reader.chapters = [[["frase uno"]], [["frase dos"]]]  # 2 chapters
        scrolled = []
        saved = []

        def fake_scroll(c, p, s):
            scrolled.append((c, p, s))

        reader._scroll_to_position_immediate = fake_scroll
        reader._save_extended_progress = lambda **k: saved.append(k)

        async def fake_stop(r):
            pass

        monkeypatch.setattr(audio, "stop_and_clear_audio", fake_stop)

        async def fake_restart():
            pass

        reader._restart_audio_after_navigation = fake_restart

        async def scenario():
            await reader._jump_to_bookmark({"id": 1, "c": 1, "p": 1, "s": 0})

        asyncio.run(scenario())
        assert reader.chapter_idx == reader.ui_chapter_idx == 1
        assert reader.paragraph_idx == reader.ui_paragraph_idx == 1
        assert reader.sentence_idx == reader.ui_sentence_idx == 0
        assert scrolled == [(1, 1, 0)]
        assert reader.auto_scroll_enabled is False
        assert reader.show_bookmark_menu is False
        assert saved  # progress persisted

    def test_jump_ignores_out_of_bounds(self, docs, display_calls):
        reader = make_reader(docs.parent)

        async def scenario():
            await reader._jump_to_bookmark({"id": 1, "c": 99, "p": 0, "s": 0})

        asyncio.run(scenario())
        assert reader.chapter_idx == 0  # unchanged


class TestOverlayRenderSmoke:
    def test_renders_empty_and_populated(self, display_calls):
        from lue.ui import render_bookmarks_overlay

        reader = make_reader(None)
        panel, w, h = render_bookmarks_overlay(reader, 100, 30)
        assert panel is not None and w > 0 and h > 0

        reader.bookmarks = [{"id": 1, "c": 0, "p": 1, "s": 0, "timestamp": "17/11/2026 10:00:00"}]
        panel, w, h = render_bookmarks_overlay(reader, 100, 30)
        assert panel is not None

    def test_renders_selection_marker(self, display_calls):
        from lue.ui import render_bookmarks_overlay

        reader = make_reader(None)
        reader.bookmarks = [{"id": 1, "c": 0, "p": 0, "s": 0, "timestamp": "t"}]
        reader.bookmark_menu_selection_idx = 0
        panel, _, _ = render_bookmarks_overlay(reader, 100, 30)
        assert panel is not None

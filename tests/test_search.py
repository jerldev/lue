"""Tests for the in-book text search feature.

The matching function operates on the parsed chapter structure
(chapters[chapter][paragraph] = text) and returns sentence-level matches,
which the reader uses to jump to the found text. The keyboard shortcut
files must register the search command.
"""

import json
from pathlib import Path

from rich.console import Console

from lue import ui
from lue.content_parser import find_search_matches
from lue.reader import Lue

LUE_DIR = Path(__file__).parent.parent / "lue"


def load_shortcuts(name):
    return json.loads((LUE_DIR / name).read_text(encoding="utf-8"))


def make_chapters():
    return [
        [
            "Primera oración del libro. Y una segunda oración aquí.",
            "Un párrafo con la palabra murciélago al final.",
        ],
        [
            "Otro capítulo sin coincidencias relevantes.",
            "La casa verde y la MURCIÉLAGO azul. Fin del párrafo.",
        ],
    ]


class TestFindSearchMatches:
    def test_finds_case_insensitive_matches(self):
        matches = find_search_matches(make_chapters(), "murciélago")
        assert len(matches) == 2

    def test_matches_are_sentence_level(self):
        chapters = [["Primera oración. Segunda menciona aguja. Tercera oración."]]
        matches = find_search_matches(chapters, "aguja")
        assert len(matches) == 1
        c, p, s, text = matches[0]
        assert (c, p, s) == (0, 0, 1)
        assert "aguja" in text

    def test_no_matches_returns_empty_list(self):
        assert find_search_matches(make_chapters(), "zorro ártico") == []

    def test_empty_query_returns_empty_list(self):
        assert find_search_matches(make_chapters(), "") == []
        assert find_search_matches(make_chapters(), "   ") == []

    def test_results_in_reading_order(self):
        matches = find_search_matches(make_chapters(), "murciélago")
        assert matches[0][:3] == (0, 1, 0)
        assert matches[1][:3] == (1, 1, 0)

    def test_result_limit_is_respected(self):
        chapters = [["palabra palabra palabra palabra. ".split(". ")[0] * 1]]
        paragraph = " ".join([f"palabra{i} blanca." for i in range(30)])
        matches = find_search_matches([paragraph.split()], "blanca", limit=10)
        assert len(matches) == 10


class TestSearchShortcut:
    def test_default_layout_registers_search_key(self):
        shortcuts = load_shortcuts("keys_default.json")
        assert shortcuts["display_controls"]["search"] == "/"

    def test_vim_layout_registers_search_key(self):
        shortcuts = load_shortcuts("keys_vim.json")
        assert shortcuts["display_controls"]["search"] == "/"

    def test_shortcut_files_stay_valid_json(self):
        for name in ("keys_default.json", "keys_vim.json"):
            assert isinstance(load_shortcuts(name), dict)


class SearchResultsStub:
    """Reader stub in the search results view with a markup-looking query."""

    def __init__(self, query="[/]"):
        self.search_input_mode = False
        self.search_query = query
        self.search_matches = [(0, 0, 0, "párrafo con la búsqueda")]
        self.search_selection_idx = 0
        self.search_scroll_offset = 0


def render_panel_text(panel):
    console = Console()
    with console.capture() as capture:
        console.print(panel)
    return capture.get()


class TestSearchOverlayTitleIsMarkupSafe:
    def test_results_title_renders_markup_like_query_literally(self):
        panel, _, _ = ui.render_search_overlay(SearchResultsStub(), 100, 40)
        assert "[/]" in render_panel_text(panel)

    def test_zero_matches_title_renders_markup_like_query_literally(self):
        stub = SearchResultsStub()
        stub.search_matches = []
        panel, _, _ = ui.render_search_overlay(stub, 100, 40)
        assert "[/]" in render_panel_text(panel)


class TestEmptySearchSubmitCloses:
    def test_empty_submit_closes_overlay(self):
        reader = Lue.__new__(Lue)
        reader.search_query = "   "
        reader.show_search = True
        reader.search_input_mode = True
        Lue._handle_search_submit(reader)
        assert reader.show_search is False
        assert reader.search_input_mode is False

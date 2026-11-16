"""Tests for the in-book text search feature.

The matching function operates on the parsed chapter structure
(chapters[chapter][paragraph] = text) and returns sentence-level matches,
which the reader uses to jump to the found text. The keyboard shortcut
files must register the search command.
"""

import json
from pathlib import Path

from lue.content_parser import find_search_matches

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

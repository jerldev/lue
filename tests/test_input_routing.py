"""Input routing regression tests for the search and note input modes.

These use a minimal reader stub: _process_normal_key only touches the
input-mode flags, running, command_received_event, and post_command.
"""

import threading

from lue import input_handler


class StubReader:
    def __init__(self):
        self.note_input_mode = False
        self.show_search = False
        self.search_input_mode = False
        self.running = True
        self.command_received_event = threading.Event()
        self.commands = []

    def post_command(self, cmd):
        self.commands.append(cmd)


class TestInputModeGuardsTakePrecedence:
    def test_note_mode_swallows_shortcut_keys_as_text(self):
        reader = StubReader()
        reader.note_input_mode = True
        input_handler._process_normal_key(reader, "/")
        assert reader.commands[-1] == ("note_char", "/")
        assert reader.running is True

    def test_search_typing_mode_swallows_quit_key_as_text(self):
        reader = StubReader()
        reader.show_search = True
        reader.search_input_mode = True
        input_handler._process_normal_key(reader, "q")
        assert reader.commands[-1] == ("search_char", "q")
        assert reader.running is True

    def test_search_enter_posts_search_submit(self):
        reader = StubReader()
        reader.show_search = True
        reader.search_input_mode = True
        input_handler._process_normal_key(reader, "\r")
        assert reader.commands[-1] == "search_submit"

    def test_note_enter_posts_note_save(self):
        reader = StubReader()
        reader.note_input_mode = True
        input_handler._process_normal_key(reader, "\r")
        assert reader.commands[-1] == "note_save"


class TestQuitWithSearchResultsOpen:
    def test_quit_key_still_quits_in_results_view(self):
        reader = StubReader()
        reader.show_search = True
        reader.search_input_mode = False
        input_handler._process_normal_key(reader, "q")
        assert reader.running is False
        assert reader.commands == []

"""Mouse drag selection and clipboard copy tests.

The mouse parser must defer the legacy click-jump until release, drive a
drag selection with motion events, and auto-copy on release. The copy
chain tries native clipboard tools first (verifiable) and falls back to
OSC 52, which terminals and multiplexers that forward it can honor.
"""

import asyncio
import base64

from lue import audio, input_handler
from lue import reader as reader_module
from lue.reader import Lue


def make_reader():
    reader = Lue.__new__(Lue)
    reader.pending_commands = []
    reader.loop = None
    reader.selection_press_screen = None
    reader.selection_active = False
    reader.selection_start = None
    reader.selection_end = None
    reader.status_message = ""
    reader.status_message_until = 0.0
    reader.status_seconds = 2.5

    async def no_clear(seconds):
        pass

    reader._clear_status_after = no_clear
    return reader


class MouseReaderStub:
    """Reader stub exposing what _process_mouse_sequence touches."""

    def __init__(self):
        self.show_chapter_index = False
        self.note_input_mode = False
        self.show_search = False
        self.auto_scroll_enabled = True
        self.selection_press_screen = None
        self.commands = []

    def post_command(self, cmd):
        self.commands.append(cmd)

    def _is_click_on_subtitle(self, x, y):
        return False

    def _is_click_on_progress_bar(self, x, y):
        return False

    def _is_click_on_text(self, x, y):
        return True


class TestMouseParserSelectionFlow:
    def test_press_on_text_posts_selection_press_and_defers_kill(self, monkeypatch):
        reader = MouseReaderStub()

        def fail_kill(r):
            raise AssertionError("audio must not be killed on press")

        monkeypatch.setattr(audio, "kill_audio_immediately", fail_kill)
        input_handler._process_mouse_sequence(reader, "\x1b[<0;10;5M")
        assert reader.commands == [("selection_press", (10, 5))]

    def test_press_blocked_while_typing_note(self):
        reader = MouseReaderStub()
        reader.note_input_mode = True
        input_handler._process_mouse_sequence(reader, "\x1b[<0;10;5M")
        assert reader.commands == []

    def test_drag_motion_posts_move_only_while_pressed(self):
        reader = MouseReaderStub()
        input_handler._process_mouse_sequence(reader, "\x1b[<32;12;6M")
        assert reader.commands == []
        reader.selection_press_screen = (10, 5)
        input_handler._process_mouse_sequence(reader, "\x1b[<32;12;6M")
        assert reader.commands == [("selection_move", (12, 6))]

    def test_release_posts_selection_release(self):
        reader = MouseReaderStub()
        input_handler._process_mouse_sequence(reader, "\x1b[<0;10;5m")
        assert reader.commands == [("selection_release", (10, 5))]

    def test_wheel_scrolling_unaffected(self):
        reader = MouseReaderStub()
        input_handler._process_mouse_sequence(reader, "\x1b[<64;10;5M")
        assert reader.commands == ["wheel_scroll_up"]
        assert reader.auto_scroll_enabled is False


class TestSelectionReleaseHandler:
    def test_plain_click_keeps_legacy_jump(self, monkeypatch):
        reader = make_reader()
        reader.selection_press_screen = (10, 5)
        killed = []
        monkeypatch.setattr(audio, "kill_audio_immediately", lambda r: killed.append(r))
        asyncio.run(Lue._handle_selection_release(reader, (10, 5)))
        assert reader.pending_commands == [("click_jump", (10, 5))]
        assert killed == [reader]
        assert reader.selection_press_screen is None

    def test_drag_release_copies_and_clears_selection(self, monkeypatch):
        reader = make_reader()
        reader.selection_press_screen = (10, 5)
        reader.selection_active = True
        reader.selection_start = (0, 0)
        reader.selection_end = (1, 5)
        copied = []
        monkeypatch.setattr(Lue, "_get_selected_text", lambda self: "texto elegido")
        monkeypatch.setattr(Lue, "_copy_to_clipboard", lambda self, text: copied.append(text) or True)
        asyncio.run(Lue._handle_selection_release(reader, (12, 6)))
        assert copied == ["texto elegido"]
        assert reader.selection_active is False
        assert "Copiado" in reader.status_message

    def test_failed_copy_keeps_selection_for_retry(self, monkeypatch):
        reader = make_reader()
        reader.selection_active = True
        reader.selection_start = (0, 0)
        reader.selection_end = (1, 5)
        monkeypatch.setattr(Lue, "_get_selected_text", lambda self: "texto")
        monkeypatch.setattr(Lue, "_copy_to_clipboard", lambda self, text: False)
        asyncio.run(Lue._handle_selection_release(reader, (12, 6)))
        assert reader.selection_active is True
        assert "No se pudo" in reader.status_message


class TestCopyChain:
    def test_native_tool_used_first(self, monkeypatch, capsys):
        import shutil

        reader = make_reader()
        monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
        monkeypatch.delenv("DISPLAY", raising=False)
        monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/wl-copy")
        calls = []

        class FakeProcess:
            returncode = 0

            def communicate(self, input=None, timeout=None):
                calls.append((input, timeout))

        monkeypatch.setattr(reader_module.subprocess, "Popen", lambda argv, **k: calls.append(argv) or FakeProcess())
        assert reader._copy_to_clipboard("hola") is True
        assert calls[0] == ["wl-copy"]
        assert calls[1] == ("hola", 2)
        assert "\x1b]52;c;" not in capsys.readouterr().out

    def test_osc52_fallback_when_no_tools(self, monkeypatch, capsys):
        import shutil

        reader = make_reader()
        monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
        monkeypatch.delenv("DISPLAY", raising=False)
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.setattr(shutil, "which", lambda name: None)
        assert reader._copy_to_clipboard("hola") is True
        out = capsys.readouterr().out
        expected = base64.b64encode("hola".encode()).decode()
        assert f"\x1b]52;c;{expected}\x07" in out

    def test_osc52_wraps_inside_tmux(self, monkeypatch, capsys):
        import shutil

        reader = make_reader()
        monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
        monkeypatch.delenv("DISPLAY", raising=False)
        monkeypatch.setenv("TMUX", "/tmp/tmux-0/default,123,0")
        monkeypatch.setattr(shutil, "which", lambda name: None)
        assert reader._copy_to_clipboard("hola") is True
        out = capsys.readouterr().out
        assert out.startswith("\x1bPtmux;")
        assert out.endswith("\x1b\\")

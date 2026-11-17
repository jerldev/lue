"""Voice picker tests: Spanish default voice, language/voice catalog,
menu navigation, and hot voice swap used for reading."""

import asyncio
import json

import pytest
from rich.console import Console

from lue import audio, config, ui
from lue.reader import Lue
from lue.tts.edge_tts import EdgeTTS, format_voice_label, group_edge_voices
from lue.tts.kokoro_tts import kokoro_voice_catalog

EDGE_VOICES_FIXTURE = [
    {"Locale": "en-US", "ShortName": "en-US-JennyNeural", "Gender": "Female",
     "FriendlyName": "Microsoft Jenny Online (Natural) - English (United States)"},
    {"Locale": "es-CO", "ShortName": "es-CO-SalomeNeural", "Gender": "Female",
     "FriendlyName": "Microsoft Salome Online (Natural) - Spanish (Colombia)"},
    {"Locale": "es-CO", "ShortName": "es-CO-GonzaloNeural", "Gender": "Male",
     "FriendlyName": "Microsoft Gonzalo Online (Natural) - Spanish (Colombia)"},
    {"Locale": "es-ES", "ShortName": "es-ES-ElviraNeural", "Gender": "Female",
     "FriendlyName": "Microsoft Elvira Online (Natural) - Spanish (Spain)"},
]


def make_reader():
    reader = Lue.__new__(Lue)
    reader.tts_model = None
    reader.console = Console(file=open("/dev/null", "w"))
    reader.is_paused = False
    reader.running = True
    reader.show_recent_menu = False
    reader.show_chapter_index = False
    reader.show_search = False
    reader.note_input_mode = False
    reader.search_input_mode = False
    # Voice menu state
    reader.show_voice_menu = False
    reader.voice_menu_level = "language"
    reader.voice_menu_selection_idx = 0
    reader.voice_menu_scroll_offset = 0
    reader.voice_menu_languages = []
    reader.voice_menu_voices = []
    reader.voice_menu_language = None
    reader.voice_menu_loading = False
    reader.voice_menu_error = ""
    reader.voice_menu_was_playing = False
    reader._voice_menu_catalog = {}
    # Status message infra (from selection feature)
    reader.status_message = ""
    reader.status_message_until = 0.0
    reader.status_seconds = 2.5

    async def no_clear(seconds):
        pass

    reader._clear_status_after = no_clear
    reader._save_extended_progress = lambda: None

    async def fake_display(r):
        pass

    reader._fake_display = fake_display
    return reader


class StubTTS:
    name = "edge"

    def __init__(self, grouped):
        self.voice = "en-US-JennyNeural"
        self._grouped = grouped

    async def list_voices(self):
        return self._grouped


@pytest.fixture
def display_calls(monkeypatch):
    calls = []

    async def fake_display(reader):
        calls.append(reader)

    monkeypatch.setattr(ui, "display_ui", fake_display)
    return calls


class TestDefaultVoice:
    def test_config_default_edge_voice_is_salome(self):
        assert config.TTS_VOICES["edge"] == "es-CO-SalomeNeural"

    def test_edgetts_defaults_to_salome(self):
        tts = EdgeTTS(Console(file=open("/dev/null", "w")))
        assert tts.voice == "es-CO-SalomeNeural"

    def test_keymaps_register_voice_menu_shortcut(self):
        for path in ("lue/keys_default.json", "lue/keys_vim.json"):
            with open(path) as f:
                shortcuts = json.load(f)
            assert shortcuts["display_controls"]["toggle_voice_menu"] == "o"


class TestVoiceCatalog:
    def test_format_voice_label_strips_neural(self):
        voice = EDGE_VOICES_FIXTURE[1]
        assert format_voice_label(voice) == "Salome (Female)"

    def test_group_edge_voices_by_language(self):
        grouped = group_edge_voices(EDGE_VOICES_FIXTURE)
        assert set(grouped) == {"en", "es"}
        ids = [voice_id for voice_id, _ in grouped["es"]]
        assert ids == sorted(ids)
        assert ("es-CO-SalomeNeural", "Salome (Female) · es-CO") in grouped["es"]
        assert ("en-US-JennyNeural", "Jenny (Female) · en-US") in grouped["en"]

    def test_group_edge_voices_empty(self):
        assert group_edge_voices([]) == {}

    def test_kokoro_catalog_groups_languages(self):
        catalog = kokoro_voice_catalog()
        assert ("af_heart", "Heart (Female)") in catalog["en"]
        assert any(voice_id.startswith("ef_") for voice_id, _ in catalog["es"])

    def test_edgetts_list_voices_uses_library(self):
        import types

        tts = EdgeTTS(Console(file=open("/dev/null", "w")))
        fake_module = types.SimpleNamespace(
            list_voices=lambda: asyncio.sleep(0, result=EDGE_VOICES_FIXTURE)
        )
        tts.edge_tts = fake_module
        tts.initialized = True
        grouped = asyncio.run(tts.list_voices())
        assert set(grouped) == {"en", "es"}

    def test_edgetts_list_voices_offline_returns_empty(self, monkeypatch):
        import sys

        tts = EdgeTTS(Console(file=open("/dev/null", "w")))
        tts.edge_tts = None
        monkeypatch.setitem(sys.modules, "edge_tts", None)  # forces ImportError
        assert asyncio.run(tts.list_voices()) == {}


class TestVoiceMenu:
    def test_toggle_opens_pauses_and_loads_languages(self, display_calls, monkeypatch):
        reader = make_reader()
        reader.tts_model = StubTTS({"en": [], "es": []})
        saved = []
        monkeypatch.setattr(reader, "_save_extended_progress", lambda: saved.append(True))

        async def fake_stop(r):
            pass

        monkeypatch.setattr(audio, "stop_and_clear_audio", fake_stop)

        async def scenario():
            await reader._handle_toggle_voice_menu()
            assert reader.show_voice_menu is True
            assert reader.voice_menu_was_playing is True
            assert reader.is_paused is True
            assert reader.voice_menu_loading is True
            await asyncio.sleep(0.01)
            assert reader.voice_menu_languages == ["en", "es"]
            assert reader.voice_menu_loading is False

        asyncio.run(scenario())
        assert len(display_calls) >= 1

    def test_toggle_without_tts_shows_error(self, display_calls, monkeypatch):
        reader = make_reader()

        async def fake_stop(r):
            pass

        monkeypatch.setattr(audio, "stop_and_clear_audio", fake_stop)

        async def scenario():
            await reader._handle_toggle_voice_menu()
            assert reader.voice_menu_error != ""

        asyncio.run(scenario())

    def test_navigation_enter_and_apply(self, display_calls, monkeypatch):
        reader = make_reader()
        reader.voice_menu_languages = ["en", "es"]
        reader._voice_menu_catalog = {"en": [("en-US-JennyNeural", "Jenny (Female) · en-US")],
                                      "es": [("es-CO-SalomeNeural", "Salome (Female) · es-CO")]}
        applied = []

        async def fake_apply(voice_id):
            applied.append(voice_id)

        monkeypatch.setattr(reader, "_apply_voice_selection", fake_apply)

        async def scenario():
            reader.show_voice_menu = True
            assert await reader._handle_voice_menu_command("next_sentence") is True
            assert reader.voice_menu_selection_idx == 1
            # Enter on a language opens its voice list
            assert await reader._handle_voice_menu_command("select_menu_item") is True
            assert reader.voice_menu_level == "voice"
            assert reader.voice_menu_language == "es"
            assert reader.voice_menu_voices == [("es-CO-SalomeNeural", "Salome (Female) · es-CO")]
            # Enter on a voice applies it and closes the menu
            assert await reader._handle_voice_menu_command("select_menu_item") is True
            assert applied == ["es-CO-SalomeNeural"]
            assert reader.show_voice_menu is False

        asyncio.run(scenario())

    def test_selection_wraps_around(self, display_calls):
        reader = make_reader()
        reader.show_voice_menu = True
        reader.voice_menu_languages = ["en", "es"]

        async def scenario():
            await reader._handle_voice_menu_command("prev_sentence")
            assert reader.voice_menu_selection_idx == 1

        asyncio.run(scenario())

    def test_close_command(self, display_calls):
        reader = make_reader()
        reader.show_voice_menu = True

        async def scenario():
            assert await reader._handle_voice_menu_command("toggle_voice_menu") is True
            assert reader.show_voice_menu is False

        asyncio.run(scenario())


class TestApplyVoiceSelection:
    def test_sets_voice_and_restarts_reading(self, display_calls, monkeypatch):
        reader = make_reader()
        model = StubTTS({})
        reader.tts_model = model
        reader.voice_menu_was_playing = True
        reader.is_paused = True
        restarts = []

        async def fake_restart():
            restarts.append(True)

        monkeypatch.setattr(reader, "_restart_audio_after_navigation", fake_restart)

        asyncio.run(reader._apply_voice_selection("es-CO-SalomeNeural"))
        assert model.voice == "es-CO-SalomeNeural"
        assert restarts == [True]
        assert reader.is_paused is False
        assert "Voz" in reader.status_message

    def test_paused_reader_stays_paused(self, display_calls, monkeypatch):
        reader = make_reader()
        model = StubTTS({})
        reader.tts_model = model
        reader.voice_menu_was_playing = False
        reader.is_paused = True
        restarts = []

        async def fake_restart():
            restarts.append(True)

        monkeypatch.setattr(reader, "_restart_audio_after_navigation", fake_restart)

        asyncio.run(reader._apply_voice_selection("en-US-JennyNeural"))
        assert model.voice == "en-US-JennyNeural"
        assert restarts == []
        assert reader.is_paused is True


class TestOverlayRenderSmoke:
    def test_renders_at_both_levels(self, display_calls):
        from lue.ui import render_voice_menu_overlay

        reader = make_reader()
        reader.voice_menu_languages = ["en", "es"]
        reader.tts_model = StubTTS({})
        panel, w, h = render_voice_menu_overlay(reader, 100, 30)
        assert panel is not None and w > 0 and h > 0

        reader.voice_menu_level = "voice"
        reader.voice_menu_language = "es"
        reader.voice_menu_voices = [("es-CO-SalomeNeural", "Salome (Female)")]
        panel, w, h = render_voice_menu_overlay(reader, 100, 30)
        assert panel is not None

    def test_renders_loading_and_error_states(self, display_calls):
        from lue.ui import render_voice_menu_overlay

        reader = make_reader()
        reader.voice_menu_loading = True
        panel, _, _ = render_voice_menu_overlay(reader, 100, 30)
        assert panel is not None

        reader.voice_menu_loading = False
        reader.voice_menu_error = "No hay voces disponibles"
        panel, _, _ = render_voice_menu_overlay(reader, 100, 30)
        assert panel is not None

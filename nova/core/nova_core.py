"""
NOVA Core (Android build).

Plays exactly the same role as nova_desktop/nova/core/nova_core.py: the
single source of truth for "what is NOVA doing right now", plus two
small forward-looking registries (memory, plugins) that do nothing yet
but give future features a place to live without another refactor:

    Speech-to-Text  -\\
    AI Chat           |
    Camera / CV        >---  NOVA Bridge  --->  NOVA Core  ---> UI (robot + chat)
    Face Tracking     |                              |
    Plugins          -/                        memory / plugins

NOVA Core never touches Kivy widgets or canvas drawing -- it only knows
about *state* and *intent*. Everything visual lives in nova/ui/. This
is what lets a real AI Chat backend, Memory, Camera, Computer Vision,
Face Tracking, or a Plugin System be added later by talking to this
class, without ever touching the robot renderer.

Built on Kivy's EventDispatcher (instead of PyQt's pyqtSignal, which
doesn't exist here) so the rest of the app can just do
``core.bind(on_state_changed=...)`` the same way the Windows UI does
``core.state_changed.connect(...)``.
"""

from kivy.event import EventDispatcher

from ..state import NovaState, StateMachine


class NovaCore(EventDispatcher):
    __events__ = ("on_state_changed", "on_speak_requested", "on_quit_requested")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state_machine = StateMachine()
        self.state_machine.add_listener(self._handle_state_changed)

        # Placeholders for future capabilities -- plain dict/list so a
        # real Memory or Plugin system can replace the internals later
        # without changing this class's public API.
        self.memory: dict = {}
        self.plugins: list = []

    # ---- state ---------------------------------------------------------
    @property
    def state(self) -> NovaState:
        return self.state_machine.state

    def is_busy(self) -> bool:
        return self.state_machine.is_busy()

    def request_state(self, new_state: NovaState, force: bool = False) -> None:
        self.state_machine.set_state(new_state, force=force)

    def _handle_state_changed(self, old_state, new_state) -> None:
        self.dispatch("on_state_changed", old_state, new_state)

    # ---- speech / output -------------------------------------------------
    def say(self, text: str) -> None:
        """Any engine (voice, typed chat, future AI backend, ...) reports
        outgoing speech here. The App is responsible for moving NOVA into
        SPEAKING and actually calling the TTS service -- see main.py."""
        self.dispatch("on_speak_requested", text)

    # ---- lifecycle -------------------------------------------------------
    def request_quit(self) -> None:
        self.dispatch("on_quit_requested")

    # ---- default (no-op) event handlers -----------------------------------
    def on_state_changed(self, old_state, new_state):
        pass

    def on_speak_requested(self, text):
        pass

    def on_quit_requested(self):
        pass

    # ---- plugin system (scaffold) ----------------------------------------
    def register_plugin(self, plugin) -> None:
        """Future plugin system entry point. A plugin is any object the
        caller wants tracked; NOVA Core does not impose an interface yet."""
        self.plugins.append(plugin)

    # ---- memory (scaffold) -------------------------------------------------
    def remember(self, key: str, value) -> None:
        self.memory[key] = value

    def recall(self, key: str, default=None):
        return self.memory.get(key, default)

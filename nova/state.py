"""
NOVA's state machine (Android build).

Deliberately plain Python (no Kivy import here) -- exactly the same
spirit as the Windows version's nova/state.py, which keeps the state
machine separate from both the voice engine and the renderer so new
states or new triggers (camera, face tracking, plugins, ...) can be
added later without touching drawing or movement code.

v1 ships the four states the phone UI actually needs. The
_PROTECTED_STATES / force pattern is kept identical to the Windows
version on purpose: it's what lets a background trigger (e.g. a future
"NOVA wanders back to idle after a timeout" feature) avoid interrupting
NOVA while she's actively listening/thinking/speaking, while an
explicit `force=True` (used by the voice/chat pipeline itself) always
wins.
"""

from enum import Enum, auto


class NovaState(Enum):
    IDLE = auto()
    LISTENING = auto()
    THINKING = auto()
    SPEAKING = auto()


class StateMachine:
    """Plain observer-based state machine (no UI framework dependency).

    Register a listener with add_listener(callback); callback is called
    as callback(old_state, new_state) whenever the state actually changes.
    """

    _PROTECTED_STATES = {NovaState.LISTENING, NovaState.THINKING, NovaState.SPEAKING}
    _NON_INTERRUPTING_TARGETS = {NovaState.IDLE}

    def __init__(self, initial: NovaState = NovaState.IDLE):
        self._state = initial
        self._listeners = []

    @property
    def state(self) -> NovaState:
        return self._state

    def is_busy(self) -> bool:
        return self._state in self._PROTECTED_STATES

    def add_listener(self, callback) -> None:
        self._listeners.append(callback)

    def set_state(self, new_state: NovaState, force: bool = False) -> None:
        if new_state == self._state:
            return

        if not force and self._state in self._PROTECTED_STATES and new_state in self._NON_INTERRUPTING_TARGETS:
            # Ignore background/idle triggers while NOVA is actively
            # listening, thinking, or speaking -- same rule as Windows.
            return

        old_state = self._state
        self._state = new_state
        for callback in list(self._listeners):
            callback(old_state, new_state)

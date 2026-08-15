"""
NOVA Bridge (Android build).

Same role as nova_desktop/nova/core/bridge.py: translates
engine-specific callbacks (the STT service today; AI chat, computer
vision, face tracking tomorrow) into NOVA Core calls. This is the only
piece that needs to know about a given engine's callback names --
NOVA Core and the UI never do.

Adding a new input source later is meant to look like:

    bridge.attach_vision_engine(vision_engine)

with a small ``attach_*`` method here, exactly like
``attach_stt_service`` below does for the existing STTService.
"""

from ..state import NovaState


class NovaBridge:
    def __init__(self, core):
        self.core = core

    def attach_stt_service(self, stt) -> None:
        """Wire an STTService (nova/voice/stt_service.py) into NOVA Core."""
        stt.on_listening = lambda: self.core.request_state(NovaState.LISTENING, force=True)
        stt.on_result = self._on_stt_result
        stt.on_error = self._on_stt_error

    def _on_stt_result(self, text: str) -> None:
        self.core.request_state(NovaState.THINKING, force=True)
        # The actual command dispatch / chat reply is handled by the App
        # (main.py), which owns the chat log UI. The bridge's job stops
        # at "NOVA now knows a THINKING cycle should start".
        self._pending_text = text
        if self.on_recognized:
            self.on_recognized(text)

    def _on_stt_error(self, message: str) -> None:
        self.core.request_state(NovaState.IDLE, force=True)
        if self.on_error:
            self.on_error(message)

    # The App assigns these after construction, same pattern as the
    # STTService's own on_listening/on_result/on_error callbacks.
    on_recognized = None
    on_error = None

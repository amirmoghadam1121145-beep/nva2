"""
NOVA Android -- entry point.

Same layered wiring idea as the Windows version's main.py:

    STTService  --(callbacks)-->  NovaBridge  -->  NovaCore  --(events)-->  UI
                                                        ^
                                            commands.py / typed chat

Run for local logic testing on a laptop (no phone/APK needed):
    python main.py
(falls back to console input + pyttsx3/print, see nova/voice/*_service.py)

Build into an installable APK: see README.md.
"""

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.core.window import Window

from nova import config
from nova.core.nova_core import NovaCore
from nova.core.bridge import NovaBridge
from nova.state import NovaState
from nova import commands
from nova.voice.tts_service import TTSService
from nova.voice.stt_service import STTService
from nova.ui.robot_widget import RobotWidget  # noqa: F401 -- used by KV via Factory


KV = """
<NovaRoot>:
    orientation: "vertical"
    canvas.before:
        Color:
            rgba: 0.0196, 0.0431, 0.0863, 1
        Rectangle:
            pos: self.pos
            size: self.size

    RobotWidget:
        id: robot
        size_hint_y: 0.46

    Label:
        id: status_label
        text: "IDLE"
        size_hint_y: 0.05
        color: 0.56, 0.86, 0.97, 1
        font_size: "16sp"
        bold: True
        halign: "center"

    ScrollView:
        size_hint_y: 0.27
        do_scroll_x: False
        Label:
            id: chat_label
            text: "NOVA: Hello. I am NOVA."
            size_hint_y: None
            height: max(self.texture_size[1], 1)
            text_size: self.width - 24, None
            color: 0.9, 0.98, 1, 1
            padding: 12, 10
            valign: "top"
            markup: False

    BoxLayout:
        size_hint_y: 0.09
        padding: 12, 4
        spacing: 8
        TextInput:
            id: chat_input
            hint_text: "Type a command or message..."
            multiline: False
            size_hint_x: 0.72
            background_color: 0.06, 0.12, 0.2, 1
            foreground_color: 0.9, 0.98, 1, 1
            cursor_color: 0.4, 0.9, 1, 1
            on_text_validate: app.on_text_submit()
        Button:
            text: "Send"
            size_hint_x: 0.28
            background_normal: ""
            background_color: 0.11, 0.29, 0.35, 1
            on_release: app.on_text_submit()

    Button:
        id: mic_button
        text: "TAP TO SPEAK"
        size_hint_y: 0.13
        font_size: "18sp"
        bold: True
        background_normal: ""
        background_color: 0, 0.6, 0.7, 1
        on_release: app.on_mic_pressed()
"""


class NovaRoot(BoxLayout):
    pass


class NovaApp(App):
    title = config.APP_TITLE

    def build(self):
        Builder.load_string(KV)
        Window.clearcolor = (0.0196, 0.0431, 0.0863, 1)

        self.core = NovaCore()
        self.bridge = NovaBridge(self.core)

        self.tts = TTSService()
        self.stt = STTService()
        self.bridge.attach_stt_service(self.stt)
        self.bridge.on_recognized = self._on_recognized
        self.bridge.on_error = self._on_stt_error

        self.core.bind(on_state_changed=self._on_state_changed)
        self.core.bind(on_speak_requested=self._on_speak_requested)
        self.core.bind(on_quit_requested=self._on_quit_requested)

        self.root_widget = NovaRoot()
        Clock.schedule_once(self._greet, 0.6)
        return self.root_widget

    def _greet(self, dt):
        self.core.say("Hello. I am NOVA. Tap the button and speak, or type a message.")

    # ---- NovaCore event wiring --------------------------------------------
    def _on_state_changed(self, old_state, new_state):
        self.root_widget.ids.robot.set_state(new_state)
        self.root_widget.ids.status_label.text = new_state.name

    def _on_speak_requested(self, text):
        self.core.request_state(NovaState.SPEAKING, force=True)
        self._append_chat("NOVA: " + text)
        self.tts.speak(text)
        Clock.schedule_once(
            lambda dt: self.core.request_state(NovaState.IDLE, force=True),
            config.SPEAKING_AUTO_IDLE_DELAY,
        )

    def _on_quit_requested(self):
        self.stop()

    def _append_chat(self, line: str):
        label = self.root_widget.ids.chat_label
        lines = (label.text + "\n" + line).split("\n")
        label.text = "\n".join(lines[-config.MAX_CHAT_LINES:])

    # ---- mic button ----------------------------------------------------------
    def on_mic_pressed(self):
        if self.core.state in (NovaState.LISTENING, NovaState.THINKING):
            return
        self.stt.listen()

    def _on_recognized(self, text: str):
        self._append_chat("You: " + text)
        Clock.schedule_once(lambda dt: self._handle_text(text), 0.3)

    def _on_stt_error(self, message: str):
        self.core.say("Sorry, I didn't catch that.")

    # ---- typed chat ------------------------------------------------------------
    def on_text_submit(self):
        field = self.root_widget.ids.chat_input
        text = field.text.strip()
        if not text:
            return
        field.text = ""
        self._append_chat("You: " + text)
        self.core.request_state(NovaState.THINKING, force=True)
        Clock.schedule_once(lambda dt: self._handle_text(text), 0.3)

    def _handle_text(self, text: str):
        handled = commands.dispatch(text, self.core)
        if not handled:
            # Placeholder reply -- this is the hook point for a future
            # real AI Chat backend (see NovaCore's docstring).
            self.core.say("I don't know that command yet.")


if __name__ == "__main__":
    NovaApp().run()

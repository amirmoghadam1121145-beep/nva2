"""
Speech-to-text for NOVA (Android build).

Uses Android's own built-in speech recognizer through
`android.speech.RecognizerIntent` -- the same system dialog used by
the keyboard's mic button and Google Assistant -- instead of a Python
speech library. This matters because Python's `SpeechRecognition` +
`PyAudio` (used on Windows) does not build for Android at all.

Why the Intent approach instead of a raw `SpeechRecognizer` +
`RecognitionListener`:
  - it needs no extra native build recipe in Buildozer,
  - it uses the phone's own (usually on-device) recognizer,
  - it is the most reliable, best-documented path for a first working
    build -- exactly what was asked for ("سالم بساز، اول ساده").

It requests RECORD_AUDIO permission the first time it runs.

On a desktop test run (no Android APIs available) it falls back to a
console `input()` prompt, so `python main.py` keeps working for logic
testing without a phone.
"""

from kivy.utils import platform

ANDROID = platform == "android"


class STTService:
    """Callbacks the App wires up after construction:
    - on_listening()       -- mic/recognizer about to start
    - on_result(text: str) -- recognized text
    - on_error(message)    -- recognition failed / was cancelled
    """

    _REQUEST_CODE = 1001

    def __init__(self):
        self.on_listening = None
        self.on_result = None
        self.on_error = None
        self._android_ready = False

        if ANDROID:
            self._setup_android()

    def _setup_android(self) -> None:
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.RECORD_AUDIO])

            from android import activity
            activity.bind(on_activity_result=self._on_activity_result)
            self._android_ready = True
        except Exception as exc:
            self._android_ready = False
            if self.on_error:
                self.on_error(f"Voice setup failed: {exc}")

    def listen(self) -> None:
        if self.on_listening:
            self.on_listening()

        if ANDROID and self._android_ready:
            self._start_android_recognizer()
        else:
            self._desktop_fallback()

    def _start_android_recognizer(self) -> None:
        try:
            from jnius import autoclass

            Intent = autoclass("android.content.Intent")
            RecognizerIntent = autoclass("android.speech.RecognizerIntent")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")

            intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM,
            )
            intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "Speak to NOVA...")

            PythonActivity.mActivity.startActivityForResult(intent, self._REQUEST_CODE)
        except Exception as exc:
            if self.on_error:
                self.on_error(f"Could not start voice recognition: {exc}")

    def _on_activity_result(self, request_code, result_code, intent) -> None:
        if request_code != self._REQUEST_CODE:
            return
        try:
            from jnius import autoclass

            Activity = autoclass("android.app.Activity")
            RecognizerIntent = autoclass("android.speech.RecognizerIntent")

            if result_code == Activity.RESULT_OK and intent is not None:
                results = intent.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
                if results and results.size() > 0:
                    text = results.get(0)
                    if self.on_result:
                        self.on_result(text)
                    return

            if self.on_error:
                self.on_error("Didn't catch that.")
        except Exception as exc:
            if self.on_error:
                self.on_error(f"Voice recognition error: {exc}")

    def _desktop_fallback(self) -> None:
        try:
            text = input("[NOVA test-mode] Type what you would say: ")
        except Exception:
            text = ""

        if text and self.on_result:
            self.on_result(text)
        elif self.on_error:
            self.on_error("No input received.")

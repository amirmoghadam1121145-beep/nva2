"""
Text-to-speech for NOVA (Android build).

On the phone this speaks through Android's own built-in TextToSpeech
engine (accessed via `plyer`), so:
  - no extra app or network call is needed,
  - no audio synthesis runs in Python, which keeps battery use low,
  - it uses whatever voice/language the user already has installed.

On a desktop test run (`python main.py`) it falls back to `pyttsx3` if
installed, or just prints the line, so the whole app can be smoke
-tested on a laptop before ever being built into an APK.
"""


class TTSService:
    def __init__(self):
        self._backend = None
        self._backend_kind = None

        try:
            from plyer import tts as plyer_tts
            self._backend = plyer_tts
            self._backend_kind = "plyer"
        except Exception:
            try:
                import pyttsx3
                self._backend = pyttsx3.init()
                self._backend.setProperty("rate", 165)
                self._backend_kind = "pyttsx3"
            except Exception:
                self._backend = None
                self._backend_kind = None

    def speak(self, text: str) -> None:
        if not text:
            return

        if self._backend_kind == "plyer":
            try:
                self._backend.speak(message=text)
                return
            except Exception:
                pass
        elif self._backend_kind == "pyttsx3":
            try:
                self._backend.say(text)
                self._backend.runAndWait()
                return
            except Exception:
                pass

        # Last-resort fallback (e.g. no TTS backend available at all).
        print("NOVA:", text)

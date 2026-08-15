"""
NOVA's command table (Android build).

Mirrors the *idea* of the Windows version's nova/commands.py -- a
simple "keyword: function" registry, checked top-to-bottom, first
match wins -- but every action here is something that actually exists
on a phone.

Windows-only actions were intentionally NOT ported, because they don't
mean anything on Android and porting them literally would just fail
silently or do nothing useful:
  - Notepad / os.system("start notepad")   -> no equivalent, dropped
  - Calculator / os.system("start calc")   -> no equivalent, dropped
  - Chrome via os.system("start chrome")   -> replaced with an Android
                                               ACTION_VIEW intent that
                                               opens the device's
                                               default browser

"chrome" is kept as an alias to the new open-browser action purely so
old habits (saying/typing "chrome") keep working; the actual mechanism
underneath is fully Android-native (see nova/platform_actions.py).

To add a new command later (AI chat fallback, plugins, system control,
...) add one more "keyword: function" entry here -- no other file
needs to change, exactly like the Windows version.
"""

import datetime

from .platform_actions import open_browser, open_camera, battery_status


def _tell_time(core) -> None:
    now = datetime.datetime.now().strftime("%H:%M")
    core.say(f"The time is {now}")


def _say_hello(core) -> None:
    core.say("Hello. Nice to hear you.")


def _open_browser(core) -> None:
    core.say("Opening the browser.")
    open_browser()


def _open_camera(core) -> None:
    core.say("Opening the camera.")
    open_camera()


def _battery(core) -> None:
    core.say(battery_status())


def _stop(core) -> None:
    core.say("Goodbye.")
    core.request_quit()


# Order matters, exactly like the Windows version's if/elif chain:
# the text is checked against these keywords top-to-bottom and the
# first match wins.
COMMANDS = {
    "chrome": _open_browser,     # alias, kept for muscle memory
    "browser": _open_browser,
    "camera": _open_camera,
    "battery": _battery,
    "time": _tell_time,
    "hello": _say_hello,
    "stop": _stop,
    "exit": _stop,
}


def dispatch(text: str, core) -> bool:
    """Match `text` against COMMANDS (same first-match-wins logic as the
    Windows voice_engine.py loop) and run it.

    Returns True if a command handled the text, False if NOVA should
    fall back to a plain chat reply (this is also the hook point for a
    future real AI Chat backend -- see NovaCore's docstring).
    """
    lowered = text.lower()
    for keyword, action in COMMANDS.items():
        if keyword in lowered:
            action(core)
            return True
    return False

"""
Thin wrappers around Android-specific actions, with safe fallbacks so
the exact same code can be smoke-tested with `python main.py` on a
laptop (Windows/Linux/macOS) before it's ever built into an APK.

These are the Android equivalents of the Windows version's os.system()
calls in nova/commands.py. Nothing here is shared code with the
Windows project -- this file only exists in nova_android/.
"""

import webbrowser

try:
    from plyer import battery as _battery_plyer
except Exception:
    _battery_plyer = None


def _android_activity():
    """Returns the running PythonActivity, or None off-Android."""
    try:
        from jnius import autoclass
        return autoclass("org.kivy.android.PythonActivity").mActivity
    except Exception:
        return None


def open_browser(url: str = "https://www.google.com") -> None:
    activity = _android_activity()
    if activity is not None:
        try:
            from jnius import autoclass
            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
            activity.startActivity(intent)
            return
        except Exception:
            pass
    # Desktop test-mode fallback.
    webbrowser.open(url)


def open_camera() -> None:
    activity = _android_activity()
    if activity is not None:
        try:
            from jnius import autoclass
            Intent = autoclass("android.content.Intent")
            MediaStore = autoclass("android.provider.MediaStore")
            intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            activity.startActivity(intent)
            return
        except Exception:
            pass
    print("[NOVA] Camera command received (no camera on this platform).")


def battery_status() -> str:
    if _battery_plyer is not None:
        try:
            pct = int(_battery_plyer.status.get("percentage", 0) or 0)
            return f"Battery is at {pct} percent."
        except Exception:
            pass
    return "Battery status is not available on this device."

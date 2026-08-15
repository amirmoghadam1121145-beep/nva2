"""
Central configuration for NOVA Android.

Same idea as the Windows version's nova/config.py: every tunable
number/color lives here so the look-and-feel can be re-tuned without
touching any class. The palette is intentionally kept identical to
the Windows build's config.py so NOVA "looks like herself" on both
platforms.
"""

# ---- App -----------------------------------------------------------------
APP_TITLE = "NOVA"

# ---- Palette (holographic sci-fi, matches nova_desktop/nova/config.py) ---
COLOR_BG = "#050b16"
COLOR_BODY = "#060b16"
COLOR_GLOW_SOFT = "#38bdf8"     # idle
COLOR_LISTEN = "#32ff9a"        # listening
COLOR_THINK = "#b99cff"         # thinking
COLOR_SPEAK = "#6ff6ff"         # speaking
COLOR_TEXT = "#e6fbff"

# ---- Animation timing (seconds) -------------------------------------------
BREATH_HALF_CYCLE = 1.6         # idle "breathing" bob, up then down
BLINK_MIN_DELAY = 2.5
BLINK_MAX_DELAY = 5.5
STATE_COLOR_TRANSITION = 0.35   # how long a state's color fade takes
SPEAKING_AUTO_IDLE_DELAY = 1.2  # how long a spoken line holds SPEAKING before falling back to IDLE

# ---- Chat log --------------------------------------------------------------
MAX_CHAT_LINES = 40             # trim the on-screen chat log to keep it light

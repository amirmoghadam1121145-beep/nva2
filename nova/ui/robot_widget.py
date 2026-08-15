"""
Procedural, animated NOVA robot for the Android app.

Same spirit as the Windows version's renderer
(nova_desktop/nova/ui/renderer.py): nothing here is an image file --
every shape is drawn with Kivy's Canvas instructions, sized relative
to the widget so it stays crisp on any phone screen, and costs very
little battery (the GPU does the actual drawing; Python only updates a
handful of numbers per frame).

"No teleporting" rule, kept identical to the Windows version's
movement.py: every visible change (state color, breathing, blinking,
pulse) goes through `kivy.animation.Animation`, never an instant jump.
"""

import random

from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line
from kivy.properties import NumericProperty, ListProperty
from kivy.animation import Animation
from kivy.clock import Clock

from ..state import NovaState
from .. import config


def _hex_to_rgba(hex_color: str, alpha: float = 1.0):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return [r, g, b, alpha]


STATE_COLORS = {
    NovaState.IDLE: config.COLOR_GLOW_SOFT,
    NovaState.LISTENING: config.COLOR_LISTEN,
    NovaState.THINKING: config.COLOR_THINK,
    NovaState.SPEAKING: config.COLOR_SPEAK,
}

# Per-state pulse animation: (peak_duration, trough_duration) in seconds.
# Faster pulse = feels more "active"; used for the glow rings + core.
STATE_PULSE_SPEED = {
    NovaState.LISTENING: (0.5, 0.5),
    NovaState.THINKING: (0.25, 0.25),
    NovaState.SPEAKING: (0.18, 0.18),
}


class RobotWidget(Widget):
    glow_color = ListProperty(_hex_to_rgba(config.COLOR_GLOW_SOFT))
    bob_offset = NumericProperty(0.0)
    pulse = NumericProperty(0.0)        # 0..1, drives glow/core pulsing
    eye_scale = NumericProperty(1.0)    # 1 = open, ~0 = blinking closed
    ring_angle = NumericProperty(0.0)   # rotating holo ring under NOVA

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._state = NovaState.IDLE

        self.bind(
            pos=self._redraw, size=self._redraw, glow_color=self._redraw,
            bob_offset=self._redraw, pulse=self._redraw,
            eye_scale=self._redraw, ring_angle=self._redraw,
        )

        Clock.schedule_interval(self._tick_ring, 1 / 60)
        self._start_breathing()
        self._schedule_blink()
        self._redraw()

    # ---- continuous ambient animation (not tied to state) ----------------
    def _tick_ring(self, dt):
        self.ring_angle = (self.ring_angle + dt * 24) % 360

    def _start_breathing(self):
        d = config.BREATH_HALF_CYCLE
        anim = (Animation(bob_offset=6, duration=d, t="in_out_sine") +
                Animation(bob_offset=-6, duration=d, t="in_out_sine"))
        anim.repeat = True
        anim.start(self)

    def _schedule_blink(self):
        delay = random.uniform(config.BLINK_MIN_DELAY, config.BLINK_MAX_DELAY)
        Clock.schedule_once(self._do_blink, delay)

    def _do_blink(self, dt):
        anim = (Animation(eye_scale=0.08, duration=0.08, t="in_out_quad") +
                Animation(eye_scale=1.0, duration=0.10, t="in_out_quad"))
        anim.start(self)
        self._schedule_blink()

    # ---- state transitions -------------------------------------------------
    def set_state(self, new_state: NovaState) -> None:
        self._state = new_state

        target_color = STATE_COLORS.get(new_state, config.COLOR_GLOW_SOFT)
        Animation.cancel_all(self, "glow_color")
        Animation(
            glow_color=_hex_to_rgba(target_color),
            duration=config.STATE_COLOR_TRANSITION, t="in_out_quad",
        ).start(self)

        Animation.cancel_all(self, "pulse")
        speeds = STATE_PULSE_SPEED.get(new_state)
        if speeds:
            up, down = speeds
            anim = (Animation(pulse=1, duration=up, t="in_out_sine") +
                    Animation(pulse=0, duration=down, t="in_out_sine"))
            anim.repeat = True
            anim.start(self)
        else:
            Animation(pulse=0, duration=0.4, t="in_out_quad").start(self)

    # ---- drawing -------------------------------------------------------------
    def _redraw(self, *args):
        self.canvas.clear()
        if self.width <= 0 or self.height <= 0:
            return

        cx = self.center_x
        cy = self.center_y + self.bob_offset
        base_r = min(self.width, self.height) * 0.30

        with self.canvas:
            # Rotating holographic ring beneath NOVA.
            Color(*self.glow_color, 0.35)
            ring_r = base_r * 1.55
            ring_cy = cy - base_r * 1.1
            Line(circle=(cx, ring_cy, ring_r, self.ring_angle, self.ring_angle + 260), width=1.6)
            Line(circle=(cx, ring_cy, ring_r * 0.7, -self.ring_angle * 1.3, -self.ring_angle * 1.3 + 200), width=1.2)

            # Soft outer glow layers (they widen slightly with `pulse`).
            for i, alpha in enumerate((0.06, 0.10, 0.16)):
                r = base_r * (1.5 - i * 0.18) + self.pulse * 14
                Color(*self.glow_color, alpha)
                Ellipse(pos=(cx - r, cy - r), size=(r * 2, r * 2))

            # Body.
            Color(*_hex_to_rgba(config.COLOR_BODY))
            Ellipse(pos=(cx - base_r, cy - base_r), size=(base_r * 2, base_r * 2))
            Color(*self.glow_color, 0.9)
            Line(circle=(cx, cy, base_r), width=2)

            # Eyes (blink = vertical squash toward 0, never disappear instantly).
            eye_r = base_r * 0.16
            eye_dx = base_r * 0.38
            eye_y = cy + base_r * 0.08
            Color(*self.glow_color, 1)
            for sign in (-1, 1):
                ex = cx + sign * eye_dx
                h = max(eye_r * self.eye_scale, 1.0)
                Ellipse(pos=(ex - eye_r, eye_y - h), size=(eye_r * 2, h * 2))

            # Chest core, pulses brighter/larger with the current state.
            core_r = base_r * (0.12 + self.pulse * 0.05)
            Color(*self.glow_color, 0.85)
            Ellipse(
                pos=(cx - core_r, cy - base_r * 0.45 - core_r),
                size=(core_r * 2, core_r * 2),
            )

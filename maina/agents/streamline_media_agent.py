"""
StreamLine Media Agent — YouTube & Spotify AI Agent Window
=============================================================

A floating, top-right "agent" window for media tasks — video discovery,
channel/playlist work on YouTube, and track/playlist/queue work on Spotify.
Same architectural family as the Microline Scientific agent window: a
self-contained PyQt6 widget that forwards user text to a host backend via
an `on_command` callback and renders whatever comes back via
`write_response()`. This widget never calls the YouTube or Spotify APIs
itself — it is purely the front-end shell.

What's different from a single-service agent
-----------------------------------------------
This window hosts **two services in one shell** via a tab switcher in the
header. Switching tabs:
    - Re-themes the accent colour (YouTube = red/crimson, Spotify = green)
      while keeping the shared futuristic dark-glass base palette.
    - Swaps the capability chip list to that service's actual feature set.
    - Changes which `agent_name` is sent to `on_command` — "youtube" or
      "spotify" — so the host backend can route the query correctly.
    - Keeps a single shared activity log so a user's full session (across
      both services) stays in one place, with chips on each line showing
      which service a given exchange belongs to.

Design goals (carried over from the Microline agent, then sharpened)
------------------------------------------------------------------------
1. Responsive desktop layout — from ~300px wide up to large monitors.
   No fixed pixel panel widths; everything scales or collapses by size.
2. Clean separation of concerns — theme tokens, small reusable widgets,
   the animated HUD orb, and the main window are each isolated.
3. Defensive UX — input disables itself mid-request, command history is
   recallable with arrow keys, missing backend produces a clear error.
4. Distinct visual identity per tab without feeling like two unrelated
   apps glued together — a shared chrome (glass panels, grid HUD, type)
   with service-specific accent colour and iconography.

Public API:
    StreamLineWindow(on_command=callable(agent_name: str, text: str) -> None)
    .write_response(text: str) -> None
    .set_thinking(val: bool) -> None
    .append_log(text: str) -> None
    .set_active_service(name: Literal["youtube", "spotify"]) -> None
"""
from __future__ import annotations

import math
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from PyQt6.QtCore import QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QBrush, QColor, QFont, QKeyEvent, QLinearGradient, QPainter, QPen,
    QTextCursor,
)
from PyQt6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QPushButton, QSizePolicy, QSplitter, QVBoxLayout, QWidget, QTextEdit,
)


# ═══════════════════════════════════════════════════════════════════════════
#  Theme tokens — shared "dark glass" base + per-service accent
# ═══════════════════════════════════════════════════════════════════════════

class Theme:
    """Shared futuristic base palette."""
    BG        = "#05060d"
    PANEL     = "#0a0d18"
    DARK      = "#070912"
    BORDER    = "#1b2138"
    BORDER_B  = "#2e3a5c"
    PRIMARY   = "#5ad8ff"
    PRI_DIM   = "#1f4a5c"
    PRI_GHOST = "#0c1622"
    TEXT      = "#aab6d8"
    TEXT_DIM  = "#3c4566"
    WHITE     = "#eaf2ff"
    RED       = "#ff4d6d"
    YELLOW    = "#ffd166"

    FONT_FAMILY = "Segoe UI"
    MONO_FAMILY = "Consolas"

    @staticmethod
    def qc(hex_colour: str, alpha: int = 255) -> QColor:
        c = QColor(hex_colour)
        c.setAlpha(alpha)
        return c


@dataclass(frozen=True)
class ServiceProfile:
    """Everything that changes when the user switches tabs."""
    key: str
    label: str
    tagline: str
    accent: str
    accent_dim: str
    accent_ghost: str
    glyph: str
    capabilities: list[str]
    placeholder: str
    welcome_lines: list[str]


YOUTUBE = ServiceProfile(
    key="youtube",
    label="YOUTUBE",
    tagline="Video Intelligence & Channel Operations",
    accent="#ff3b5c",
    accent_dim="#5c1726",
    accent_ghost="#1a0a10",
    glyph="▶",
    capabilities=[
        "🔎 Video & Channel Search",
        "📈 Trending & Topic Discovery",
        "🗂️ Playlist Building",
        "📊 Channel Analytics Lookup",
        "💬 Comment & Engagement Insights",
        "🎬 Upload Metadata Assistance",
    ],
    placeholder="Search videos, channels, playlists…",
    welcome_lines=[
        "SYS: YouTube module online.",
        "SYS: Ready for video search, channel & playlist queries.",
    ],
)

SPOTIFY = ServiceProfile(
    key="spotify",
    label="SPOTIFY",
    tagline="Audio Discovery & Playlist Operations",
    accent="#1ed760",
    accent_dim="#0f4f29",
    accent_ghost="#081a10",
    glyph="●",
    capabilities=[
        "🎵 Track & Artist Search",
        "🗂️ Playlist Building & Editing",
        "📈 Audio Feature Lookup (tempo, key, energy)",
        "🎚️ Queue & Playback Control",
        "🧑‍🎤 Artist & Album Insights",
        "🔁 Recommendation Generation",
    ],
    placeholder="Search tracks, artists, playlists…",
    welcome_lines=[
        "SYS: Spotify module online.",
        "SYS: Ready for track search, playlist & queue queries.",
    ],
)

SERVICES: dict[str, ServiceProfile] = {p.key: p for p in (YOUTUBE, SPOTIFY)}


# ═══════════════════════════════════════════════════════════════════════════
#  Responsive sizing helper
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Breakpoints:
    compact: int = 360
    narrow:  int = 460
    comfortable: int = 620


BP = Breakpoints()


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def scaled_font(base_pt: float, width: int, *, bold: bool = False,
                 family: str = Theme.FONT_FAMILY) -> QFont:
    factor = clamp(math.sqrt(width / 480.0), 0.78, 1.35)
    size = max(6, round(base_pt * factor))
    f = QFont(family, size)
    if bold:
        f.setWeight(QFont.Weight.Bold)
    return f


# ═══════════════════════════════════════════════════════════════════════════
#  Log widget
# ═══════════════════════════════════════════════════════════════════════════

class LogWidget(QTextEdit):
    _append_signal = pyqtSignal(str, str, str)

    ROLE_COLOURS = {
        "user":   Theme.WHITE,
        "error":  Theme.RED,
        "system": Theme.YELLOW,
        "info":   Theme.TEXT,
    }

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont(Theme.MONO_FAMILY, 9))
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(f"""
            QTextEdit {{
                background: {Theme.PANEL};
                color: {Theme.TEXT};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 6px;
            }}
            QScrollBar:vertical {{
                background: {Theme.BG}; width: 7px; border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {Theme.BORDER_B}; border-radius: 3px; min-height: 16px;
            }}
        """)
        self._append_signal.connect(self._do_append)

    def log(self, text: str, role: str = "info", service: Optional[str] = None) -> None:
        self._append_signal.emit(text, role, service or "")

    def _do_append(self, text: str, role: str, service_key: str) -> None:
        if role == "agent":
            profile = SERVICES.get(service_key)
            colour = Theme.qc(profile.accent if profile else Theme.PRIMARY)
        else:
            colour = Theme.qc(self.ROLE_COLOURS.get(role, Theme.TEXT))
        cur = self.textCursor()
        fmt = cur.charFormat()
        fmt.setForeground(QBrush(colour))
        cur.movePosition(QTextCursor.MoveOperation.End)
        cur.insertText(text + "\n", fmt)
        self.setTextCursor(cur)
        self.ensureCursorVisible()

    def set_base_font_size(self, pt: int) -> None:
        f = self.font()
        f.setPointSize(pt)
        self.setFont(f)


# ═══════════════════════════════════════════════════════════════════════════
#  Command-history line edit
# ═══════════════════════════════════════════════════════════════════════════

class HistoryLineEdit(QLineEdit):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._history: list[str] = []
        self._cursor = 0

    def remember(self, text: str) -> None:
        if text and (not self._history or self._history[-1] != text):
            self._history.append(text)
        self._cursor = len(self._history)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Up:
            if self._history and self._cursor > 0:
                self._cursor -= 1
                self.setText(self._history[self._cursor])
            return
        if event.key() == Qt.Key.Key_Down:
            if self._history:
                if self._cursor < len(self._history) - 1:
                    self._cursor += 1
                    self.setText(self._history[self._cursor])
                else:
                    self._cursor = len(self._history)
                    self.clear()
            return
        super().keyPressEvent(event)


# ═══════════════════════════════════════════════════════════════════════════
#  Animated HUD orb
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class OrbState:
    rings: list[float] = field(default_factory=lambda: [0.0, 90.0, 180.0, 270.0])
    scan: float = 0.0
    pulses: list[float] = field(default_factory=lambda: [0.0, 30.0])
    blink: bool = True
    blink_tick: int = 0


class OrbCanvas(QWidget):
    STEP_MS = 20

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumSize(72, 72)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.state = "READY"
        self.thinking = False
        self.profile: ServiceProfile = YOUTUBE
        self._s = OrbState()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)
        self._timer.start(self.STEP_MS)

    def set_profile(self, profile: ServiceProfile) -> None:
        self.profile = profile
        self.update()

    def _step(self) -> None:
        s = self._s
        speed = 2.0 if self.thinking else 0.7
        s.rings = [(r + speed * (1 + i * 0.3)) % 360 for i, r in enumerate(s.rings)]
        s.scan = (s.scan + (3.5 if self.thinking else 1.2)) % 360
        side = min(self.width(), self.height()) or 1
        limit = side * 0.6
        pulse_speed = 3.5 if self.thinking else 1.5
        s.pulses = [r + pulse_speed for r in s.pulses if r + pulse_speed < limit]
        spawn_chance = 0.06 if self.thinking else 0.02
        if len(s.pulses) < 3 and random.random() < spawn_chance:
            s.pulses.append(0.0)
        s.blink_tick += 1
        if s.blink_tick >= 30:
            s.blink = not s.blink
            s.blink_tick = 0
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        side = min(w, h)
        p.fillRect(self.rect(), Theme.qc(Theme.BG))
        accent = self.profile.accent
        accent_dim = self.profile.accent_dim
        accent_ghost = self.profile.accent_ghost
        self._paint_grid(p, w, h)
        self._paint_pulses(p, cx, cy, side, accent)
        self._paint_orbit_rings(p, cx, cy, side, accent)
        self._paint_scanner(p, cx, cy, side)
        self._paint_core(p, cx, cy, w, side, accent, accent_dim, accent_ghost)
        self._paint_status_text(p, cx, cy, w, side, accent)

    def _paint_grid(self, p: QPainter, w: int, h: int) -> None:
        step = max(24, min(w, h) // 6)
        p.setPen(QPen(Theme.qc(Theme.PRI_GHOST), 1))
        for x in range(0, w, step):
            for y in range(0, h, step):
                p.drawPoint(x, y)

    def _paint_pulses(self, p: QPainter, cx: float, cy: float, side: float, accent: str) -> None:
        limit = side * 0.6
        p.setBrush(Qt.BrushStyle.NoBrush)
        for radius in self._s.pulses:
            alpha = max(0, int(190 * (1.0 - radius / limit))) if limit else 0
            p.setPen(QPen(Theme.qc(accent, alpha), 1))
            p.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

    def _paint_orbit_rings(self, p: QPainter, cx: float, cy: float, side: float, accent: str) -> None:
        rings_spec = [(0.40, 80, 60), (0.32, 55, 40), (0.24, 35, 28)]
        for idx, (r_frac, arc_len, gap) in enumerate(rings_spec):
            r = side * r_frac
            alpha = max(0, min(255, 150 - idx * 28))
            p.setPen(QPen(Theme.qc(accent, alpha), max(0.6, 1.5 - idx * 0.3)))
            p.setBrush(Qt.BrushStyle.NoBrush)
            rect = QRectF(cx - r, cy - r, r * 2, r * 2)
            angle = self._s.rings[idx]
            end = angle + 360
            while angle < end:
                p.drawArc(rect, int(angle * 16), int(arc_len * 16))
                angle += arc_len + gap

    def _paint_scanner(self, p: QPainter, cx: float, cy: float, side: float) -> None:
        r = side * 0.42
        rect = QRectF(cx - r, cy - r, r * 2, r * 2)
        p.setPen(QPen(Theme.qc(Theme.PRIMARY, 170), 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(rect, int(self._s.scan * 16), int(50 * 16))

    def _paint_core(self, p: QPainter, cx: float, cy: float, w: float, side: float,
                     accent: str, accent_dim: str, accent_ghost: str) -> None:
        r = side * 0.18
        grad = QLinearGradient(cx - r, cy - r, cx + r, cy + r)
        grad.setColorAt(0, Theme.qc(accent_ghost))
        grad.setColorAt(1, Theme.qc(accent_dim))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))
        label_pt = max(8, int(side * 0.16))
        p.setFont(QFont(Theme.FONT_FAMILY, label_pt, QFont.Weight.Bold))
        p.setPen(QPen(Theme.qc(accent, 230), 1))
        p.drawText(QRectF(0, cy - label_pt, w, label_pt * 2),
                   Qt.AlignmentFlag.AlignCenter, self.profile.glyph)

    def _paint_status_text(self, p: QPainter, cx: float, cy: float, w: float, side: float, accent: str) -> None:
        sy = cy + side * 0.38
        status_pt = max(6, int(side * 0.055))
        if self.thinking:
            text, colour = "◈  PROCESSING", Theme.qc(Theme.YELLOW)
        else:
            dot = "●" if self._s.blink else "○"
            text, colour = f"{dot}  {self.state}", Theme.qc(accent)
        p.setPen(QPen(colour, 1))
        p.setFont(QFont(Theme.MONO_FAMILY, status_pt, QFont.Weight.Bold))
        p.drawText(QRectF(0, sy, w, status_pt * 2.4),
                   Qt.AlignmentFlag.AlignCenter, text)

    def set_processing(self, is_processing: bool) -> None:
        self.thinking = is_processing
        self.state = "PROCESSING" if is_processing else "READY"


# ═══════════════════════════════════════════════════════════════════════════
#  Service tab switcher
# ═══════════════════════════════════════════════════════════════════════════

class ServiceTabs(QWidget):
    service_changed = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._active_key = YOUTUBE.key
        self._buttons: dict[str, QPushButton] = {}
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        for profile in (YOUTUBE, SPOTIFY):
            btn = QPushButton(f"{profile.glyph}  {profile.label}")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _checked, k=profile.key: self._on_click(k))
            layout.addWidget(btn)
            self._buttons[profile.key] = btn
        self._restyle()

    def _on_click(self, key: str) -> None:
        if key == self._active_key:
            return
        self._active_key = key
        self._restyle()
        self.service_changed.emit(key)

    def set_active(self, key: str) -> None:
        if key not in self._buttons or key == self._active_key:
            return
        self._active_key = key
        self._restyle()

    def _restyle(self) -> None:
        for key, btn in self._buttons.items():
            profile = SERVICES[key]
            is_active = key == self._active_key
            btn.setChecked(is_active)
            if is_active:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {profile.accent_ghost};
                        color: {profile.accent};
                        border: 1px solid {profile.accent};
                        border-radius: 12px;
                        padding: 4px 12px;
                        font-weight: 600;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {Theme.TEXT_DIM};
                        border: 1px solid {Theme.BORDER};
                        border-radius: 12px;
                        padding: 4px 12px;
                    }}
                    QPushButton:hover {{
                        border: 1px solid {Theme.BORDER_B};
                        color: {Theme.TEXT};
                    }}
                """)

    def apply_font_scale(self, width: int) -> None:
        f = scaled_font(8, width, bold=True, family=Theme.FONT_FAMILY)
        for btn in self._buttons.values():
            btn.setFont(f)


# ═══════════════════════════════════════════════════════════════════════════
#  Capability panel
# ═══════════════════════════════════════════════════════════════════════════

class CapabilityPanel(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {Theme.BG};")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(5)
        self._header = QLabel("▸ CAPABILITIES")
        self._header.setFont(QFont(Theme.FONT_FAMILY, 7, QFont.Weight.Bold))
        self._header.setStyleSheet(f"color: {Theme.TEXT_DIM}; background: transparent;")
        self._layout.addWidget(self._header)
        self._chip_container = QVBoxLayout()
        self._chip_container.setSpacing(5)
        self._layout.addLayout(self._chip_container)
        self._chips: list[QLabel] = []
        self._layout.addStretch()
        self.set_profile(YOUTUBE)

    def set_profile(self, profile: ServiceProfile) -> None:
        for chip in self._chips:
            chip.setParent(None)
            chip.deleteLater()
        self._chips.clear()
        for cap in profile.capabilities:
            chip = QLabel(cap)
            chip.setFont(QFont(Theme.FONT_FAMILY, 7))
            chip.setWordWrap(True)
            chip.setStyleSheet(
                f"color: {profile.accent}; background: {Theme.PANEL}; "
                f"border: 1px solid {Theme.BORDER}; border-radius: 4px; padding: 4px 6px;"
            )
            self._chip_container.addWidget(chip)
            self._chips.append(chip)

    def apply_font_scale(self, width: int) -> None:
        self._header.setFont(scaled_font(7, width, bold=True))
        chip_font = scaled_font(7, width)
        for chip in self._chips:
            chip.setFont(chip_font)


# ═══════════════════════════════════════════════════════════════════════════
#  Header bar
# ═══════════════════════════════════════════════════════════════════════════

class HeaderBar(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedHeight(58)
        self.setStyleSheet(f"background: {Theme.DARK}; border-bottom: 1px solid {Theme.BORDER_B};")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 6, 12, 6)
        outer.setSpacing(4)
        top_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        self._title = QLabel("◈ STREAMLINE MEDIA")
        self._title.setFont(QFont(Theme.FONT_FAMILY, 10, QFont.Weight.Bold))
        self._title.setStyleSheet(f"color: {Theme.PRIMARY}; background: transparent;")
        self._tagline = QLabel(YOUTUBE.tagline)
        self._tagline.setFont(QFont(Theme.FONT_FAMILY, 7))
        self._tagline.setStyleSheet(f"color: {Theme.TEXT_DIM}; background: transparent;")
        title_col.addWidget(self._title)
        title_col.addWidget(self._tagline)
        top_row.addLayout(title_col)
        top_row.addStretch()
        self._clock = QLabel("00:00")
        self._clock.setFont(QFont(Theme.MONO_FAMILY, 11, QFont.Weight.Bold))
        self._clock.setStyleSheet(f"color: {Theme.PRIMARY}; background: transparent;")
        top_row.addWidget(self._clock)
        outer.addLayout(top_row)
        self.tabs = ServiceTabs()
        outer.addWidget(self.tabs)

    def set_tagline(self, text: str) -> None:
        self._tagline.setText(text)

    def set_clock_text(self, text: str) -> None:
        self._clock.setText(text)

    def set_compact(self, compact: bool) -> None:
        self._tagline.setVisible(not compact)

    def apply_font_scale(self, width: int) -> None:
        self._title.setFont(scaled_font(10, width, bold=True))
        self._tagline.setFont(scaled_font(7, width))
        self._clock.setFont(scaled_font(11, width, bold=True, family=Theme.MONO_FAMILY))
        self.tabs.apply_font_scale(width)


# ═══════════════════════════════════════════════════════════════════════════
#  Input bar
# ═══════════════════════════════════════════════════════════════════════════

class InputBar(QWidget):
    submitted = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {Theme.DARK}; border-top: 1px solid {Theme.BORDER};")
        self._profile = YOUTUBE
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(5)
        self._input = HistoryLineEdit()
        self._input.setFont(QFont(Theme.FONT_FAMILY, 9))
        self._input.setFixedHeight(30)
        layout.addWidget(self._input)
        self._send_btn = QPushButton("➤")
        self._send_btn.setFixedSize(30, 30)
        self._send_btn.setFont(QFont(Theme.FONT_FAMILY, 11, QFont.Weight.Bold))
        self._send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._send_btn)
        self._input.returnPressed.connect(self._emit_submit)
        self._send_btn.clicked.connect(self._emit_submit)
        self.set_profile(YOUTUBE)

    def set_profile(self, profile: ServiceProfile) -> None:
        self._profile = profile
        self._input.setPlaceholderText(profile.placeholder)
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background: {Theme.PANEL}; color: {Theme.WHITE};
                border: 1px solid {Theme.BORDER}; border-radius: 6px; padding: 4px 8px;
            }}
            QLineEdit:focus {{ border: 1px solid {profile.accent}; }}
            QLineEdit:disabled {{ color: {Theme.TEXT_DIM}; border: 1px solid {Theme.BORDER}; }}
        """)
        self._send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {profile.accent_ghost}; color: {profile.accent};
                border: 1px solid {profile.accent_dim}; border-radius: 6px;
            }}
            QPushButton:hover {{ background: {profile.accent_dim}; border: 1px solid {profile.accent}; }}
            QPushButton:disabled {{ color: {Theme.TEXT_DIM}; border: 1px solid {Theme.BORDER}; }}
        """)

    def _emit_submit(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        self._input.remember(text)
        self._input.clear()
        self.submitted.emit(text)

    def set_busy(self, busy: bool) -> None:
        self._input.setEnabled(not busy)
        self._send_btn.setEnabled(not busy)
        if not busy:
            self._input.setFocus()

    def apply_font_scale(self, width: int) -> None:
        self._input.setFont(scaled_font(9, width))


# ═══════════════════════════════════════════════════════════════════════════
#  Footer bar
# ═══════════════════════════════════════════════════════════════════════════

class FooterBar(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedHeight(22)
        self.setStyleSheet(f"background: {Theme.DARK}; border-top: 1px solid {Theme.BORDER};")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        self._status = QLabel("● Connected")
        self._status.setFont(QFont(Theme.FONT_FAMILY, 7))
        self._status.setStyleSheet(f"color: {Theme.TEXT_DIM}; background: transparent;")
        layout.addWidget(self._status)
        layout.addStretch()
        self._routing = QLabel("Routing → YouTube")
        self._routing.setFont(QFont(Theme.FONT_FAMILY, 7))
        self._routing.setStyleSheet(f"color: {Theme.TEXT_DIM}; background: transparent;")
        layout.addWidget(self._routing)

    def set_profile(self, profile: ServiceProfile) -> None:
        self._routing.setText(f"Routing → {profile.label.title()}")
        self._routing.setStyleSheet(f"color: {profile.accent}; background: transparent;")

    def set_compact(self, compact: bool) -> None:
        self._status.setVisible(not compact)

    def apply_font_scale(self, width: int) -> None:
        f = scaled_font(7, width)
        self._status.setFont(f)
        self._routing.setFont(f)


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════════

class StreamLineWindow(QMainWindow):
    """Top-right floating agent window for YouTube + Spotify media tasks."""

    def __init__(self, on_command: Optional[Callable[[str, str], None]] = None,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("◈ StreamLine Media — YouTube & Spotify Agent")
        self.setMinimumSize(300, 400)
        self.resize(440, 600)
        self.on_command = on_command
        self._busy = False
        self._active: ServiceProfile = YOUTUBE
        self._position_top_right()
        self._build_ui()
        self._seed_log()
        self._start_clock()

    def _position_top_right(self) -> None:
        try:
            screen = QApplication.primaryScreen().availableGeometry()
            margin = 20
            x = max(0, screen.width() - self.width() - margin)
            self.move(x, margin)
        except Exception:
            pass

    def _build_ui(self) -> None:
        central = QWidget()
        central.setStyleSheet(f"background: {Theme.BG};")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.header = HeaderBar()
        self.header.tabs.service_changed.connect(self._on_service_changed)
        root.addWidget(self.header)
        self._top_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._top_splitter.setStyleSheet(f"""
            QSplitter::handle {{ background: {Theme.BORDER}; }}
            QSplitter::handle:hover {{ background: {Theme.BORDER_B}; }}
        """)
        self._top_splitter.setChildrenCollapsible(False)
        self.orb = OrbCanvas()
        self._top_splitter.addWidget(self.orb)
        self.capabilities = CapabilityPanel()
        self._top_splitter.addWidget(self.capabilities)
        self._top_splitter.setStretchFactor(0, 1)
        self._top_splitter.setStretchFactor(1, 1)
        root.addWidget(self._top_splitter, stretch=3)
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {Theme.BORDER};")
        root.addWidget(sep)
        log_header = QLabel("  ▸ ACTIVITY LOG")
        log_header.setFixedHeight(20)
        log_header.setFont(QFont(Theme.FONT_FAMILY, 7, QFont.Weight.Bold))
        log_header.setStyleSheet(f"color: {Theme.TEXT_DIM}; background: {Theme.DARK};")
        root.addWidget(log_header)
        self._log_header = log_header
        self.log = LogWidget()
        root.addWidget(self.log, stretch=4)
        self.input_bar = InputBar()
        self.input_bar.submitted.connect(self._handle_submit)
        root.addWidget(self.input_bar)
        self.footer = FooterBar()
        root.addWidget(self.footer)

    def _seed_log(self) -> None:
        self.log.log("SYS: StreamLine Media Agent v1.0 online.", role="system")
        self.log.log("SYS: Two modules loaded — YouTube & Spotify.", role="system")
        for line in YOUTUBE.welcome_lines:
            self.log.log(line, role="system")

    def _start_clock(self) -> None:
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start(1000)
        self._tick_clock()

    def _tick_clock(self) -> None:
        self.header.set_clock_text(time.strftime("%H:%M"))

    def _on_service_changed(self, key: str) -> None:
        self.set_active_service(key)

    def set_active_service(self, key: str) -> None:
        profile = SERVICES.get(key)
        if profile is None or profile.key == self._active.key:
            return
        self._active = profile
        self.header.tabs.set_active(profile.key)
        self.header.set_tagline(profile.tagline)
        self.orb.set_profile(profile)
        self.capabilities.set_profile(profile)
        self.input_bar.set_profile(profile)
        self.footer.set_profile(profile)
        self.log.log(f"SYS: Switched to {profile.label} module.", role="system")
        for line in profile.welcome_lines:
            self.log.log(line, role="system")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        width = event.size().width()
        self._apply_breakpoints(width)
        self._apply_font_scaling(width)

    def _apply_breakpoints(self, width: int) -> None:
        compact = width < BP.compact
        narrow = width < BP.narrow
        self.header.set_compact(compact)
        self.footer.set_compact(compact)
        self.capabilities.setVisible(not compact)
        if compact:
            self._top_splitter.setSizes([1, 0])
        elif narrow:
            total = max(self._top_splitter.width(), 1)
            self._top_splitter.setSizes([int(total * 0.55), int(total * 0.45)])
        self._log_header.setVisible(width >= BP.compact)

    def _apply_font_scaling(self, width: int) -> None:
        self.header.apply_font_scale(width)
        self.capabilities.apply_font_scale(width)
        self.input_bar.apply_font_scale(width)
        self.footer.apply_font_scale(width)
        log_pt = max(7, round(9 * clamp(math.sqrt(width / 480.0), 0.85, 1.3)))
        self.log.set_base_font_size(log_pt)

    def _handle_submit(self, text: str) -> None:
        if self._busy:
            return
        self.log.log(f"You [{self._active.label}]: {text}", role="user")
        if self.on_command is None:
            self.log.log("ERR: Backend not connected. Launch from host app first.", role="error")
            return
        self._set_busy(True)
        threading.Thread(
            target=self._run_command, args=(self._active.key, text), daemon=True
        ).start()

    def _run_command(self, agent_key: str, text: str) -> None:
        try:
            self.on_command(agent_key, text)
        except Exception as exc:
            self.log.log(f"ERR: {exc}", role="error", service=agent_key)
            self._set_busy(False)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.orb.set_processing(busy)
        self.input_bar.set_busy(busy)

    # ── Public API ──

    def write_response(self, text: str, service: Optional[str] = None) -> None:
        key = service or self._active.key
        if text:
            display = text if len(text) <= 500 else text[:500] + "..."
            label = SERVICES.get(key, self._active).label
            self.log.log(f"{label}: {display}", role="agent", service=key)
        self._set_busy(False)

    def set_thinking(self, val: bool) -> None:
        self._set_busy(val)

    def append_log(self, text: str) -> None:
        role = "info"
        lowered = text.lower()
        if "err" in lowered:
            role = "error"
        elif "sys:" in lowered:
            role = "system"
        elif lowered.startswith("you"):
            role = "user"
        self.log.log(text, role=role)


# ═══════════════════════════════════════════════════════════════════════════
#  Smoke test
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    def fake_backend(agent: str, text: str) -> None:
        time.sleep(1.0)
        if agent == "youtube":
            reply = f"Found 5 videos matching '{text}'. Top result: 12.4M views."
        else:
            reply = f"Found 8 tracks matching '{text}'. Top result: 92 BPM."
        win.write_response(reply, service=agent)

    app = QApplication(sys.argv)
    win = StreamLineWindow(on_command=fake_backend)
    win.show()
    sys.exit(app.exec())
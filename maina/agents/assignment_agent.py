"""
Assignment Helper — AI Academic Agent Window
Opens in top-left of screen. Handles homework, essays, research, academic tasks.

v3.1 — Voice-enabled console redesign:
  • Circuit-trace background matching the JARVIS design language
  • Rotating "knowledge ring" orb with radial-gradient core, now with
    LISTENING / SPEAKING states in addition to ANALYSING / READY
  • Slim top status strip (LINK / SIGNAL / MODE)
  • Mic button for voice input (speech-to-text) beside the send button
  • Voice-output toggle — Helper replies are spoken aloud (text-to-speech)
  • Capability chips redrawn as data-readout tiles
  • Fully wired to MainWindow's status_callback / on_closed integration
"""
from __future__ import annotations
import time, threading
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QRectF
from PyQt6.QtGui import (
    QColor, QFont, QBrush, QPainter, QPen, QRadialGradient, QTextCursor, QCloseEvent
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFrame, QSizePolicy,
    QComboBox, QGridLayout
)
import math, random

from agent.voice_utils import VoiceEngine, listen_once

# ─── Colour Palette — deep violet / magenta console ───────────────────────
class AC:
    BG       = "#0a0010"
    PANEL    = "#0f0016"
    PANEL2   = "#12001a"
    BORDER   = "#2e0a4a"
    BORDER_B = "#7a2ecf"
    PRI      = "#c98cff"
    PRI_DIM  = "#4a0f7a"
    PRI_GHO  = "#170026"
    ACC      = "#ff8cf0"
    ACC2     = "#b98cff"
    TEXT     = "#e4c8ff"
    TEXT_DIM = "#5c3a80"
    WHITE    = "#f5ecff"
    DARK     = "#08000d"
    RED      = "#ff4d78"
    YELLOW   = "#ffd24d"
    CYAN     = "#8cdcff"

def aq(h: str, a: int = 255) -> QColor:
    c = QColor(h); c.setAlpha(a); return c


class AssignmentLogWidget(QTextEdit):
    _sig = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 9))
        self.setStyleSheet(f"""
            QTextEdit {{
                background: {AC.PANEL};
                color: {AC.TEXT};
                border: 1px solid {AC.BORDER};
                border-radius: 6px;
                padding: 8px;
            }}
            QScrollBar:vertical {{ background: {AC.BG}; width: 7px; border: none; }}
            QScrollBar::handle:vertical {{ background: {AC.BORDER_B}; border-radius: 3px; min-height: 16px; }}
        """)
        self._sig.connect(self._do_append)

    def append_log(self, text: str):
        self._sig.emit(text)

    def _do_append(self, text: str):
        cur = self.textCursor()
        tl = text.lower()
        if   "helper:" in tl: col = aq(AC.PRI)
        elif "you:" in tl:    col = aq(AC.WHITE)
        elif "err" in tl:     col = aq(AC.RED)
        elif "sys:" in tl:    col = aq(AC.YELLOW)
        else:                 col = aq(AC.TEXT)
        fmt = cur.charFormat()
        fmt.setForeground(QBrush(col))
        cur.movePosition(QTextCursor.MoveOperation.End)
        cur.insertText(text + "\n", fmt)
        self.setTextCursor(cur)
        self.ensureCursorVisible()


class AssignmentOrbCanvas(QWidget):
    """Futuristic knowledge-ring HUD orb for Assignment Helper."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(140, 140)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.state    = "READY"
        self.thinking = False
        self.listening = False
        self.speaking  = False
        self._tick    = 0
        self._rings   = [0.0, 120.0, 240.0]
        self._scan    = 45.0
        self._blink   = True
        self._blink_t = 0
        self._core    = 0.0
        self._nodes   = [random.uniform(0, 360) for _ in range(5)]
        self._pulses: list[float] = [0.0, 25.0]
        t = QTimer(self)
        t.timeout.connect(self._step)
        t.start(20)

    def _active(self) -> bool:
        return self.thinking or self.listening or self.speaking

    def _step(self):
        self._tick += 1
        spd = 1.8 if self._active() else 0.6
        for i in range(len(self._rings)):
            self._rings[i] = (self._rings[i] + spd * (1 + i * 0.4)) % 360
        for i in range(len(self._nodes)):
            self._nodes[i] = (self._nodes[i] + (0.8 if self._active() else 0.3)) % 360
        self._scan = (self._scan + (3.0 if self._active() else 1.0)) % 360
        self._core = (self._core + (3.6 if self._active() else 1.4)) % 360
        fw = min(self.width(), self.height())
        lim = fw * 0.56
        ps = 3.0 if self._active() else 1.2
        self._pulses = [r + ps for r in self._pulses if r + ps < lim]
        if len(self._pulses) < 3 and random.random() < (0.05 if self._active() else 0.018):
            self._pulses.append(0.0)
        self._blink_t += 1
        if self._blink_t >= 32:
            self._blink = not self._blink; self._blink_t = 0
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        cx, cy = W/2, H/2
        fw = min(W, H)
        p.fillRect(self.rect(), aq(AC.BG))

        p.setPen(QPen(aq(AC.PRI, 14), 1))
        step = 34
        for x in range(0, W, step):
            for y in range(0, H, step):
                p.drawLine(x, y, x + 9, y)
                p.drawLine(x, y, x, y + 9)

        # Core orb colour shifts by state: violet=ready/thinking, cyan=listening, pink=speaking
        core_col = AC.ACC
        if self.listening:
            core_col = AC.CYAN
        elif self.speaking:
            core_col = AC.ACC

        for pr in self._pulses:
            a = max(0, int(180 * (1.0 - pr / (fw*0.56))))
            p.setPen(QPen(aq(core_col, a), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QRectF(cx-pr, cy-pr, pr*2, pr*2))

        for idx, (r_frac, arc_l, gap) in enumerate(
            [(0.40, 70, 55), (0.32, 48, 36), (0.24, 30, 24)]
        ):
            rr = fw * r_frac
            base = self._rings[idx]
            a = max(0, min(255, int(160 - idx*25)))
            p.setPen(QPen(aq(AC.PRI, a), 1.6 - idx*0.3))
            p.setBrush(Qt.BrushStyle.NoBrush)
            rect = QRectF(cx-rr, cy-rr, rr*2, rr*2)
            angle = base
            while angle < base + 360:
                p.drawArc(rect, int(angle*16), int(arc_l*16))
                angle += arc_l + gap

        # scanner
        sr_ = fw * 0.44
        p.setPen(QPen(aq(core_col, 170), 1.5))
        srect = QRectF(cx-sr_, cy-sr_, sr_*2, sr_*2)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(srect, int(self._scan*16), int(45*16))

        # Orbiting knowledge nodes with faint bonds to centre
        node_r = fw * 0.30
        pts = []
        for ang in self._nodes:
            rad = math.radians(ang)
            nx = cx + node_r * math.cos(rad)
            ny = cy + node_r * math.sin(rad) * 0.9
            pts.append((nx, ny))
        p.setPen(QPen(aq(AC.PRI, 45), 1))
        for nx, ny in pts:
            p.drawLine(int(cx), int(cy), int(nx), int(ny))
        for nx, ny in pts:
            p.setBrush(QBrush(aq(core_col, 210)))
            p.setPen(QPen(aq(AC.PRI, 160), 1))
            p.drawEllipse(QRectF(nx-3, ny-3, 6, 6))

        # Core orb — radial gradient + rotating inner ring
        orb_r = int(fw * 0.155)
        grad = QRadialGradient(cx, cy, orb_r)
        grad.setColorAt(0.0, aq(core_col, 235))
        grad.setColorAt(0.55, aq(AC.PRI_DIM, 220))
        grad.setColorAt(1.0, aq(AC.BG, 0))
        p.setBrush(QBrush(grad)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx-orb_r, cy-orb_r, orb_r*2, orb_r*2))
        p.setPen(QPen(aq(core_col, 200), 1.3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        inner = orb_r * 0.62
        p.drawArc(QRectF(cx-inner, cy-inner, inner*2, inner*2), int(self._core*16), int(120*16))
        p.drawArc(QRectF(cx-inner, cy-inner, inner*2, inner*2), int((self._core+180)*16), int(120*16))

        p.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        p.setPen(QPen(aq(AC.WHITE, 235), 1))
        p.drawText(QRectF(0, cy-9, W, 18), Qt.AlignmentFlag.AlignCenter, "AH")

        # Status
        sy = cy + fw * 0.40
        sym = "●" if self._blink else "○"
        if self.listening:
            txt, col = "🎙  LISTENING", aq(AC.CYAN)
        elif self.speaking:
            txt, col = "🔊  SPEAKING", aq(AC.ACC)
        elif self.thinking:
            txt, col = "◈  ANALYSING", aq(AC.YELLOW)
        else:
            txt, col = f"{sym}  {self.state}", aq(AC.PRI)
        p.setPen(QPen(col, 1))
        p.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
        p.drawText(QRectF(0, sy, W, 16), Qt.AlignmentFlag.AlignCenter, txt)


class AssignmentWindow(QMainWindow):
    """Top-left agent window — Assignment Helper."""

    def __init__(self, on_command=None, status_callback=None, on_closed=None):
        super().__init__()
        self.setWindowTitle("✎ Assignment Helper — AI Academic Agent")
        self.setMinimumSize(400, 560)
        self.resize(420, 600)
        self.on_command       = on_command
        self._status_callback = status_callback
        self._on_closed_cb    = on_closed

        self.move(10, 20)

        # ── Voice engine (TTS out) ──
        self._voice = VoiceEngine(rate=180, voice_hint=None)
        self._voice.on_speech_start(lambda: self._set_speaking(True))
        self._voice.on_speech_end(lambda: self._set_speaking(False))
        self._voice_enabled = self._voice.available  # auto-speak toggle

        self._setup_ui()
        self._log("SYS: ASSIGNMENT HELPER AGENT ACTIVATED.")
        self._log("SYS: Ready for essays, research & academic support.")
        if not self._voice.available:
            self._log("SYS: Voice output unavailable — install pyttsx3.")
        self._set_link(True)

        self._clock_tmr = QTimer(self)
        self._clock_tmr.timeout.connect(self._tick_clock)
        self._clock_tmr.start(1000)
        self._tick_clock()

    # ── lifecycle ──────────────────────────────────────────────────
    def closeEvent(self, e: QCloseEvent):
        self._voice.shutdown()
        if self._on_closed_cb:
            try: self._on_closed_cb()
            except Exception: pass
        super().closeEvent(e)

    def _notify_status(self, active: bool):
        if self._status_callback:
            try: self._status_callback(active)
            except Exception: pass

    def _set_link(self, on: bool):
        col = AC.PRI if on else AC.TEXT_DIM
        txt = "● LINK ESTABLISHED" if on else "○ LINK IDLE"
        self._link_lbl.setText(txt)
        self._link_lbl.setStyleSheet(f"color: {col}; background: transparent;")

    def _set_speaking(self, val: bool):
        self._orb.speaking = val
        if not val:
            self._orb.state = "READY"

    # ── UI construction ────────────────────────────────────────────
    def _setup_ui(self):
        central = QWidget()
        central.setStyleSheet(f"background: {AC.BG};")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ──
        hdr = QWidget(); hdr.setFixedHeight(56)
        hdr.setStyleSheet(f"background: {AC.DARK}; border-bottom: 2px solid {AC.BORDER_B};")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(16, 6, 16, 4)
        title_col = QVBoxLayout(); title_col.setSpacing(1)
        t1 = QLabel("✎ ASSIGNMENT HELPER")
        t1.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        t1.setStyleSheet(f"color: {AC.PRI}; background: transparent; letter-spacing: 1px;")
        t2 = QLabel("AI ACADEMIC & RESEARCH CONSOLE")
        t2.setFont(QFont("Consolas", 7))
        t2.setStyleSheet(f"color: {AC.TEXT_DIM}; background: transparent;")
        title_col.addWidget(t1); title_col.addWidget(t2)
        hl.addLayout(title_col); hl.addStretch()
        self._clock_lbl = QLabel("00:00")
        self._clock_lbl.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        self._clock_lbl.setStyleSheet(f"color: {AC.PRI}; background: transparent;")
        hl.addWidget(self._clock_lbl)
        root.addWidget(hdr)

        # ── Status strip, including the subject selector + voice toggle ──
        strip = QWidget()
        strip.setStyleSheet(f"background: {AC.PANEL2}; border-bottom: 1px solid {AC.BORDER};")
        sl = QHBoxLayout(strip); sl.setContentsMargins(14, 5, 14, 5); sl.setSpacing(8)
        self._link_lbl = QLabel("○ LINK IDLE")
        self._link_lbl.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
        sl.addWidget(self._link_lbl)
        sl.addStretch()

        self._voice_btn = QPushButton("🔊 VOICE: ON" if self._voice_enabled else "🔇 VOICE: OFF")
        self._voice_btn.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
        self._voice_btn.setFixedHeight(20)
        self._voice_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._voice_btn.setCheckable(True)
        self._voice_btn.setChecked(self._voice_enabled)
        self._voice_btn.setEnabled(self._voice.available)
        self._style_voice_btn()
        self._voice_btn.clicked.connect(self._toggle_voice)
        sl.addWidget(self._voice_btn)

        subj_lbl = QLabel("SUBJECT:")
        subj_lbl.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
        subj_lbl.setStyleSheet(f"color: {AC.TEXT_DIM}; background: transparent;")
        sl.addWidget(subj_lbl)
        self._subject_combo = QComboBox()
        self._subject_combo.addItems([
            "General", "Mathematics", "Physics", "Chemistry",
            "Biology", "History", "Literature", "Computer Science",
            "Economics", "Philosophy", "Law", "Medicine"
        ])
        self._subject_combo.setFont(QFont("Consolas", 7))
        self._subject_combo.setFixedHeight(20)
        self._subject_combo.setStyleSheet(f"""
            QComboBox {{
                background: {AC.PANEL}; color: {AC.TEXT};
                border: 1px solid {AC.BORDER}; border-radius: 3px;
                padding: 1px 6px;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background: {AC.PANEL}; color: {AC.TEXT};
                border: 1px solid {AC.BORDER_B}; selection-background-color: {AC.PRI_GHO};
            }}
        """)
        sl.addWidget(self._subject_combo)
        root.addWidget(strip)

        # ── Centred orb, full width — the console's focal point ──
        orb_wrap = QWidget()
        orb_wrap.setFixedHeight(200)
        orb_wrap.setStyleSheet(f"background: {AC.BG}; border-bottom: 1px solid {AC.BORDER};")
        orb_lay = QHBoxLayout(orb_wrap); orb_lay.setContentsMargins(0, 0, 0, 0)
        self._orb = AssignmentOrbCanvas()
        self._orb.setStyleSheet(f"background: {AC.BG};")
        orb_lay.addWidget(self._orb)
        root.addWidget(orb_wrap)

        # ── Module readout strip — horizontal chip row beneath the orb ──
        mod_wrap = QWidget()
        mod_wrap.setStyleSheet(f"background: {AC.PANEL2}; border-bottom: 1px solid {AC.BORDER};")
        mod_outer = QVBoxLayout(mod_wrap); mod_outer.setContentsMargins(10, 6, 10, 8); mod_outer.setSpacing(4)
        cap_hdr = QLabel("▸ ACTIVE MODULES")
        cap_hdr.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
        cap_hdr.setStyleSheet(f"color: {AC.TEXT_DIM}; background: transparent;")
        mod_outer.addWidget(cap_hdr)

        grid = QGridLayout(); grid.setSpacing(5)
        caps = ["📝 Essay Structure", "🔍 Research Assist",
                "📐 Problem Solving", "📖 Summarisation",
                "🌐 Citations", "✔️ Proofreading", "🎙 Voice Input", "🔊 Voice Output"]
        for i, cap in enumerate(caps):
            l = QLabel(cap)
            l.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
            l.setStyleSheet(f"""
                color: {AC.ACC2}; background: {AC.PANEL};
                border: 1px solid {AC.BORDER}; border-radius: 3px; padding: 5px 6px;
            """)
            grid.addWidget(l, i // 3, i % 3)
        mod_outer.addLayout(grid)
        root.addWidget(mod_wrap)

        log_hdr = QLabel("  ▸ AGENT LOG")
        log_hdr.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
        log_hdr.setFixedHeight(20)
        log_hdr.setStyleSheet(f"color: {AC.TEXT_DIM}; background: {AC.DARK}; padding-left: 8px;")
        root.addWidget(log_hdr)
        self._log_w = AssignmentLogWidget()
        root.addWidget(self._log_w, stretch=2)

        # Quick prompt buttons
        quick = QWidget()
        quick.setStyleSheet(f"background: {AC.DARK}; border-top: 1px solid {AC.BORDER};")
        quick_lay = QHBoxLayout(quick); quick_lay.setContentsMargins(6, 4, 6, 4); quick_lay.setSpacing(4)
        for label, prompt in [("Summarise", "Summarise the following:"),
                               ("Essay Plan", "Create an essay plan for:"),
                               ("Cite Sources", "Find sources for:")]:
            btn = QPushButton(label)
            btn.setFixedHeight(24)
            btn.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {AC.PRI_GHO}; color: {AC.PRI};
                    border: 1px solid {AC.PRI_DIM}; border-radius: 4px; padding: 1px 6px;
                }}
                QPushButton:hover {{ background: {AC.PRI_DIM}; }}
            """)
            btn.clicked.connect(lambda _, pp=prompt: self._quick_fill(pp))
            quick_lay.addWidget(btn)
        root.addWidget(quick)

        # ── Input ──
        inp_w = QWidget()
        inp_w.setStyleSheet(f"background: {AC.DARK}; border-top: 1px solid {AC.BORDER};")
        inp_lay = QHBoxLayout(inp_w); inp_lay.setContentsMargins(8, 6, 8, 6); inp_lay.setSpacing(5)
        self._inp = QLineEdit()
        self._inp.setPlaceholderText("Ask Assignment Helper…")
        self._inp.setFont(QFont("Consolas", 8))
        self._inp.setFixedHeight(30)
        self._inp.setStyleSheet(f"""
            QLineEdit {{
                background: #10001a; color: {AC.WHITE};
                border: 1px solid {AC.BORDER}; border-radius: 4px; padding: 3px 8px;
            }}
            QLineEdit:focus {{ border: 1px solid {AC.PRI}; }}
        """)
        self._inp.returnPressed.connect(self._send)
        inp_lay.addWidget(self._inp)

        self._mic_btn = QPushButton("🎙")
        self._mic_btn.setFixedSize(30, 30)
        self._mic_btn.setFont(QFont("Consolas", 12))
        self._mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mic_btn.setToolTip("Speak your question")
        self._mic_btn.setEnabled(listen_once.__module__ is not None)
        self._mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: {AC.PANEL}; color: {AC.CYAN};
                border: 1px solid {AC.PRI_DIM}; border-radius: 4px;
            }}
            QPushButton:hover {{ background: {AC.PRI_GHO}; border: 1px solid {AC.CYAN}; }}
            QPushButton:disabled {{ color: {AC.TEXT_DIM}; }}
        """)
        self._mic_btn.clicked.connect(self._start_listening)
        inp_lay.addWidget(self._mic_btn)

        send = QPushButton("▸")
        send.setFixedSize(30, 30)
        send.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        send.setCursor(Qt.CursorShape.PointingHandCursor)
        send.setStyleSheet(f"""
            QPushButton {{
                background: {AC.PANEL}; color: {AC.PRI};
                border: 1px solid {AC.PRI_DIM}; border-radius: 4px;
            }}
            QPushButton:hover {{ background: {AC.PRI_GHO}; border: 1px solid {AC.PRI}; }}
        """)
        send.clicked.connect(self._send)
        inp_lay.addWidget(send)
        root.addWidget(inp_w)

    def _style_voice_btn(self):
        on = self._voice_btn.isChecked()
        col = AC.ACC if on else AC.TEXT_DIM
        bord = AC.PRI_DIM if on else AC.BORDER
        self._voice_btn.setStyleSheet(f"""
            QPushButton {{
                color: {col}; background: {AC.PANEL};
                border: 1px solid {bord}; border-radius: 3px; padding: 1px 8px;
            }}
            QPushButton:hover {{ background: {AC.PRI_GHO}; }}
        """)

    def _toggle_voice(self):
        self._voice_enabled = self._voice_btn.isChecked()
        self._voice_btn.setText("🔊 VOICE: ON" if self._voice_enabled else "🔇 VOICE: OFF")
        self._style_voice_btn()

    def _tick_clock(self):
        self._clock_lbl.setText(time.strftime("%H:%M"))

    def _log(self, text: str):
        self._log_w.append_log(text)

    def _quick_fill(self, prompt: str):
        self._inp.setText(prompt + " ")
        self._inp.setFocus()

    # ── Voice input ─────────────────────────────────────────────────
    def _start_listening(self):
        self._mic_btn.setEnabled(False)
        self._orb.listening = True
        self._orb.state = "LISTENING"
        self._log("SYS: Listening…")
        threading.Thread(target=self._listen_worker, daemon=True).start()

    def _listen_worker(self):
        try:
            text = listen_once()
            self._inp.setText(text)
            self._log(f"SYS: Heard — \"{text}\"")
        except RuntimeError as e:
            self._log(f"ERR: {e}")
        finally:
            self._orb.listening = False
            self._orb.state = "READY"
            self._mic_btn.setEnabled(True)

    # ── Send / receive ─────────────────────────────────────────────
    def _send(self):
        txt = self._inp.text().strip()
        if not txt:
            return
        self._inp.clear()
        subject = self._subject_combo.currentText()
        context_txt = f"[{subject}] {txt}" if subject != "General" else txt
        self._log(f"You: {txt}")
        self._orb.thinking = True
        self._orb.state = "ANALYSING"
        self._set_link(True)
        self._notify_status(True)
        if self.on_command:
            threading.Thread(target=self._run_command, args=(context_txt,), daemon=True).start()

    def _run_command(self, txt: str):
        try:
            result = self.on_command("assignment", txt)
            if result:
                self._log(f"Helper: {result}")
                if self._voice_enabled:
                    self._voice.speak(result)
        except Exception as e:
            self._log(f"ERR: {e}")
        finally:
            self._orb.thinking = False
            self._orb.state = "READY"
            self._notify_status(False)

    def write_response(self, text: str):
        self._log(f"Helper: {text}")
        self._orb.thinking = False
        self._orb.state = "READY"
        self._notify_status(False)
        if self._voice_enabled:
            self._voice.speak(text)

    def set_thinking(self, val: bool):
        self._orb.thinking = val
        self._orb.state = "ANALYSING" if val else "READY"
        self._notify_status(val)
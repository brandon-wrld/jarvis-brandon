"""
Microline Scientific Solutions Ltd — Specialist AI Agent Window
Opens in top-right of screen. Handles scientific, laboratory, research tasks.

v3.1 — Voice-enabled lab-console redesign:
  • Circuit-trace background instead of dot grid
  • Rotating "molecular ring" orb with LISTENING / SPEAKING / PROCESSING states
  • Slim top status strip (LINK / SIGNAL / CLEARANCE) for a console feel
  • Mic button for voice input (speech-to-text) beside the send button
  • Voice-output toggle — Microline replies are spoken aloud (text-to-speech)
  • Capability chips redrawn as data-readout tiles
  • Fully wired to MainWindow's status_callback / on_closed integration
"""
from __future__ import annotations
import time, threading
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QRectF
from PyQt6.QtGui import (
    QColor, QFont, QBrush, QPainter, QPen, QLinearGradient, QRadialGradient,
    QTextCursor, QCloseEvent
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFrame, QSizePolicy, QGridLayout
)
import math, random

from agent.voice_utils import VoiceEngine, listen_once

# ─── Colour Palette — deep lab-green / cyan console ───────────────────────
class MC:
    BG       = "#00100a"
    PANEL    = "#00170e"
    PANEL2   = "#001a10"
    BORDER   = "#0d3d26"
    BORDER_B = "#1fa066"
    PRI      = "#2bffa8"
    PRI_DIM  = "#0a6b46"
    PRI_GHO  = "#00251508"
    ACC      = "#5cffe6"
    ACC2     = "#7dffb0"
    TEXT     = "#b6ffdd"
    TEXT_DIM = "#3f8a68"
    WHITE    = "#e8fff4"
    DARK     = "#000c07"
    RED      = "#ff4d6d"
    YELLOW   = "#d7ff4d"
    AMBER    = "#ffb347"
    CYAN     = "#5cd9ff"

def mq(h: str, a: int = 255) -> QColor:
    c = QColor(h); c.setAlpha(a); return c


class MicrolineLogWidget(QTextEdit):
    _sig = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 9))
        self.setStyleSheet(f"""
            QTextEdit {{
                background: {MC.PANEL};
                color: {MC.TEXT};
                border: 1px solid {MC.BORDER};
                border-radius: 6px;
                padding: 8px;
            }}
            QScrollBar:vertical {{ background: {MC.BG}; width: 7px; border: none; }}
            QScrollBar::handle:vertical {{ background: {MC.BORDER_B}; border-radius: 3px; min-height: 16px; }}
        """)
        self._sig.connect(self._do_append)

    def append_log(self, text: str):
        self._sig.emit(text)

    def _do_append(self, text: str):
        cur = self.textCursor()
        tl = text.lower()
        if   "microline:" in tl: col = mq(MC.PRI)
        elif "you:" in tl:       col = mq(MC.WHITE)
        elif "err" in tl:        col = mq(MC.RED)
        elif "sys:" in tl:       col = mq(MC.YELLOW)
        else:                    col = mq(MC.TEXT)
        fmt = cur.charFormat()
        fmt.setForeground(QBrush(col))
        cur.movePosition(QTextCursor.MoveOperation.End)
        cur.insertText(text + "\n", fmt)
        self.setTextCursor(cur)
        self.ensureCursorVisible()


class MicrolineOrbCanvas(QWidget):
    """Futuristic molecular-ring HUD orb for the Microline agent."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(140, 140)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.state    = "READY"
        self.thinking = False
        self.listening = False
        self.speaking  = False
        self.linked   = False
        self._tick    = 0
        self._rings   = [0.0, 90.0, 180.0, 270.0]
        self._scan    = 0.0
        self._blink   = True
        self._blink_t = 0
        self._core    = 0.0
        self._nodes   = [random.uniform(0, 360) for _ in range(6)]
        self._pulses: list[float] = [0.0, 30.0]
        t = QTimer(self)
        t.timeout.connect(self._step)
        t.start(20)

    def _active(self) -> bool:
        return self.thinking or self.listening or self.speaking

    def _step(self):
        self._tick += 1
        spd = 2.0 if self._active() else 0.7
        for i in range(len(self._rings)):
            self._rings[i] = (self._rings[i] + spd * (1 + i * 0.3)) % 360
        for i in range(len(self._nodes)):
            self._nodes[i] = (self._nodes[i] + (0.9 if self._active() else 0.35)) % 360
        self._scan = (self._scan + (3.5 if self._active() else 1.2)) % 360
        self._core = (self._core + (4.0 if self._active() else 1.6)) % 360
        fw = min(self.width(), self.height())
        lim = fw * 0.6
        ps = 3.5 if self._active() else 1.5
        self._pulses = [r + ps for r in self._pulses if r + ps < lim]
        if len(self._pulses) < 3 and random.random() < (0.06 if self._active() else 0.02):
            self._pulses.append(0.0)
        self._blink_t += 1
        if self._blink_t >= 30:
            self._blink = not self._blink; self._blink_t = 0
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        cx, cy = W / 2, H / 2
        fw = min(W, H)
        p.fillRect(self.rect(), mq(MC.BG))

        # Circuit-trace backdrop
        p.setPen(QPen(mq(MC.PRI, 14), 1))
        step = 36
        for x in range(0, W, step):
            for y in range(0, H, step):
                p.drawLine(x, y, x + 10, y)
                p.drawLine(x, y, x, y + 10)

        core_col = MC.CYAN if self.listening else MC.ACC

        for pr in self._pulses:
            a = max(0, int(180 * (1.0 - pr / (fw * 0.6))))
            p.setPen(QPen(mq(core_col, a), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QRectF(cx-pr, cy-pr, pr*2, pr*2))

        for idx, (r_frac, arc_l, gap) in enumerate(
            [(0.42, 78, 58), (0.34, 52, 38), (0.26, 34, 26)]
        ):
            rr = fw * r_frac
            base = self._rings[idx]
            a = max(0, min(255, int(170 - idx * 30)))
            p.setPen(QPen(mq(MC.PRI, a), 1.6 - idx*0.3))
            p.setBrush(Qt.BrushStyle.NoBrush)
            rect = QRectF(cx-rr, cy-rr, rr*2, rr*2)
            angle = base
            while angle < base + 360:
                p.drawArc(rect, int(angle * 16), int(arc_l * 16))
                angle += arc_l + gap

        # Scanner sweep
        sr_ = fw * 0.46
        p.setPen(QPen(mq(core_col, 190), 1.5))
        srect = QRectF(cx-sr_, cy-sr_, sr_*2, sr_*2)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(srect, int(self._scan * 16), int(46 * 16))

        # Orbiting molecule nodes, connected to centre with faint bonds
        node_r = fw * 0.30
        pts = []
        for ang in self._nodes:
            rad = math.radians(ang)
            nx = cx + node_r * math.cos(rad)
            ny = cy + node_r * math.sin(rad) * 0.9
            pts.append((nx, ny))
        p.setPen(QPen(mq(MC.PRI, 45), 1))
        for nx, ny in pts:
            p.drawLine(int(cx), int(cy), int(nx), int(ny))
        for nx, ny in pts:
            p.setBrush(QBrush(mq(MC.ACC2, 210)))
            p.setPen(QPen(mq(MC.PRI, 160), 1))
            p.drawEllipse(QRectF(nx-3, ny-3, 6, 6))

        # Core orb with radial gradient + rotating inner ring
        orb_r = int(fw * 0.155)
        grad = QRadialGradient(cx, cy, orb_r)
        grad.setColorAt(0.0, mq(core_col, 235))
        grad.setColorAt(0.55, mq(MC.PRI_DIM, 220))
        grad.setColorAt(1.0, mq(MC.BG, 0))
        p.setBrush(QBrush(grad)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx-orb_r, cy-orb_r, orb_r*2, orb_r*2))
        p.setPen(QPen(mq(core_col, 200), 1.3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        inner = orb_r * 0.62
        p.drawArc(QRectF(cx-inner, cy-inner, inner*2, inner*2), int(self._core*16), int(120*16))
        p.drawArc(QRectF(cx-inner, cy-inner, inner*2, inner*2), int((self._core+180)*16), int(120*16))

        p.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        p.setPen(QPen(mq(MC.WHITE, 235), 1))
        p.drawText(QRectF(0, cy-9, W, 18), Qt.AlignmentFlag.AlignCenter, "ML")

        # Status
        sy = cy + fw * 0.40
        sym = "●" if self._blink else "○"
        if self.listening:
            txt, col = "🎙  LISTENING", mq(MC.CYAN)
        elif self.speaking:
            txt, col = "🔊  SPEAKING", mq(MC.ACC)
        elif self.thinking:
            txt, col = "◈  PROCESSING", mq(MC.YELLOW)
        else:
            txt, col = f"{sym}  {self.state}", mq(MC.PRI)
        p.setPen(QPen(col, 1))
        p.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
        p.drawText(QRectF(0, sy, W, 16), Qt.AlignmentFlag.AlignCenter, txt)


class MicrolineWindow(QMainWindow):
    """Top-right agent window — Microline Scientific Solutions Ltd."""

    def __init__(self, on_command=None, status_callback=None, on_closed=None):
        super().__init__()
        self.setWindowTitle("⬡ Microline Scientific Solutions — AI Agent")
        self.setMinimumSize(400, 560)
        self.resize(420, 600)
        self.on_command      = on_command
        self._status_callback = status_callback
        self._on_closed_cb    = on_closed

        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - 440, 20)

        # ── Voice engine (TTS out) ──
        self._voice = VoiceEngine(rate=175, voice_hint=None)
        self._voice.on_speech_start(lambda: self._set_speaking(True))
        self._voice.on_speech_end(lambda: self._set_speaking(False))
        self._voice_enabled = self._voice.available

        self._setup_ui()
        self._log("SYS: Microline Scientific Agent v3.1 online.")
        self._log("SYS: Specialised in lab, research & scientific analysis.")
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
        col = MC.PRI if on else MC.TEXT_DIM
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
        central.setStyleSheet(f"background: {MC.BG};")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ──
        hdr = QWidget(); hdr.setFixedHeight(52)
        hdr.setStyleSheet(f"background: {MC.DARK}; border-bottom: 2px solid {MC.BORDER_B};")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(14, 0, 14, 0)
        title_col = QVBoxLayout(); title_col.setSpacing(1)
        t1 = QLabel("⬡ MICROLINE SCIENTIFIC")
        t1.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        t1.setStyleSheet(f"color: {MC.PRI}; background: transparent; letter-spacing: 1px;")
        t2 = QLabel("SOLUTIONS LTD  ·  AI RESEARCH CONSOLE")
        t2.setFont(QFont("Consolas", 7))
        t2.setStyleSheet(f"color: {MC.TEXT_DIM}; background: transparent;")
        title_col.addWidget(t1); title_col.addWidget(t2)
        hl.addLayout(title_col); hl.addStretch()
        self._clock_lbl = QLabel("00:00")
        self._clock_lbl.setFont(QFont("Consolas", 13, QFont.Weight.Bold))
        self._clock_lbl.setStyleSheet(f"color: {MC.PRI}; background: transparent;")
        hl.addWidget(self._clock_lbl)
        root.addWidget(hdr)

        # ── Status strip ──
        strip = QWidget(); strip.setFixedHeight(24)
        strip.setStyleSheet(f"background: {MC.PANEL2}; border-bottom: 1px solid {MC.BORDER};")
        sl = QHBoxLayout(strip); sl.setContentsMargins(14, 0, 14, 0)
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
        sl.addSpacing(10)

        for txt, col in [("SIGNAL: STABLE", MC.ACC2), ("CLEARANCE: LVL-4", MC.TEXT_DIM)]:
            l = QLabel(txt); l.setFont(QFont("Consolas", 7))
            l.setStyleSheet(f"color: {col}; background: transparent;")
            sl.addWidget(l); sl.addSpacing(10)
        root.addWidget(strip)

        # ── Body: orb + capability tiles ──
        body = QHBoxLayout(); body.setContentsMargins(0, 0, 0, 0); body.setSpacing(0)

        self._orb = MicrolineOrbCanvas()
        self._orb.setFixedWidth(150)
        self._orb.setStyleSheet(f"background: {MC.BG};")
        body.addWidget(self._orb)

        rp = QWidget()
        rp.setStyleSheet(f"background: {MC.BG}; border-left: 1px solid {MC.BORDER};")
        rp_lay = QVBoxLayout(rp); rp_lay.setContentsMargins(10, 10, 10, 10); rp_lay.setSpacing(6)

        cap_hdr = QLabel("▸ ACTIVE MODULES")
        cap_hdr.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
        cap_hdr.setStyleSheet(f"color: {MC.TEXT_DIM}; background: transparent;")
        rp_lay.addWidget(cap_hdr)

        grid = QGridLayout(); grid.setSpacing(5)
        caps = ["🧬 Molecular Analysis", "🔬 Lab Protocol Design",
                "📊 Statistical Processing", "⚗️ Compound Research",
                "📡 Spectroscopy", "🧪 Experiment Design",
                "🎙 Voice Input", "🔊 Voice Output"]
        for i, cap in enumerate(caps):
            l = QLabel(cap)
            l.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
            l.setStyleSheet(f"""
                color: {MC.ACC2}; background: {MC.PANEL};
                border: 1px solid {MC.BORDER}; border-radius: 3px; padding: 5px 6px;
            """)
            grid.addWidget(l, i // 2, i % 2)
        rp_lay.addLayout(grid)
        rp_lay.addStretch()
        body.addWidget(rp, stretch=1)
        root.addLayout(body, stretch=1)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {MC.BORDER};")
        root.addWidget(sep)

        log_hdr = QLabel("  ▸ AGENT LOG")
        log_hdr.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
        log_hdr.setFixedHeight(20)
        log_hdr.setStyleSheet(f"color: {MC.TEXT_DIM}; background: {MC.DARK}; padding-left: 8px;")
        root.addWidget(log_hdr)
        self._log_w = MicrolineLogWidget()
        root.addWidget(self._log_w, stretch=2)

        # ── Input ──
        inp_w = QWidget()
        inp_w.setStyleSheet(f"background: {MC.DARK}; border-top: 1px solid {MC.BORDER};")
        inp_lay = QHBoxLayout(inp_w); inp_lay.setContentsMargins(8, 6, 8, 6); inp_lay.setSpacing(5)
        self._inp = QLineEdit()
        self._inp.setPlaceholderText("Query Microline Scientific…")
        self._inp.setFont(QFont("Consolas", 8))
        self._inp.setFixedHeight(30)
        self._inp.setStyleSheet(f"""
            QLineEdit {{
                background: #001008; color: {MC.WHITE};
                border: 1px solid {MC.BORDER}; border-radius: 4px; padding: 3px 8px;
            }}
            QLineEdit:focus {{ border: 1px solid {MC.PRI}; }}
        """)
        self._inp.returnPressed.connect(self._send)
        inp_lay.addWidget(self._inp)

        self._mic_btn = QPushButton("🎙")
        self._mic_btn.setFixedSize(30, 30)
        self._mic_btn.setFont(QFont("Consolas", 12))
        self._mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mic_btn.setToolTip("Speak your query")
        self._mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: {MC.PANEL}; color: {MC.CYAN};
                border: 1px solid {MC.PRI_DIM}; border-radius: 4px;
            }}
            QPushButton:hover {{ background: {MC.PRI_GHO}; border: 1px solid {MC.CYAN}; }}
            QPushButton:disabled {{ color: {MC.TEXT_DIM}; }}
        """)
        self._mic_btn.clicked.connect(self._start_listening)
        inp_lay.addWidget(self._mic_btn)

        send = QPushButton("▸")
        send.setFixedSize(30, 30)
        send.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        send.setCursor(Qt.CursorShape.PointingHandCursor)
        send.setStyleSheet(f"""
            QPushButton {{
                background: {MC.PANEL}; color: {MC.PRI};
                border: 1px solid {MC.PRI_DIM}; border-radius: 4px;
            }}
            QPushButton:hover {{ background: {MC.PRI_GHO}; border: 1px solid {MC.PRI}; }}
        """)
        send.clicked.connect(self._send)
        inp_lay.addWidget(send)
        root.addWidget(inp_w)

    def _style_voice_btn(self):
        on = self._voice_btn.isChecked()
        col = MC.ACC if on else MC.TEXT_DIM
        bord = MC.PRI_DIM if on else MC.BORDER
        self._voice_btn.setStyleSheet(f"""
            QPushButton {{
                color: {col}; background: {MC.PANEL};
                border: 1px solid {bord}; border-radius: 3px; padding: 1px 8px;
            }}
            QPushButton:hover {{ background: {MC.PRI_GHO}; }}
        """)

    def _toggle_voice(self):
        self._voice_enabled = self._voice_btn.isChecked()
        self._voice_btn.setText("🔊 VOICE: ON" if self._voice_enabled else "🔇 VOICE: OFF")
        self._style_voice_btn()

    def _tick_clock(self):
        self._clock_lbl.setText(time.strftime("%H:%M"))

    def _log(self, text: str):
        self._log_w.append_log(text)

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
        self._log(f"You: {txt}")
        self._orb.thinking = True
        self._orb.state = "PROCESSING"
        self._set_link(True)
        self._notify_status(True)
        if self.on_command:
            threading.Thread(target=self._run_command, args=(txt,), daemon=True).start()

    def _run_command(self, txt: str):
        try:
            result = self.on_command("microline", txt)
            if result:
                self._log(f"Microline: {result}")
                if self._voice_enabled:
                    self._voice.speak(result)
        except Exception as e:
            self._log(f"ERR: {e}")
        finally:
            self._orb.thinking = False
            self._orb.state = "READY"
            self._notify_status(False)

    def write_response(self, text: str):
        self._log(f"Microline: {text}")
        self._orb.thinking = False
        self._orb.state = "READY"
        self._notify_status(False)
        if self._voice_enabled:
            self._voice.speak(text)

    def set_thinking(self, val: bool):
        self._orb.thinking = val
        self._orb.state = "PROCESSING" if val else "READY"
        self._notify_status(val)
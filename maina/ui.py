from __future__ import annotations

import json
import math
import os
import platform
import random
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import psutil

from PyQt6.QtCore import (
    QEasingCurve, QMimeData, QObject, QPointF, QRectF, QSize, Qt,
    QTimer, QUrl, pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush, QColor, QDragEnterEvent, QDropEvent, QFont, QFontDatabase,
    QKeySequence, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap,
    QRadialGradient, QShortcut, QTextCursor, QTextCharFormat,
)
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QPushButton, QScrollArea, QSizePolicy, QTextEdit,
    QVBoxLayout, QWidget, QProgressBar, QTabWidget, QSplitter,
)

def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

BASE_DIR   = _base_dir()
CONFIG_DIR = BASE_DIR / "config"
API_FILE   = CONFIG_DIR / "api_keys.json"
CORE_PROMPT_FILE = BASE_DIR / "core" / "prompt.txt"


def _load_core_identity() -> str:
    """Loads the same core/prompt.txt used by the main JARVIS voice loop,
    so specialist agent windows (Microline, Assignment Helper, etc.)
    share one consistent personality/tone instead of drifting into their
    own separate voices."""
    try:
        return CORE_PROMPT_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        return (
            "IDENTITY: Efficient, professional, direct assistant. No fluff. "
            "Address the user as 'sir'. Be concise."
        )

_DEFAULT_W, _DEFAULT_H = 1100, 720
_MIN_W,     _MIN_H     = 880, 600
_LEFT_W  = 160
_RIGHT_W = 360

_OS = platform.system()

# Gemini model used for the agent windows (Microline / Assignment Helper)
_GEMINI_MODEL = "gemini-2.5-flash"

_MICROLINE_SOURCE_ROOTS = (
    "https://microlinescientific.com/",
    "https://microline-scientific-portal.netlify.app/",
)
_MICROLINE_SUPABASE_URL = "https://kspxztsupbbjevtgapus.supabase.co"
_MICROLINE_SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtzcHh6dHN1cGJiamV2dGdhcHVzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjcyODE0OTMsImV4cCI6MjA4Mjg1NzQ5M30."
    "EUl7WwJS_g686It26qMgYEdCij5fHrYIx4CQRVSuFos"
)
_microline_source_cache: tuple[float, str] | None = None
_microline_source_lock = threading.Lock()


def _microline_source_context(max_pages: int = 8) -> str:
    """Collect current public Microline pages for source-grounded answers."""
    global _microline_source_cache
    now = time.time()
    with _microline_source_lock:
        if _microline_source_cache and now - _microline_source_cache[0] < 900:
            return _microline_source_cache[1]

    try:
        import requests
        from bs4 import BeautifulSoup

        session = requests.Session()
        session.headers.update({"User-Agent": "JARVIS Microline Knowledge Agent/1.0"})
        pending = list(_MICROLINE_SOURCE_ROOTS)
        visited: set[str] = set()
        documents: list[str] = []
        allowed_hosts = {"microlinescientific.com", "microline-scientific-portal.netlify.app"}

        while pending and len(documents) < max_pages:
            url = pending.pop(0)
            if url in visited:
                continue
            visited.add(url)
            try:
                response = session.get(url, timeout=12)
                if response.status_code != 200 or "text/html" not in response.headers.get("content-type", ""):
                    continue
                soup = BeautifulSoup(response.text, "html.parser")
                for element in soup(["script", "style", "noscript", "svg"]):
                    element.decompose()
                text = " ".join(soup.get_text(" ").split())
                if text:
                    documents.append(f"SOURCE: {url}\n{text[:3500]}")
                for link in soup.find_all("a", href=True):
                    href = str(link["href"])
                    absolute = urljoin(url, href).split("#", 1)[0]
                    parsed = urlparse(absolute)
                    if parsed.scheme not in ("http", "https") or parsed.netloc not in allowed_hosts:
                        continue
                    if any(part in parsed.path.lower() for part in ("/auth", "/admin", "/login")):
                        continue
                    if absolute not in visited and absolute not in pending:
                        pending.append(absolute)
            except requests.RequestException:
                continue

        context = "\n\n".join(documents)
        context = _microline_portal_context(session, context)
    except ImportError:
        context = ""

    with _microline_source_lock:
        _microline_source_cache = (now, context)
    return context


def _microline_portal_context(session, context: str) -> str:
    """Add portal catalog and optional admin data to the source context."""
    import requests

    headers = {
        "apikey": _MICROLINE_SUPABASE_ANON_KEY,
        "Accept": "application/json",
    }
    access_token = ""
    email = os.environ.get("MICROLINE_PORTAL_EMAIL", "").strip()
    password = os.environ.get("MICROLINE_PORTAL_PASSWORD", "")
    if email and password:
        try:
            login = session.post(
                f"{_MICROLINE_SUPABASE_URL}/auth/v1/token?grant_type=password",
                headers={**headers, "Content-Type": "application/json"},
                json={"email": email, "password": password},
                timeout=12,
            )
            if login.ok:
                access_token = login.json().get("access_token", "")
        except requests.RequestException:
            pass

    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    tables = ["products"]
    if access_token:
        tables.extend(["inventory", "deliveries", "invoices", "sales", "clients"])

    documents = []
    for table in tables:
        try:
            response = session.get(
                f"{_MICROLINE_SUPABASE_URL}/rest/v1/{table}",
                headers=headers,
                params={"select": "*", "limit": "100"},
                timeout=12,
            )
            if response.ok:
                rows = response.json()
                if rows:
                    documents.append(f"PORTAL TABLE: {table}\n{json.dumps(rows, ensure_ascii=True)[:7000]}")
        except (requests.RequestException, ValueError):
            continue

    if documents:
        context = f"{context}\n\n" + "\n\n".join(documents)
    return context


# ═══════════════════════════════════════════════════════════════════
# COLOUR PALETTE — Iron Man HUD, deep space navy-to-black
# ═══════════════════════════════════════════════════════════════════
class C:
    BG        = "#00060a"
    PANEL     = "#010d14"
    PANEL2    = "#010f18"
    BORDER    = "#0d3347"
    BORDER_B  = "#1a5c7a"
    BORDER_A  = "#0f4060"
    PRI       = "#00d4ff"
    PRI_DIM   = "#007a99"
    PRI_GHO   = "#001f2e"
    ACC       = "#ff6b00"
    ACC2      = "#ffcc00"
    GREEN     = "#00ff88"
    GREEN_D   = "#00aa55"
    RED       = "#ff3355"
    MUTED_C   = "#ff3366"
    TEXT      = "#8ffcff"
    TEXT_DIM  = "#3a8a9a"
    TEXT_MED  = "#5ab8cc"
    WHITE     = "#d8f8ff"
    DARK      = "#000d14"
    BAR_BG    = "#011520"
    # Agent colours
    MICRO_PRI = "#00ff88"
    ASSIGN_PRI = "#cc88ff"


def qcol(h: str, a: int = 255) -> QColor:
    c = QColor(h); c.setAlpha(a); return c


# ═══════════════════════════════════════════════════════════════════
# SYSTEM METRICS (background thread)
# ═══════════════════════════════════════════════════════════════════
class _SysMetrics:
    def __init__(self):
        self.cpu = 0.0; self.mem = 0.0; self.net = 0.0
        self.gpu = -1.0; self.tmp = -1.0
        self._lock = threading.Lock()
        self._last_net = psutil.net_io_counters()
        self._last_net_t = time.time()
        self._running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self._running:
            try: self._update()
            except Exception: pass
            time.sleep(1.5)

    def _update(self):
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        nc  = psutil.net_io_counters()
        now = time.time(); dt = now - self._last_net_t
        if dt > 0:
            sent = (nc.bytes_sent - self._last_net.bytes_sent) / dt
            recv = (nc.bytes_recv - self._last_net.bytes_recv) / dt
            net  = (sent + recv) / (1024 * 1024)
        else:
            net = 0.0
        self._last_net = nc; self._last_net_t = now
        with self._lock:
            self.cpu = cpu; self.mem = mem; self.net = net
            self.gpu = self._get_gpu(); self.tmp = self._get_temp()

    def _get_gpu(self) -> float:
        try:
            r = subprocess.run(
                ["nvidia-smi","--query-gpu=utilization.gpu","--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=2)
            if r.returncode == 0:
                vals = [float(v.strip()) for v in r.stdout.strip().split("\n") if v.strip()]
                if vals: return sum(vals)/len(vals)
        except Exception: pass
        return -1.0

    def _get_temp(self) -> float:
        try:
            temps = psutil.sensors_temperatures()
            for name in ["coretemp","k10temp","cpu_thermal","acpitz","zenpower"]:
                if name in temps and temps[name]:
                    return temps[name][0].current
            for entries in temps.values():
                if entries: return entries[0].current
        except Exception: pass
        if _OS == "Windows":
            try:
                r = subprocess.run(
                    ["powershell","-Command",
                     "(Get-WmiObject MSAcpi_ThermalZoneTemperature -Namespace root/wmi).CurrentTemperature"],
                    capture_output=True, text=True, timeout=3)
                if r.returncode == 0 and r.stdout.strip():
                    raw = float(r.stdout.strip().split("\n")[0])
                    return (raw/10.0) - 273.15
            except Exception: pass
        return -1.0

    def snapshot(self) -> dict:
        with self._lock:
            return {"cpu":self.cpu,"mem":self.mem,"net":self.net,"gpu":self.gpu,"tmp":self.tmp}


_metrics = _SysMetrics()


# ═══════════════════════════════════════════════════════════════════
# HUD CANVAS — main animated Iron Man face / orb
# ═══════════════════════════════════════════════════════════════════
class HudCanvas(QWidget):
    def __init__(self, face_path: str, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.setMinimumSize(320, 320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.muted    = False
        self.speaking = False
        self.state    = "INITIALISING"

        self._tick       = 0
        self._scale      = 1.0
        self._tgt_scale  = 1.0
        self._halo       = 55.0
        self._tgt_halo   = 55.0
        self._last_t     = time.time()
        self._scan       = 0.0
        self._scan2      = 180.0
        self._rings      = [0.0, 120.0, 240.0]
        self._pulses: list[float] = [0.0, 50.0, 100.0]
        self._blink      = True
        self._blink_tick = 0
        self._particles: list[list[float]] = []
        self._hexagons: list[tuple] = []   # (x, y, r, alpha)
        self._face_px: QPixmap | None = None
        self._load_face(face_path)

        # Generate static hex grid decorations
        for _ in range(18):
            self._hexagons.append((
                random.uniform(0.05, 0.95),
                random.uniform(0.05, 0.95),
                random.uniform(8, 22),
                random.randint(15, 55)
            ))

        # Agent link state — reflects whether the Microline / Assignment
        # windows are actually open, instead of a hard-coded "LINKED".
        self.microline_linked = False
        self.assign_linked    = False

        self._tmr = QTimer(self)
        self._tmr.timeout.connect(self._step)
        self._tmr.start(16)

    def _load_face(self, path: str):
        try:
            from PIL import Image, ImageDraw
            import io
            img = Image.open(path).convert("RGBA")
            sz  = min(img.size)
            img = img.resize((sz, sz), Image.LANCZOS)
            mk  = Image.new("L", (sz, sz), 0)
            ImageDraw.Draw(mk).ellipse((2, 2, sz-2, sz-2), fill=255)
            img.putalpha(mk)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            px = QPixmap(); px.loadFromData(buf.getvalue())
            self._face_px = px
        except Exception:
            self._face_px = None

    def _step(self):
        self._tick += 1
        now = time.time()
        if now - self._last_t > (0.10 if self.speaking else 0.45):
            if self.speaking:
                self._tgt_scale = random.uniform(1.06, 1.16)
                self._tgt_halo  = random.uniform(150, 200)
            elif self.muted:
                self._tgt_scale = random.uniform(0.997, 1.002)
                self._tgt_halo  = random.uniform(12, 25)
            else:
                self._tgt_scale = random.uniform(1.001, 1.009)
                self._tgt_halo  = random.uniform(45, 70)
            self._last_t = now

        sp = 0.40 if self.speaking else 0.14
        self._scale += (self._tgt_scale - self._scale) * sp
        self._halo  += (self._tgt_halo  - self._halo)  * sp

        speeds = [1.4, -1.0, 2.2] if self.speaking else [0.55, -0.35, 0.92]
        for i, spd in enumerate(speeds):
            self._rings[i] = (self._rings[i] + spd) % 360

        self._scan  = (self._scan  + (3.2 if self.speaking else 1.3)) % 360
        self._scan2 = (self._scan2 + (-2.2 if self.speaking else -0.78)) % 360

        fw  = min(self.width(), self.height())
        lim = fw * 0.75
        spd = 4.5 if self.speaking else 2.1
        self._pulses = [r+spd for r in self._pulses if r+spd < lim]
        if len(self._pulses) < 4 and random.random() < (0.08 if self.speaking else 0.025):
            self._pulses.append(0.0)

        if self.speaking and random.random() < 0.30:
            cx, cy = self.width()/2, self.height()/2
            ang = random.uniform(0, 2*math.pi)
            r_s = fw * 0.28
            self._particles.append([
                cx + math.cos(ang)*r_s, cy + math.sin(ang)*r_s,
                math.cos(ang)*random.uniform(0.9, 2.6),
                math.sin(ang)*random.uniform(0.9, 2.6) - 0.4, 1.0,
            ])
        self._particles = [
            [p[0]+p[2], p[1]+p[3], p[2]*0.96, p[3]*0.96, p[4]-0.026]
            for p in self._particles if p[4] > 0
        ]

        self._blink_tick += 1
        if self._blink_tick >= 36:
            self._blink = not self._blink; self._blink_tick = 0
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), qcol(C.BG))

        W, H = self.width(), self.height()
        cx, cy = W/2, H/2
        fw = min(W, H)

        # Background hex grid
        p.setPen(QPen(qcol(C.PRI_GHO), 1))
        for x in range(0, W, 44):
            for y in range(0, H, 44):
                p.drawPoint(x, y)

        # Static hex decorations
        for hx, hy, hr, ha in self._hexagons:
            xx, yy = hx*W, hy*H
            col = qcol(C.PRI, ha)
            p.setPen(QPen(col, 0.7)); p.setBrush(Qt.BrushStyle.NoBrush)
            path = QPainterPath()
            for i in range(6):
                ang = math.radians(i*60)
                px2 = xx + hr * math.cos(ang)
                py2 = yy + hr * math.sin(ang)
                if i == 0: path.moveTo(px2, py2)
                else:       path.lineTo(px2, py2)
            path.closeSubpath()
            p.drawPath(path)

        r_face = fw * 0.31

        # Halo glow — multiple layers
        for i in range(12):
            r   = r_face * (1.9 - i*0.08)
            frc = 1.0 - i/12
            a   = max(0, min(255, int(self._halo * 0.090 * frc)))
            col = qcol(C.MUTED_C if self.muted else C.PRI, a)
            p.setPen(QPen(col, 1.5)); p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QRectF(cx-r, cy-r, r*2, r*2))

        # Pulse rings
        for pr in self._pulses:
            a   = max(0, int(240*(1.0 - pr/(fw*0.75))))
            col = qcol(C.MUTED_C if self.muted else C.PRI, a)
            p.setPen(QPen(col, 1.5)); p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QRectF(cx-pr, cy-pr, pr*2, pr*2))

        # Spinning arc rings — 4 levels now
        for idx, (r_frac, w_r, arc_l, gap) in enumerate(
            [(0.50, 3.0, 118, 80), (0.42, 2.0, 80, 56), (0.34, 1.5, 58, 42), (0.26, 1.0, 38, 28)]
        ):
            ring_r = fw * r_frac
            base   = self._rings[idx % 3]
            a_val  = max(0, min(255, int(self._halo*(1.0 - idx*0.16))))
            col    = qcol(C.MUTED_C if self.muted else C.PRI, a_val)
            p.setPen(QPen(col, w_r)); p.setBrush(Qt.BrushStyle.NoBrush)
            angle = base
            rect  = QRectF(cx-ring_r, cy-ring_r, ring_r*2, ring_r*2)
            while angle < base + 360:
                p.drawArc(rect, int(angle*16), int(arc_l*16))
                angle += arc_l + gap

        # Dual scanners
        sr = fw * 0.52
        sa = min(255, int(self._halo * 1.6))
        ex = 78 if self.speaking else 46
        p.setPen(QPen(qcol(C.MUTED_C if self.muted else C.PRI, sa), 2.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        srect = QRectF(cx-sr, cy-sr, sr*2, sr*2)
        p.drawArc(srect, int(self._scan*16), int(ex*16))
        p.setPen(QPen(qcol(C.ACC, sa//2), 1.5))
        p.drawArc(srect, int(self._scan2*16), int(ex*16))
        # Third counter-scanner
        sr2 = fw * 0.44
        p.setPen(QPen(qcol(C.ACC2, sa//3), 1.0))
        srect2 = QRectF(cx-sr2, cy-sr2, sr2*2, sr2*2)
        p.drawArc(srect2, int((self._scan+90)*16 % (360*16)), int(32*16))

        # Tick marks
        t_out, t_in = fw*0.510, fw*0.488
        p.setPen(QPen(qcol(C.PRI, 140), 1))
        for deg in range(0, 360, 10):
            rad = math.radians(deg)
            inn = t_in if deg % 30 == 0 else t_in+7
            p.drawLine(
                QPointF(cx + t_out*math.cos(rad), cy - t_out*math.sin(rad)),
                QPointF(cx + inn *math.cos(rad), cy - inn *math.sin(rad)),
            )

        # Crosshair
        ch_r, gap_h = fw*0.53, fw*0.17
        p.setPen(QPen(qcol(C.PRI, int(self._halo*0.55)), 1))
        p.drawLine(QPointF(cx-ch_r, cy), QPointF(cx-gap_h, cy))
        p.drawLine(QPointF(cx+gap_h, cy), QPointF(cx+ch_r, cy))
        p.drawLine(QPointF(cx, cy-ch_r), QPointF(cx, cy-gap_h))
        p.drawLine(QPointF(cx, cy+gap_h), QPointF(cx, cy+ch_r))

        # Corner brackets
        bl = 28
        bc = qcol(C.PRI, 220)
        hl2, hr2 = cx - fw//2, cx + fw//2
        ht, hb   = cy - fw//2, cy + fw//2
        p.setPen(QPen(bc, 2))
        for bx, by, dx, dy in [(hl2,ht,1,1),(hr2,ht,-1,1),(hl2,hb,1,-1),(hr2,hb,-1,-1)]:
            p.drawLine(QPointF(bx, by), QPointF(bx+dx*bl, by))
            p.drawLine(QPointF(bx, by), QPointF(bx, by+dy*bl))

        # Face / orb
        if self._face_px:
            fsz    = int(fw * 0.63 * self._scale)
            scaled = self._face_px.scaled(
                fsz, fsz,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            p.drawPixmap(int(cx-fsz/2), int(cy-fsz/2), scaled)
        else:
            orb_r = int(fw * 0.27 * self._scale)
            oc    = (200, 0, 50) if self.muted else (0, 60, 110)
            for i in range(8, 0, -1):
                r2  = int(orb_r * i/8)
                frc = i/8
                a   = max(0, min(255, int(self._halo*1.1*frc)))
                p.setBrush(QBrush(QColor(int(oc[0]*frc), int(oc[1]*frc), int(oc[2]*frc), a)))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QRectF(cx-r2, cy-r2, r2*2, r2*2))
            p.setPen(QPen(qcol(C.PRI, min(255, int(self._halo*2))), 1))
            p.setFont(QFont("Courier New", 14, QFont.Weight.Bold))
            p.drawText(QRectF(cx-90, cy-16, 180, 32), Qt.AlignmentFlag.AlignCenter, "J.A.R.V.I.S")

        # Particles
        for pt in self._particles:
            a = max(0, min(255, int(pt[4]*255)))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(qcol(C.PRI, a)))
            p.drawEllipse(QPointF(pt[0], pt[1]), 2.5, 2.5)

        # Status text
        sy = cy + fw * 0.42
        if self.muted:
            txt, col = "⊘  MUTED",     qcol(C.MUTED_C)
        elif self.speaking:
            txt, col = "●  SPEAKING",  qcol(C.ACC)
        elif self.state == "THINKING":
            sym = "◈" if self._blink else "◇"
            txt, col = f"{sym}  THINKING",   qcol(C.ACC2)
        elif self.state == "PROCESSING":
            sym = "▷" if self._blink else "▶"
            txt, col = f"{sym}  PROCESSING", qcol(C.ACC2)
        elif self.state == "LISTENING":
            sym = "●" if self._blink else "○"
            txt, col = f"{sym}  LISTENING",  qcol(C.GREEN)
        else:
            sym = "●" if self._blink else "○"
            txt, col = f"{sym}  {self.state}", qcol(C.PRI)
        p.setPen(QPen(col, 1))
        p.setFont(QFont("Courier New", 12, QFont.Weight.Bold))
        p.drawText(QRectF(0, sy, W, 28), Qt.AlignmentFlag.AlignCenter, txt)

        # Waveform
        wy = sy + 34
        N, bw = 40, 8
        wx0 = (W - N*bw) / 2
        for i in range(N):
            if self.muted:
                hgt, cl = 2, qcol(C.MUTED_C)
            elif self.speaking:
                hgt = random.randint(3, 22)
                cl  = qcol(C.PRI) if hgt > 13 else qcol(C.PRI_DIM)
            else:
                hgt = int(3 + 2*math.sin(self._tick*0.09 + i*0.6))
                cl  = qcol(C.BORDER_B)
            p.fillRect(QRectF(wx0+i*bw, wy+22-hgt, bw-1, hgt), cl)

        # Agent connection indicators (bottom corners) — now reflect the
        # real state of the Microline / Assignment windows.
        p.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
        micro_txt = "⬡ MICROLINE: LINKED" if self.microline_linked else "⬡ MICROLINE: IDLE"
        micro_col = C.MICRO_PRI if self.microline_linked else C.TEXT_DIM
        p.setPen(QPen(qcol(micro_col, 180 if self.microline_linked else 120), 1))
        p.drawText(QRectF(5, H-20, 130, 16), Qt.AlignmentFlag.AlignLeft, micro_txt)
        assign_txt = "✎ ASSIGN: LINKED" if self.assign_linked else "✎ ASSIGN: IDLE"
        assign_col = C.ASSIGN_PRI if self.assign_linked else C.TEXT_DIM
        p.setPen(QPen(qcol(assign_col, 180 if self.assign_linked else 120), 1))
        p.drawText(QRectF(W-155, H-20, 150, 16), Qt.AlignmentFlag.AlignRight, assign_txt)


# ═══════════════════════════════════════════════════════════════════
# METRIC BAR
# ═══════════════════════════════════════════════════════════════════
class MetricBar(QWidget):
    def __init__(self, label: str, color: str = C.PRI, parent=None):
        super().__init__(parent)
        self._label = label
        self._color = color
        self._value = 0.0
        self._text  = "--"
        self.setFixedHeight(38)
        self.setMinimumWidth(80)

    def set_value(self, pct: float, text: str):
        self._value = max(0.0, min(100.0, pct))
        self._text  = text
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        p.setBrush(QBrush(qcol(C.PANEL2)))
        p.setPen(QPen(qcol(C.BORDER_A), 1))
        p.drawRoundedRect(QRectF(1, 1, W-2, H-2), 4, 4)
        bar_h = 4; bar_y = H-bar_h-5; bar_w = W-12; bar_x = 6
        fill_w = int(bar_w * self._value / 100)
        p.setBrush(QBrush(qcol(C.BAR_BG))); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 2, 2)
        if self._value > 85:   bar_col = qcol(C.RED)
        elif self._value > 65: bar_col = qcol(C.ACC)
        else:                  bar_col = qcol(self._color)
        if fill_w > 0:
            p.setBrush(QBrush(bar_col))
            p.drawRoundedRect(QRectF(bar_x, bar_y, fill_w, bar_h), 2, 2)
        p.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
        p.setPen(QPen(qcol(C.TEXT_DIM), 1))
        p.drawText(QRectF(8, 5, 50, 14), Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter, self._label)
        p.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        p.setPen(QPen(bar_col if self._text != "--" else qcol(C.TEXT_DIM), 1))
        p.drawText(QRectF(0, 4, W-6, 16), Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter, self._text)


# ═══════════════════════════════════════════════════════════════════
# LOG WIDGET — typewriter effect
# ═══════════════════════════════════════════════════════════════════
class LogWidget(QTextEdit):
    _sig = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Courier New", 9))
        self.setStyleSheet(f"""
            QTextEdit {{
                background: {C.PANEL};
                color: {C.TEXT};
                border: 1px solid {C.BORDER};
                border-radius: 4px;
                padding: 6px;
                selection-background-color: {C.PRI_GHO};
            }}
            QScrollBar:vertical {{
                background: {C.BG}; width: 8px; border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {C.BORDER_B}; border-radius: 4px; min-height: 20px;
            }}
        """)
        self._queue: list[str] = []
        self._typing  = False
        self._text    = ""
        self._pos     = 0
        self._tag     = "sys"
        self._tmr = QTimer(self)
        self._tmr.timeout.connect(self._step)
        self._sig.connect(self._enqueue)

    def append_log(self, text: str):
        self._sig.emit(text)

    def _enqueue(self, text: str):
        self._queue.append(text)
        if not self._typing:
            self._next()

    def _next(self):
        if not self._queue:
            self._typing = False; return
        self._typing = True
        self._text   = self._queue.pop(0)
        self._pos    = 0
        tl = self._text.lower()
        if   tl.startswith("you:"):    self._tag = "you"
        elif tl.startswith("jarvis:"): self._tag = "ai"
        elif tl.startswith("file:"):   self._tag = "file"
        elif "err" in tl:              self._tag = "err"
        else:                          self._tag = "sys"
        self._tmr.start(5)

    def _step(self):
        if self._pos < len(self._text):
            ch  = self._text[self._pos]
            cur = self.textCursor()
            fmt = cur.charFormat()
            col = {
                "you":  qcol(C.WHITE),
                "ai":   qcol(C.PRI),
                "err":  qcol(C.RED),
                "file": qcol(C.GREEN),
                "sys":  qcol(C.ACC2),
            }.get(self._tag, qcol(C.TEXT))
            fmt.setForeground(QBrush(col))
            cur.movePosition(QTextCursor.MoveOperation.End)
            cur.insertText(ch, fmt)
            self.setTextCursor(cur)
            self.ensureCursorVisible()
            self._pos += 1
        else:
            self._tmr.stop()
            cur = self.textCursor()
            cur.movePosition(QTextCursor.MoveOperation.End)
            cur.insertText("\n")
            self.setTextCursor(cur)
            self.ensureCursorVisible()
            QTimer.singleShot(18, self._next)


# ═══════════════════════════════════════════════════════════════════
# FILE DROP ZONE
# ═══════════════════════════════════════════════════════════════════
_FILE_ICONS = {
    "image":   ("🖼", "#00d4ff"), "video":   ("🎬", "#ff6b00"),
    "audio":   ("🎵", "#cc44ff"), "pdf":     ("📄", "#ff4444"),
    "word":    ("📝", "#4488ff"), "excel":   ("📊", "#44bb44"),
    "code":    ("💻", "#ffcc00"), "archive": ("📦", "#ff8844"),
    "pptx":    ("📊", "#ff6622"), "text":    ("📃", "#aaaaaa"),
    "data":    ("🔧", "#88ddff"), "unknown": ("📎", "#888888"),
}
_EXT_TO_CAT = {
    **dict.fromkeys(["jpg","jpeg","png","gif","webp","bmp","tiff","svg","ico"], "image"),
    **dict.fromkeys(["mp4","avi","mov","mkv","wmv","flv","webm","m4v"],         "video"),
    **dict.fromkeys(["mp3","wav","ogg","m4a","aac","flac","wma","opus"],        "audio"),
    **dict.fromkeys(["pdf"],                                                    "pdf"),
    **dict.fromkeys(["doc","docx"],                                             "word"),
    **dict.fromkeys(["xls","xlsx","ods"],                                       "excel"),
    **dict.fromkeys(["ppt","pptx"],                                             "pptx"),
    **dict.fromkeys(["py","js","ts","jsx","tsx","html","css","java","c","cpp",
                     "cs","go","rs","rb","php","swift","kt","sh","sql","lua"],  "code"),
    **dict.fromkeys(["zip","rar","tar","gz","7z","bz2","xz"],                  "archive"),
    **dict.fromkeys(["txt","md","rst","log"],                                   "text"),
    **dict.fromkeys(["csv","tsv","json","xml"],                                 "data"),
}

def _file_category(path: Path) -> str:
    return _EXT_TO_CAT.get(path.suffix.lower().lstrip("."), "unknown")

def _fmt_size(size: int) -> str:
    if   size < 1024:    return f"{size} B"
    elif size < 1024**2: return f"{size/1024:.1f} KB"
    elif size < 1024**3: return f"{size/1024**2:.1f} MB"
    else:                return f"{size/1024**3:.1f} GB"


class FileDropZone(QWidget):
    file_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(100)
        self._current_file: str | None = None
        self._hovering  = False
        self._drag_over = False
        self._dash_offset = 0.0
        anim = QTimer(self)
        anim.timeout.connect(self._animate)
        anim.start(40)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._canvas = _DropCanvas(self)
        layout.addWidget(self._canvas)

    def _animate(self):
        self._dash_offset = (self._dash_offset + 0.8) % 20
        self._canvas.update()

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self._drag_over = True; self._canvas.update()

    def dragLeaveEvent(self, e):
        self._drag_over = False; self._canvas.update()

    def dropEvent(self, e: QDropEvent):
        self._drag_over = False
        urls = e.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if Path(path).is_file():
                self._set_file(path)
        self._canvas.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._browse()

    def enterEvent(self, e): self._hovering = True;  self._canvas.update()
    def leaveEvent(self, e): self._hovering = False; self._canvas.update()

    def current_file(self) -> str | None:
        return self._current_file

    def clear_file(self):
        self._current_file = None; self._canvas.update()

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select a file for JARVIS", str(Path.home()),
            "All Files (*.*);;"
            "Images (*.jpg *.jpeg *.png *.gif *.webp *.bmp *.svg);;"
            "Documents (*.pdf *.docx *.txt *.md *.pptx);;"
            "Data (*.csv *.xlsx *.json *.xml);;"
            "Code (*.py *.js *.ts *.html *.css *.java *.cpp *.go);;"
            "Audio (*.mp3 *.wav *.ogg *.m4a *.aac *.flac);;"
            "Video (*.mp4 *.avi *.mov *.mkv *.wmv *.webm);;"
            "Archives (*.zip *.rar *.tar *.gz *.7z)",
        )
        if path:
            self._set_file(path)

    def _set_file(self, path: str):
        self._current_file = path
        self._canvas.update()
        self.file_selected.emit(path)


class _DropCanvas(QWidget):
    def __init__(self, zone: FileDropZone):
        super().__init__(zone); self._z = zone

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        z = self._z
        W, H = self.width(), self.height()
        pad  = 6
        rect = QRectF(pad, pad, W-pad*2, H-pad*2)
        bg_col = qcol("#001a24" if z._drag_over else ("#001218" if z._hovering else C.PANEL))
        p.setBrush(QBrush(bg_col)); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, 6, 6)
        if z._current_file:  border_col = qcol(C.GREEN, 200)
        elif z._drag_over:   border_col = qcol(C.PRI, 230)
        elif z._hovering:    border_col = qcol(C.BORDER_B, 200)
        else:                border_col = qcol(C.BORDER, 160)
        pen = QPen(border_col, 1.5, Qt.PenStyle.DashLine)
        pen.setDashOffset(z._dash_offset)
        p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect, 6, 6)
        if z._current_file:  self._paint_file(p, W, H)
        elif z._drag_over:   self._paint_drag_over(p, W, H)
        else:                self._paint_idle(p, W, H, z._hovering)

    def _paint_idle(self, p, W, H, hover):
        cx, cy = W/2, H/2
        col = qcol(C.PRI_DIM if not hover else C.PRI)
        p.setPen(QPen(col, 2)); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawLine(QPointF(cx, cy-14), QPointF(cx, cy+4))
        p.drawLine(QPointF(cx-8, cy-6), QPointF(cx, cy-14))
        p.drawLine(QPointF(cx+8, cy-6), QPointF(cx, cy-14))
        p.drawLine(QPointF(cx-14, cy+4), QPointF(cx+14, cy+4))
        p.setFont(QFont("Courier New", 8))
        p.setPen(QPen(col if not hover else qcol(C.TEXT), 1))
        p.drawText(QRectF(0, cy+8, W, 16), Qt.AlignmentFlag.AlignCenter, "Drop file here  or  Click to Browse")
        p.setFont(QFont("Courier New", 7))
        p.setPen(QPen(qcol("#1a4a5a"), 1))
        p.drawText(QRectF(0, cy+24, W, 14), Qt.AlignmentFlag.AlignCenter,
                   "Images · Video · Audio · PDF · Docs · Code · Data")

    def _paint_drag_over(self, p, W, H):
        cx, cy = W/2, H/2
        p.setFont(QFont("Courier New", 20)); p.setPen(QPen(qcol(C.PRI), 1))
        p.drawText(QRectF(0, cy-24, W, 32), Qt.AlignmentFlag.AlignCenter, "⬇")
        p.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        p.drawText(QRectF(0, cy+12, W, 16), Qt.AlignmentFlag.AlignCenter, "Release to load")

    def _paint_file(self, p, W, H):
        path = Path(self._z._current_file)
        cat  = _file_category(path)
        icon, icon_col = _FILE_ICONS.get(cat, _FILE_ICONS["unknown"])
        size_str = _fmt_size(path.stat().st_size)
        ext_str  = path.suffix.upper().lstrip(".") or "FILE"
        bx, bw = 10, 60
        p.setFont(QFont("Segoe UI Emoji", 22) if _OS == "Windows" else QFont("Arial", 22))
        p.setPen(QPen(qcol(icon_col), 1))
        p.drawText(QRectF(bx, 0, bw, H), Qt.AlignmentFlag.AlignCenter, icon)
        tx, tw = bx+bw+6, W-bx-bw-6-38
        p.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        p.setPen(QPen(qcol(C.WHITE), 1))
        name = path.name if len(path.name) <= 34 else path.name[:31]+"..."
        p.drawText(QRectF(tx, H*0.18, tw, 16), Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter, name)
        p.setFont(QFont("Courier New", 7)); p.setPen(QPen(qcol(C.TEXT_DIM), 1))
        p.drawText(QRectF(tx, H*0.18+18, tw, 14), Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter, f"{ext_str}  ·  {size_str}")
        par = str(path.parent)
        if len(par) > 42: par = "…"+par[-41:]
        p.setFont(QFont("Courier New", 6)); p.setPen(QPen(qcol("#1e5c6a"), 1))
        p.drawText(QRectF(tx, H*0.18+34, tw, 12), Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter, par)
        p.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        p.setPen(QPen(qcol(C.RED, 180), 1))
        p.drawText(QRectF(W-34, 0, 28, H), Qt.AlignmentFlag.AlignCenter, "✕")

    def mousePressEvent(self, e):
        z = self._z
        if z._current_file and e.pos().x() > self.width()-34:
            z.clear_file()
        else:
            z.mousePressEvent(e)


# ═══════════════════════════════════════════════════════════════════
# AGENT STATUS WIDGET — shows linked agents in left panel
# ═══════════════════════════════════════════════════════════════════
class AgentStatusWidget(QWidget):
    launch_signal = pyqtSignal(str)  # agent_id

    def __init__(self, agent_id: str, name: str, color: str, icon: str, parent=None):
        super().__init__(parent)
        self._id = agent_id
        self._color = color
        self._active = False
        self.setFixedHeight(54)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(1)

        top = QHBoxLayout(); top.setSpacing(4)
        ico_lbl = QLabel(icon)
        ico_lbl.setFont(QFont("Courier New", 11))
        ico_lbl.setFixedWidth(22)
        ico_lbl.setStyleSheet(f"color: {color}; background: transparent;")
        top.addWidget(ico_lbl)
        name_lbl = QLabel(name)
        name_lbl.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color: {color}; background: transparent;")
        top.addWidget(name_lbl, stretch=1)
        lay.addLayout(top)

        self._status_lbl = QLabel("● ONLINE")
        self._status_lbl.setFont(QFont("Courier New", 7))
        self._status_lbl.setStyleSheet(f"color: {C.GREEN}; background: transparent;")
        lay.addWidget(self._status_lbl)

        launch_btn = QPushButton("↗ Open Window")
        launch_btn.setFixedHeight(18)
        launch_btn.setFont(QFont("Courier New", 7))
        launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        launch_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.PRI_GHO}; color: {color};
                border: 1px solid {color}33; border-radius: 2px; padding: 1px 4px;
            }}
            QPushButton:hover {{ background: {color}22; border: 1px solid {color}; }}
        """)
        launch_btn.clicked.connect(lambda: self.launch_signal.emit(self._id))
        lay.addWidget(launch_btn)

    def set_active(self, v: bool):
        self._active = v
        self._status_lbl.setText("● PROCESSING" if v else "● ONLINE")
        col = C.ACC2 if v else C.GREEN
        self._status_lbl.setStyleSheet(f"color: {col}; background: transparent;")


# ═══════════════════════════════════════════════════════════════════
# SETUP OVERLAY
# ═══════════════════════════════════════════════════════════════════
class SetupOverlay(QWidget):
    done = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            SetupOverlay {{
                background: rgba(0, 6, 10, 245);
                border: 1px solid {C.BORDER_B};
                border-radius: 8px;
            }}
        """)
        detected = {"darwin":"mac","windows":"windows"}.get(_OS.lower(), "linux")
        self._sel_os = detected
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(10)

        def _lbl(txt, font_size=9, bold=False, color=C.PRI, align=Qt.AlignmentFlag.AlignCenter):
            w = QLabel(txt); w.setAlignment(align)
            w.setFont(QFont("Courier New", font_size, QFont.Weight.Bold if bold else QFont.Weight.Normal))
            w.setStyleSheet(f"color: {color}; background: transparent;")
            return w

        layout.addWidget(_lbl("◈  INITIALISATION REQUIRED", 14, True))
        layout.addWidget(_lbl("Configure J.A.R.V.I.S. before first boot.", 9, color=C.PRI_DIM))
        layout.addSpacing(6)
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {C.BORDER};"); layout.addWidget(sep)
        layout.addSpacing(4)
        layout.addWidget(_lbl("GEMINI API KEY", 8, color=C.TEXT_DIM, align=Qt.AlignmentFlag.AlignLeft))
        self._key_input = QLineEdit()
        self._key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_input.setPlaceholderText("AIza…")
        self._key_input.setFont(QFont("Courier New", 10))
        self._key_input.setFixedHeight(34)
        self._key_input.setStyleSheet(f"""
            QLineEdit {{
                background: #000d12; color: {C.TEXT};
                border: 1px solid {C.BORDER}; border-radius: 4px; padding: 4px 8px;
            }}
            QLineEdit:focus {{ border: 1px solid {C.PRI}; }}
        """)
        layout.addWidget(self._key_input)
        layout.addSpacing(12)
        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color: {C.BORDER};"); layout.addWidget(sep2)
        layout.addSpacing(4)
        layout.addWidget(_lbl("OPERATING SYSTEM", 8, color=C.TEXT_DIM, align=Qt.AlignmentFlag.AlignLeft))
        det_name = {"windows":"Windows","mac":"macOS","linux":"Linux"}[detected]
        layout.addWidget(_lbl(f"Auto-detected: {det_name}", 8, color=C.ACC2, align=Qt.AlignmentFlag.AlignLeft))
        os_row = QHBoxLayout(); os_row.setSpacing(6)
        self._os_btns: dict[str, QPushButton] = {}
        for key, label in [("windows","⊞  Windows"),("mac","  macOS"),("linux","🐧  Linux")]:
            btn = QPushButton(label)
            btn.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
            btn.setFixedHeight(34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, k=key: self._sel(k))
            os_row.addWidget(btn); self._os_btns[key] = btn
        layout.addLayout(os_row)
        self._sel(detected)
        layout.addSpacing(14)
        init_btn = QPushButton("▸  INITIALISE ALL SYSTEMS")
        init_btn.setFont(QFont("Courier New", 11, QFont.Weight.Bold))
        init_btn.setFixedHeight(38)
        init_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        init_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {C.PRI};
                border: 1px solid {C.PRI_DIM}; border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {C.PRI_GHO}; border: 1px solid {C.PRI};
            }}
        """)
        init_btn.clicked.connect(self._submit)
        layout.addWidget(init_btn)

    def _sel(self, key: str):
        self._sel_os = key
        pal = {"windows":(C.PRI,"#001a22"),"mac":(C.ACC2,"#1a1400"),"linux":(C.GREEN,"#001a0d")}
        for k, btn in self._os_btns.items():
            if k == key:
                fg, bg = pal[k]
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {fg}; color: {bg};
                        border: none; border-radius: 4px; font-weight: bold;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: #000d12; color: {C.TEXT_DIM};
                        border: 1px solid {C.BORDER}; border-radius: 4px;
                    }}
                    QPushButton:hover {{ color: {C.TEXT}; border: 1px solid {C.BORDER_B}; }}
                """)

    def _submit(self):
        key = self._key_input.text().strip()
        if not key:
            self._key_input.setStyleSheet(f"""
                QLineEdit {{
                    background: #000d12; color: {C.TEXT};
                    border: 1px solid {C.RED}; border-radius: 4px; padding: 4px 8px;
                }}
            """)
            return
        self.done.emit(key, self._sel_os)


# ═══════════════════════════════════════════════════════════════════
# MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    _log_sig   = pyqtSignal(str)
    _state_sig = pyqtSignal(str)
    _agent_launch_sig = pyqtSignal(str)

    def __init__(self, face_path: str):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S — MARK XXXIX ULTRA")
        self.setMinimumSize(_MIN_W, _MIN_H)
        self.resize(_DEFAULT_W, _DEFAULT_H)

        screen = QApplication.primaryScreen().availableGeometry()
        # Centre window
        self.move(
            (screen.width()  - _DEFAULT_W) // 2,
            (screen.height() - _DEFAULT_H) // 2,
        )

        self.on_text_command = None
        self._muted          = False
        self._agent_mode     = False
        self._muted_before_agents = False
        self._current_file: str | None = None
        self._agent_windows: dict = {}
        self._agent_histories: dict[str, list[dict[str, object]]] = {}
        self._agent_history_lock = threading.Lock()

        central = QWidget()
        central.setStyleSheet(f"background: {C.BG};")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self._left_panel = self._build_left_panel()
        body.addWidget(self._left_panel, stretch=0)

        self.hud = HudCanvas(face_path)
        self.hud.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        body.addWidget(self.hud, stretch=5)

        self._right_panel = self._build_right_panel()
        body.addWidget(self._right_panel, stretch=0)

        root.addLayout(body, stretch=1)
        root.addWidget(self._build_footer())

        # Timers
        self._clock_tmr = QTimer(self)
        self._clock_tmr.timeout.connect(self._tick_clock)
        self._clock_tmr.start(1000); self._tick_clock()

        self._metric_tmr = QTimer(self)
        self._metric_tmr.timeout.connect(self._update_metrics)
        self._metric_tmr.start(2000); self._update_metrics()

        self._log_sig.connect(self._log.append_log)
        self._state_sig.connect(self._apply_state)
        self._agent_launch_sig.connect(self._launch_agent)

        self._overlay: SetupOverlay | None = None
        self._ready = self._check_config()
        if not self._ready:
            self._show_setup()

        QShortcut(QKeySequence("F4"), self).activated.connect(self._toggle_mute)
        QShortcut(QKeySequence("F11"), self).activated.connect(self._toggle_fullscreen)
        QShortcut(QKeySequence("F1"), self).activated.connect(lambda: self._launch_agent("microline"))
        QShortcut(QKeySequence("F2"), self).activated.connect(lambda: self._launch_agent("assignment"))

    def _toggle_fullscreen(self):
        if self.isFullScreen(): self.showNormal()
        else:                   self.showFullScreen()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._overlay and self._overlay.isVisible():
            ow, oh = 480, 420
            cw = self.centralWidget()
            self._overlay.setGeometry(
                (cw.width()-ow)//2, (cw.height()-oh)//2, ow, oh)

    def _build_header(self) -> QWidget:
        w = QWidget(); w.setFixedHeight(58)
        w.setStyleSheet(f"background: {C.DARK}; border-bottom: 2px solid {C.BORDER_B};")
        lay = QHBoxLayout(w); lay.setContentsMargins(16, 0, 16, 0)

        def _badge(txt, color=C.TEXT_MED):
            l = QLabel(txt); l.setFont(QFont("Courier New", 8))
            l.setStyleSheet(f"color: {color}; background: transparent;")
            return l

        left_col = QVBoxLayout(); left_col.setSpacing(1)
        left_col.addWidget(_badge("MARK XXXIX · ULTRA", C.PRI_DIM))
        left_col.addWidget(_badge("[F1] Microline  [F2] Assign", C.TEXT_DIM))
        lay.addLayout(left_col)
        lay.addStretch()

        mid = QVBoxLayout(); mid.setSpacing(1)
        title = QLabel("J.A.R.V.I.S")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Courier New", 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C.PRI}; background: transparent;")
        mid.addWidget(title)
        sub = QLabel("Just A Rather Very Intelligent System  ·  ULTRA EDITION")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setFont(QFont("Courier New", 7))
        sub.setStyleSheet(f"color: {C.PRI_DIM}; background: transparent;")
        mid.addWidget(sub)
        lay.addLayout(mid)
        lay.addStretch()

        right_col = QVBoxLayout(); right_col.setSpacing(2)
        self._clock_lbl = QLabel("00:00:00")
        self._clock_lbl.setFont(QFont("Courier New", 16, QFont.Weight.Bold))
        self._clock_lbl.setStyleSheet(f"color: {C.PRI}; background: transparent;")
        self._clock_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_col.addWidget(self._clock_lbl)
        self._date_lbl = QLabel("")
        self._date_lbl.setFont(QFont("Courier New", 7))
        self._date_lbl.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
        self._date_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_col.addWidget(self._date_lbl)
        lay.addLayout(right_col)
        return w

    def _tick_clock(self):
        self._clock_lbl.setText(time.strftime("%H:%M:%S"))
        self._date_lbl.setText(time.strftime("%a %d %b %Y"))

    def _build_left_panel(self) -> QWidget:
        w = QWidget(); w.setFixedWidth(_LEFT_W)
        w.setStyleSheet(f"background: {C.DARK}; border-right: 1px solid {C.BORDER};")
        lay = QVBoxLayout(w); lay.setContentsMargins(8, 10, 8, 10); lay.setSpacing(6)

        hdr = QLabel("◈ SYS MONITOR")
        hdr.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
        hdr.setStyleSheet(f"color: {C.PRI}; background: transparent; "
                          f"border-bottom: 1px solid {C.BORDER}; padding-bottom: 4px;")
        lay.addWidget(hdr)
        lay.addSpacing(2)

        self._bar_cpu = MetricBar("CPU", C.PRI)
        self._bar_mem = MetricBar("MEM", C.ACC2)
        self._bar_net = MetricBar("NET", C.GREEN)
        self._bar_gpu = MetricBar("GPU", C.ACC)
        self._bar_tmp = MetricBar("TMP", "#ff6688")
        for bar in [self._bar_cpu, self._bar_mem, self._bar_net, self._bar_gpu, self._bar_tmp]:
            lay.addWidget(bar)

        lay.addSpacing(4)
        info_panel = QWidget()
        info_panel.setStyleSheet(f"background: {C.PANEL2}; border: 1px solid {C.BORDER}; border-radius: 4px;")
        ip_lay = QVBoxLayout(info_panel); ip_lay.setContentsMargins(6,5,6,5); ip_lay.setSpacing(3)
        self._uptime_lbl = QLabel("UP  --:--")
        self._uptime_lbl.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        self._uptime_lbl.setStyleSheet(f"color: {C.GREEN}; background: transparent; border: none;")
        ip_lay.addWidget(self._uptime_lbl)
        self._proc_lbl = QLabel("PROC  --")
        self._proc_lbl.setFont(QFont("Courier New", 8))
        self._proc_lbl.setStyleSheet(f"color: {C.TEXT_MED}; background: transparent; border: none;")
        ip_lay.addWidget(self._proc_lbl)
        os_name = {"Windows":"WIN","Darwin":"macOS","Linux":"LINUX"}.get(_OS, _OS.upper())
        os_lbl = QLabel(f"OS  {os_name}")
        os_lbl.setFont(QFont("Courier New", 8))
        os_lbl.setStyleSheet(f"color: {C.ACC2}; background: transparent; border: none;")
        ip_lay.addWidget(os_lbl)
        lay.addWidget(info_panel)

        lay.addSpacing(6)
        # Agent status widgets
        agent_hdr = QLabel("◈ LINKED AGENTS")
        agent_hdr.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
        agent_hdr.setStyleSheet(f"color: {C.PRI}; background: transparent; "
                                f"border-bottom: 1px solid {C.BORDER}; padding-bottom: 4px;")
        lay.addWidget(agent_hdr)

        self._microline_status = AgentStatusWidget(
            "microline", "Microline Sci.", C.MICRO_PRI, "⬡")
        self._microline_status.launch_signal.connect(self._launch_agent)
        self._microline_status.setStyleSheet(
            f"background: {C.PANEL2}; border: 1px solid {C.BORDER}; border-radius: 3px; padding: 3px;")
        lay.addWidget(self._microline_status)

        self._assign_status = AgentStatusWidget(
            "assignment", "Assignment Hlp", C.ASSIGN_PRI, "✎")
        self._assign_status.launch_signal.connect(self._launch_agent)
        self._assign_status.setStyleSheet(
            f"background: {C.PANEL2}; border: 1px solid {C.BORDER}; border-radius: 3px; padding: 3px;")
        lay.addWidget(self._assign_status)

        lay.addStretch()

        for txt, col in [
            ("AI CORE\nACTIVE",   C.GREEN),
            ("SEC\nCLEARED",      C.PRI),
            ("PROTOCOL\nULTRA",   C.TEXT_DIM),
        ]:
            lbl = QLabel(txt)
            lbl.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                f"color: {col}; background: {C.PANEL2}; "
                f"border: 1px solid {C.BORDER_A}; border-radius: 3px; padding: 4px;"
            )
            lay.addWidget(lbl)
        return w

    def _build_right_panel(self) -> QWidget:
        w = QWidget(); w.setFixedWidth(_RIGHT_W)
        w.setStyleSheet(f"background: {C.DARK}; border-left: 1px solid {C.BORDER};")
        lay = QVBoxLayout(w); lay.setContentsMargins(8,8,8,8); lay.setSpacing(6)

        def _sec(txt):
            l = QLabel(f"▸ {txt}")
            l.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
            l.setStyleSheet(f"color: {C.TEXT_MED}; background: transparent;")
            return l

        lay.addWidget(_sec("ACTIVITY LOG"))
        self._log = LogWidget()
        lay.addWidget(self._log, stretch=1)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {C.BORDER}; margin: 2px 0;")
        lay.addWidget(sep)

        lay.addWidget(_sec("FILE UPLOAD"))
        self._drop_zone = FileDropZone()
        self._drop_zone.file_selected.connect(self._on_file_selected)
        lay.addWidget(self._drop_zone)

        self._file_hint = QLabel("No file loaded — drop or click above to upload")
        self._file_hint.setFont(QFont("Courier New", 7))
        self._file_hint.setStyleSheet(f"color: {C.TEXT_MED}; background: transparent;")
        self._file_hint.setWordWrap(True)
        lay.addWidget(self._file_hint)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color: {C.BORDER}; margin: 2px 0;")
        lay.addWidget(sep2)

        # Quick commands
        lay.addWidget(_sec("QUICK COMMANDS"))
        quick_grid = QHBoxLayout(); quick_grid.setSpacing(4)
        quick_cmds = [("🔊 Vol Up", "increase volume"),
                      ("🔇 Vol Down", "decrease volume"),
                      ("📸 Screen", "take a screenshot")]
        for label, cmd in quick_cmds:
            btn = QPushButton(label)
            btn.setFixedHeight(24)
            btn.setFont(QFont("Courier New", 7))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {C.PANEL}; color: {C.TEXT_MED};
                    border: 1px solid {C.BORDER}; border-radius: 3px; padding: 1px 4px;
                }}
                QPushButton:hover {{ color: {C.PRI}; border: 1px solid {C.BORDER_B}; }}
            """)
            cmd_copy = cmd
            btn.clicked.connect(lambda _, c=cmd_copy: self._quick_cmd(c))
            quick_grid.addWidget(btn)
        lay.addLayout(quick_grid)

        sep3 = QFrame(); sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setStyleSheet(f"color: {C.BORDER}; margin: 2px 0;")
        lay.addWidget(sep3)

        lay.addWidget(_sec("COMMAND INPUT"))
        lay.addLayout(self._build_input_row())

        self._mute_btn = QPushButton("🎙  MICROPHONE ACTIVE")
        self._mute_btn.setFixedHeight(32)
        self._mute_btn.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        self._mute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mute_btn.clicked.connect(self._toggle_mute)
        self._style_mute_btn()
        lay.addWidget(self._mute_btn)

        # Agent launch buttons
        lay.addWidget(_sec("AGENT WINDOWS"))
        agents_row = QHBoxLayout(); agents_row.setSpacing(4)
        ml_btn = QPushButton("⬡ Microline [F1]")
        ml_btn.setFixedHeight(28)
        ml_btn.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
        ml_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ml_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.PRI_GHO}; color: {C.MICRO_PRI};
                border: 1px solid {C.MICRO_PRI}44; border-radius: 3px;
            }}
            QPushButton:hover {{ background: {C.MICRO_PRI}22; border: 1px solid {C.MICRO_PRI}; }}
        """)
        ml_btn.clicked.connect(lambda: self._launch_agent("microline"))
        agents_row.addWidget(ml_btn)

        ah_btn = QPushButton("✎ Assign [F2]")
        ah_btn.setFixedHeight(28)
        ah_btn.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
        ah_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ah_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.PRI_GHO}; color: {C.ASSIGN_PRI};
                border: 1px solid {C.ASSIGN_PRI}44; border-radius: 3px;
            }}
            QPushButton:hover {{ background: {C.ASSIGN_PRI}22; border: 1px solid {C.ASSIGN_PRI}; }}
        """)
        ah_btn.clicked.connect(lambda: self._launch_agent("assignment"))
        agents_row.addWidget(ah_btn)
        lay.addLayout(agents_row)

        fs_btn = QPushButton("⛶  FULLSCREEN  [F11]")
        fs_btn.setFixedHeight(26)
        fs_btn.setFont(QFont("Courier New", 7))
        fs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fs_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {C.TEXT_MED};
                border: 1px solid {C.BORDER}; border-radius: 3px;
            }}
            QPushButton:hover {{ color: {C.PRI}; border: 1px solid {C.BORDER_B}; }}
        """)
        fs_btn.clicked.connect(self._toggle_fullscreen)
        lay.addWidget(fs_btn)
        return w

    def _build_input_row(self) -> QHBoxLayout:
        row = QHBoxLayout(); row.setSpacing(5)
        self._input = QLineEdit()
        self._input.setPlaceholderText("Type a command or question…")
        self._input.setFont(QFont("Courier New", 9))
        self._input.setFixedHeight(32)
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background: #000d14; color: {C.WHITE};
                border: 1px solid {C.BORDER}; border-radius: 4px; padding: 3px 8px;
            }}
            QLineEdit:focus {{ border: 1px solid {C.PRI}; }}
        """)
        self._input.returnPressed.connect(self._send)
        row.addWidget(self._input)
        send = QPushButton("▸")
        send.setFixedSize(32, 32)
        send.setFont(QFont("Courier New", 12, QFont.Weight.Bold))
        send.setCursor(Qt.CursorShape.PointingHandCursor)
        send.setStyleSheet(f"""
            QPushButton {{
                background: {C.PANEL}; color: {C.PRI};
                border: 1px solid {C.PRI_DIM}; border-radius: 4px;
            }}
            QPushButton:hover {{ background: {C.PRI_GHO}; border: 1px solid {C.PRI}; }}
        """)
        send.clicked.connect(self._send)
        row.addWidget(send)
        return row

    def _build_footer(self) -> QWidget:
        w = QWidget(); w.setFixedHeight(24)
        w.setStyleSheet(f"background: {C.DARK}; border-top: 1px solid {C.BORDER};")
        lay = QHBoxLayout(w); lay.setContentsMargins(14, 0, 14, 0)

        def _fl(txt, color=C.TEXT_MED):
            l = QLabel(txt); l.setFont(QFont("Courier New", 7))
            l.setStyleSheet(f"color: {color}; background: transparent;")
            return l

        lay.addWidget(_fl("[F4] Mute  ·  [F11] Fullscreen  ·  [F1] Microline  ·  [F2] Assignment"))
        lay.addStretch()
        lay.addWidget(_fl("MARK XXXIX ULTRA  ·  MULTI-AGENT SYSTEM  ·  CLASSIFIED"))
        lay.addStretch()
        lay.addWidget(_fl("© FATIHMAKES INDUSTRIES", C.PRI_DIM))
        return w

    def _launch_agent(self, agent_id: str):
        """Launch or bring-to-front an agent window, wired to the left
        panel's status indicator and the HUD's link badges."""
        from agents.microline_window import MicrolineWindow
        from agents.assignment_agent import AssignmentWindow

        if agent_id == "microline":
            if "microline" not in self._agent_windows or not self._agent_windows["microline"].isVisible():
                win = self._make_agent_window(
                    MicrolineWindow, "microline", self._microline_status)
                self._agent_windows["microline"] = win
                win.show()
                self._enter_agent_mode()
            else:
                self._agent_windows["microline"].raise_()
                self._agent_windows["microline"].activateWindow()

        elif agent_id == "assignment":
            if "assignment" not in self._agent_windows or not self._agent_windows["assignment"].isVisible():
                win = self._make_agent_window(
                    AssignmentWindow, "assignment", self._assign_status)
                self._agent_windows["assignment"] = win
                win.show()
                self._enter_agent_mode()
            else:
                self._agent_windows["assignment"].raise_()
                self._agent_windows["assignment"].activateWindow()

    def open_agent(self, agent_id: str):
        """Request an agent window from any worker thread."""
        self._agent_launch_sig.emit(agent_id)

    def _make_agent_window(self, window_cls, agent_id: str, status_widget: "AgentStatusWidget"):
        """Build an agent window, wiring status_callback/on_closed if the
        window class supports them (keeps this file compatible with
        older agent windows that don't accept those kwargs yet)."""
        kwargs = dict(on_command=self._agent_command_handler)
        try:
            win = window_cls(
                status_callback=lambda active, aid=agent_id: self._on_agent_status(aid, active),
                on_closed=lambda aid=agent_id: self._on_agent_closed(aid),
                **kwargs,
            )
        except TypeError:
            # Older agent window signature — fall back gracefully, the
            # left-panel status just won't reflect live processing state.
            win = window_cls(**kwargs)
        return win

    def _on_agent_status(self, agent_id: str, active: bool):
        """Real integration point: an agent window tells JARVIS it's
        processing, and JARVIS reflects that on the left panel + HUD."""
        widget = self._microline_status if agent_id == "microline" else self._assign_status
        widget.set_active(active)

    def _on_agent_closed(self, agent_id: str):
        """Keep the window registry and HUD link badges in sync when the
        user closes an agent window directly."""
        self._agent_windows.pop(agent_id, None)
        if agent_id == "microline":
            self.hud.microline_linked = False
        else:
            self.hud.assign_linked = False
        if not self._agent_windows:
            self._leave_agent_mode()

    def _enter_agent_mode(self):
        if self._agent_mode:
            return
        self._agent_mode = True
        self._muted_before_agents = self._muted
        if not self._muted:
            self._toggle_mute()
        self._log.append_log("SYS: Specialist agent active. Main microphone muted.")

    def _leave_agent_mode(self):
        if not self._agent_mode:
            return
        self._agent_mode = False
        if self._muted != self._muted_before_agents:
            self._toggle_mute()
        self._log.append_log("SYS: Specialist agent closed. Main microphone restored.")

    def _agent_command_handler(self, agent_id: str, text: str):
        """Route agent commands through the Gemini API."""
        import requests

        # First real message from an agent window means it's linked —
        # reflect that on the HUD's bottom-corner indicators.
        if agent_id == "microline":
            self.hud.microline_linked = True
        elif agent_id == "assignment":
            self.hud.assign_linked = True

        try:
            core_identity = _load_core_identity()

            if agent_id == "microline":
                specialty = (
                    "SPECIALTY: You are running as JARVIS's Microline Scientific Solutions module — "
                    "a laboratory science, molecular biology, chemistry, spectroscopy, and research-data "
                    "specialist. Give technically precise answers, using scientific notation where it helps. "
                    "You are still JARVIS: keep the same voice and brevity rules above, just applied to "
                    "scientific subject matter.\n\n"
                    "SOURCE POLICY: For Microline company, product, service, catalog, contact, and portal "
                    "questions, use only the supplied official Microline sources. Do not invent missing "
                    "prices, stock, specifications, policies, people, or capabilities. If the sources do "
                    "not contain an answer, say that clearly and recommend contacting Microline. "
                    "Write professional summaries with a short conclusion, organized sections, and source "
                    "URLs when relevant. Distinguish company information from general scientific knowledge.\n\n"
                    f"CURRENT OFFICIAL MICROLINE SOURCES:\n{_microline_source_context() or '(Sources temporarily unavailable.)'}"
                )
            elif agent_id == "assignment":
                specialty = (
                    "SPECIALTY: You are running as JARVIS's Assignment Helper module — an academic tutor "
                    "covering essays, research, citations, mathematics, and coursework. Be clear and "
                    "structured, and help the user actually learn the material rather than just handing "
                    "over answers. You are still JARVIS: keep the same voice and brevity rules above, just "
                    "applied to academic subject matter."
                )
            else:
                specialty = (
                    f"SPECIALTY: You are running as JARVIS's '{agent_id}' module. Stay in the same voice "
                    "and brevity rules above for this domain."
                )

            system = f"{core_identity}\n\n{specialty}"

            with self._agent_history_lock:
                history = self._agent_histories.setdefault(agent_id, [])
                history.append({"role": "user", "parts": [{"text": text}]})
                request_history = list(history[-12:])

            providers = [
                ("OpenRouter", self._request_openrouter),
                ("Gemini", self._request_gemini),
            ]
            failures = []
            for provider_name, request in providers:
                try:
                    answer = request(system, request_history, requests)
                    if answer:
                        with self._agent_history_lock:
                            self._agent_histories[agent_id].append(
                                {"role": "model", "parts": [{"text": answer}]}
                            )
                        return answer
                except Exception as provider_error:
                    failures.append(f"{provider_name}: {provider_error}")
            answer = self._offline_agent_response(agent_id, text, "; ".join(failures))
            with self._agent_history_lock:
                self._agent_histories[agent_id].append(
                    {"role": "model", "parts": [{"text": answer}]}
                )
            return answer
        except Exception as e:
            answer = self._offline_agent_response(agent_id, text, str(e))
            with self._agent_history_lock:
                self._agent_histories.setdefault(agent_id, []).append(
                    {"role": "model", "parts": [{"text": answer}]}
                )
            return answer

    def _request_openrouter(self, system: str, history: list[dict[str, object]], requests) -> str:
        api_key = self._get_api_key("openrouter_api_key", "OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("API key not configured")
        messages = [{"role": "system", "content": system}]
        for turn in history:
            parts = turn.get("parts", [])
            content = " ".join(str(part.get("text", "")) for part in parts if isinstance(part, dict))
            if content:
                role = "assistant" if turn.get("role") == "model" else str(turn.get("role", "user"))
                messages.append({"role": role, "content": content})
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://microlinescientific.com",
                "X-Title": "JARVIS Microline Agent",
            },
            json={"model": "openai/gpt-4o-mini", "messages": messages, "max_tokens": 1024},
            timeout=30,
        )
        if not response.ok:
            try:
                detail = response.json().get("error", {}).get("message", "")
            except (ValueError, TypeError):
                detail = ""
            suffix = f": {detail[:160]}" if detail else ""
            raise RuntimeError(f"HTTP {response.status_code}{suffix}")
        choices = response.json().get("choices", [])
        return str(choices[0].get("message", {}).get("content", "")).strip() if choices else ""

    def _request_gemini(self, system: str, history: list[dict[str, object]], requests) -> str:
        api_key = self._get_api_key("gemini_api_key", "GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("API key not configured")
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{_GEMINI_MODEL}:generateContent?key={api_key}",
            json={
                "system_instruction": {"parts": [{"text": system}]},
                "contents": history,
                "generationConfig": {"maxOutputTokens": 1024},
            },
            timeout=30,
        )
        if not response.ok:
            raise RuntimeError(f"HTTP {response.status_code}")
        candidates = response.json().get("candidates", [])
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        return "".join(str(part.get("text", "")) for part in parts).strip()

    def _offline_agent_response(self, agent_id: str, text: str, reason: str) -> str:
        """Keep the agent conversational when its hosted model is unavailable."""
        if agent_id == "microline":
            source = _microline_source_context(max_pages=4)
            source_note = "Official Microline sources are currently available." if source else "Official sources are temporarily unavailable."
            return (
                "I’m still connected, but my hosted reasoning service is temporarily unavailable "
                f"({reason}). {source_note} Please ask a Microline company, product, or portal question "
                "and I will continue with verified source material, or update the Gemini API quota/key "
                "for full scientific conversation."
            )
        return (
            "I’m still connected, but my hosted reasoning service is temporarily unavailable "
            f"({reason}). Your message has been received. Please restore the Gemini API quota/key "
            "to continue the full academic conversation."
        )

    def _get_api_key(self, config_name: str, env_name: str) -> str:
        """Get a provider key from config first, then the environment."""
        try:
            cfg = json.loads(API_FILE.read_text(encoding="utf-8"))
            return cfg.get(config_name, "") or os.environ.get(env_name, "")
        except Exception:
            return os.environ.get(env_name, "")

    def _get_gemini_key(self) -> str:
        return self._get_api_key("gemini_api_key", "GEMINI_API_KEY")

    def _quick_cmd(self, cmd: str):
        if self.on_text_command:
            self._log.append_log(f"You: {cmd}")
            threading.Thread(target=self.on_text_command, args=(cmd,), daemon=True).start()

    def _update_metrics(self):
        snap = _metrics.snapshot()
        cpu = snap["cpu"]
        self._bar_cpu.set_value(cpu, f"{cpu:.0f}%")
        mem = snap["mem"]
        self._bar_mem.set_value(mem, f"{mem:.0f}%")
        net = snap["net"]
        net_str = f"{net*1024:.0f}KB/s" if net < 1.0 else f"{net:.1f}MB/s"
        self._bar_net.set_value(min(100, net*10), net_str)
        gpu = snap["gpu"]
        if gpu >= 0: self._bar_gpu.set_value(gpu, f"{gpu:.0f}%")
        else:        self._bar_gpu.set_value(0, "N/A")
        tmp = snap["tmp"]
        if tmp >= 0:
            tmp_pct = min(100, (tmp/100)*100)
            self._bar_tmp.set_value(tmp_pct, f"{tmp:.0f}°C")
        else:
            self._bar_tmp.set_value(0, "N/A")
        try:
            elapsed = time.time() - psutil.boot_time()
            h = int(elapsed//3600); m = int((elapsed%3600)//60)
            self._uptime_lbl.setText(f"UP  {h:02d}:{m:02d}")
        except Exception:
            self._uptime_lbl.setText("UP  --:--")
        try:
            self._proc_lbl.setText(f"PROC  {len(psutil.pids())}")
        except Exception:
            self._proc_lbl.setText("PROC  --")

    def _on_file_selected(self, path: str):
        self._current_file = path
        p = Path(path)
        cat = _file_category(p)
        icon, _ = _FILE_ICONS.get(cat, _FILE_ICONS["unknown"])
        size = _fmt_size(p.stat().st_size)
        self._file_hint.setText(f"{icon}  {p.name}  ·  {size}  ·  Tell JARVIS what to do with it")
        self._log.append_log(f"FILE: {p.name} ({size}) loaded")
        if self.on_text_command:
            msg = (
                f"[FILE_UPLOADED] path={path} | name={p.name} | "
                f"type={p.suffix.lstrip('.')} | size={size} | "
                f"Briefly tell the user you can see the file '{p.name}' "
                f"({size}) has been uploaded and ask what they'd like to do with it."
            )
            threading.Thread(target=self.on_text_command, args=(msg,), daemon=True).start()

    def _toggle_mute(self):
        self._muted = not self._muted
        self.hud.muted = self._muted
        self._style_mute_btn()
        if self._muted:
            self._apply_state("MUTED")
            self._log.append_log("SYS: Microphone muted.")
        else:
            self._apply_state("LISTENING")
            self._log.append_log("SYS: Microphone active.")

    def _style_mute_btn(self):
        if self._muted:
            self._mute_btn.setText("🔇  MICROPHONE MUTED")
            self._mute_btn.setStyleSheet(f"""
                QPushButton {{
                    background: #140006; color: {C.MUTED_C};
                    border: 1px solid {C.MUTED_C}; border-radius: 3px;
                }}
            """)
        else:
            self._mute_btn.setText("🎙  MICROPHONE ACTIVE")
            self._mute_btn.setStyleSheet(f"""
                QPushButton {{
                    background: #00140a; color: {C.GREEN};
                    border: 1px solid {C.GREEN}; border-radius: 3px;
                }}
                QPushButton:hover {{ background: #001f10; }}
            """)

    def _send(self):
        txt = self._input.text().strip()
        if not txt: return
        self._input.clear()
        self._log.append_log(f"You: {txt}")
        if self.on_text_command:
            threading.Thread(target=self.on_text_command, args=(txt,), daemon=True).start()

    def _apply_state(self, state: str):
        self.hud.state    = state
        self.hud.speaking = (state == "SPEAKING")

    def _check_config(self) -> bool:
        if not API_FILE.exists(): return False
        try:
            d = json.loads(API_FILE.read_text(encoding="utf-8"))
            return bool(d.get("gemini_api_key")) and bool(d.get("os_system"))
        except Exception:
            return False

    def _show_setup(self):
        ov = SetupOverlay(self.centralWidget())
        cw = self.centralWidget()
        ow, oh = 480, 420
        ov.setGeometry((cw.width()-ow)//2, (cw.height()-oh)//2, ow, oh)
        ov.done.connect(self._on_setup_done)
        ov.show()
        self._overlay = ov

    def _on_setup_done(self, key: str, os_name: str):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        API_FILE.write_text(
            json.dumps({"gemini_api_key": key, "os_system": os_name}, indent=4),
            encoding="utf-8")
        self._ready = True
        if self._overlay:
            self._overlay.hide(); self._overlay = None
        self._apply_state("LISTENING")
        self._log.append_log(f"SYS: Initialised. OS={os_name.upper()}. JARVIS ULTRA online.")
        self._log.append_log("SYS: Press F1 for Microline  ·  F2 for Assignment Helper")


# ═══════════════════════════════════════════════════════════════════
# PUBLIC API SHIM
# ═══════════════════════════════════════════════════════════════════
class _RootShim:
    def __init__(self, app: QApplication):
        self._app = app
    def mainloop(self):
        self._app.exec()
    def protocol(self, *_):
        pass


class JarvisUI:
    def __init__(self, face_path: str, size=None):
        self._app = QApplication.instance() or QApplication(sys.argv)
        self._app.setStyle("Fusion")
        self._win = MainWindow(face_path)
        self._win.show()
        self.root = _RootShim(self._app)

    @property
    def muted(self) -> bool:
        return self._win._muted

    @muted.setter
    def muted(self, v: bool):
        if v != self._win._muted:
            self._win._toggle_mute()

    @property
    def current_file(self) -> str | None:
        return self._win._drop_zone.current_file()

    @property
    def on_text_command(self):
        return self._win.on_text_command

    @on_text_command.setter
    def on_text_command(self, cb):
        self._win.on_text_command = cb

    def set_state(self, state: str):
        self._win._state_sig.emit(state)

    def write_log(self, text: str):
        self._win._log_sig.emit(text)

    def open_agent(self, agent_id: str):
        self._win.open_agent(agent_id)

    def wait_for_api_key(self):
        while not self._win._ready:
            time.sleep(0.1)

    def start_speaking(self):
        self.set_state("SPEAKING")

    def stop_speaking(self):
        if not self.muted:
            self.set_state("LISTENING")
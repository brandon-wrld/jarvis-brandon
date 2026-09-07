"""
voice_utils.py — Shared voice I/O layer for the AI agent windows.

Provides:
  • VoiceEngine  — text-to-speech playback (background thread, non-blocking)
  • listen_once  — one-shot speech-to-text capture (blocking, run in a thread)

Dependencies:
  pip install pyttsx3 SpeechRecognition pyaudio

Both agent windows import this module and stay UI-agnostic — this file has
no PyQt dependency, so it can be reused, tested, or swapped out independently.
"""
from __future__ import annotations
import threading
import queue

try:
    import pyttsx3
    _HAS_TTS = True
except ImportError:
    _HAS_TTS = False

try:
    import speech_recognition as sr
    _HAS_STT = True
except ImportError:
    _HAS_STT = False


class VoiceEngine:
    """
    Non-blocking text-to-speech engine.

    Runs pyttsx3 on a dedicated worker thread with a queue, so multiple
    `speak()` calls from UI callbacks never block or clash with each other.
    """

    def __init__(self, rate: int = 178, volume: float = 1.0, voice_hint: str | None = None):
        self.available = _HAS_TTS
        self._q: "queue.Queue[tuple[str, threading.Event | None]]" = queue.Queue()
        self._stop = False
        self._on_start = None
        self._on_end = None

        if not self.available:
            return

        self._rate = rate
        self._volume = volume
        self._voice_hint = voice_hint
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    # ── callbacks the UI can hook for orb animation state ──────────
    def on_speech_start(self, cb):
        self._on_start = cb

    def on_speech_end(self, cb):
        self._on_end = cb

    def _run(self):
        engine = pyttsx3.init()
        engine.setProperty("rate", self._rate)
        engine.setProperty("volume", self._volume)
        if self._voice_hint:
            for v in engine.getProperty("voices"):
                if self._voice_hint.lower() in (v.name or "").lower():
                    engine.setProperty("voice", v.id)
                    break
        while not self._stop:
            text, done_evt = self._q.get()
            if text is None:
                break
            try:
                if self._on_start:
                    self._on_start()
                engine.say(text)
                engine.runAndWait()
            except Exception:
                pass
            finally:
                if self._on_end:
                    self._on_end()
                if done_evt:
                    done_evt.set()

    def speak(self, text: str):
        """Queue text for speech. Returns immediately."""
        if not self.available or not text:
            return
        self._q.put((text, None))

    def shutdown(self):
        if not self.available:
            return
        self._stop = True
        self._q.put((None, None))


def listen_once(timeout: float = 5.0, phrase_time_limit: float = 12.0) -> str:
    """
    Blocking single-utterance capture from the default microphone.
    Call this from a worker thread — never from the Qt main thread.

    Returns the recognised text, or raises RuntimeError with a readable
    message on failure (no mic, timeout, unrecognised speech, etc).
    """
    if not _HAS_STT:
        raise RuntimeError("speech_recognition not installed")

    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.4)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
    except sr.WaitTimeoutError:
        raise RuntimeError("No speech detected")
    except OSError:
        raise RuntimeError("No microphone available")

    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        raise RuntimeError("Could not understand audio")
    except sr.RequestError as e:
        raise RuntimeError(f"Speech service error: {e}")

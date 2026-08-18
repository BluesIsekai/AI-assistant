from __future__ import annotations

import json
import os
import subprocess
import threading
import queue
from pathlib import Path
from typing import Iterator


class CrispASRListener:
    """Continuous microphone listener using CrispASR structured streaming JSON."""

    def __init__(
        self,
        crispasr_exe: str,
        model_path: str,
        backend: str = "parakeet",
        language: str = "en",
        stream_step_ms: int = 400,
        stream_keep_ms: int = 800,
    ) -> None:
        self.crispasr_exe = str(Path(crispasr_exe))
        self.model_path = str(Path(model_path))
        self.backend = backend
        self.language = language
        self.stream_step_ms = stream_step_ms
        self.stream_keep_ms = stream_keep_ms

        self._process: subprocess.Popen[str] | None = None
        self._thread: threading.Thread | None = None
        self._events: queue.Queue[str] = queue.Queue()
        self._stop = threading.Event()
        self._paused = threading.Event()

    def start(self) -> None:
        if self._process is not None and self._process.poll() is None:
            return

        if not Path(self.crispasr_exe).exists():
            raise FileNotFoundError(f"CrispASR executable not found: {self.crispasr_exe}")

        if not Path(self.model_path).exists():
            raise FileNotFoundError(f"STT model not found: {self.model_path}")

        self._stop.clear()
        self._paused.clear()

        cmd = [
            self.crispasr_exe,
            "--backend", self.backend,
            "-m", self.model_path,
            "--mic",
            "--live",
            "--stream-json",
            "--vad",
            "--no-gpu",
            "-l", self.language,
            "--stream-step", str(self.stream_step_ms),
            "--stream-keep", str(self.stream_keep_ms),
        ]

        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        self._process = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=creationflags,
        )

        self._thread = threading.Thread(
            target=self._read_output,
            name="crispasr-stt-reader",
            daemon=True,
        )
        self._thread.start()

    def _read_output(self) -> None:
        assert self._process is not None
        assert self._process.stdout is not None

        for raw_line in self._process.stdout:
            if self._stop.is_set():
                break

            line = raw_line.strip()
            if not line:
                continue

            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                # Older/non-JSON output is intentionally ignored. The voice
                # layer expects structured streaming from current CrispASR.
                continue

            if event.get("type") != "final":
                continue

            text = str(event.get("text", "")).strip()
            if not text or self._paused.is_set():
                continue

            self._events.put(text)

    def pause(self) -> None:
        """Ignore transcripts while the assistant is speaking."""
        self._paused.set()
        self._drain_events()

    def resume(self) -> None:
        """Resume accepting transcripts after TTS playback."""
        self._drain_events()
        self._paused.clear()

    def _drain_events(self) -> None:
        while True:
            try:
                self._events.get_nowait()
            except queue.Empty:
                return

    def listen(self, timeout: float | None = None) -> str | None:
        """Wait for the next finalized utterance."""
        try:
            return self._events.get(timeout=timeout)
        except queue.Empty:
            return None

    def __iter__(self) -> Iterator[str]:
        self.start()
        while not self._stop.is_set():
            text = self.listen(timeout=0.5)
            if text:
                yield text

    def stop(self) -> None:
        self._stop.set()

        process = self._process
        self._process = None

        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)

        self._drain_events()

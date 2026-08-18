from __future__ import annotations

import json
import socket
import struct
import subprocess
import threading
import time
import urllib.request
import urllib.error
import winsound
from pathlib import Path


class CrispASRTTS:
    """Persistent Qwen3-TTS server + Windows WAV playback."""

    def __init__(
        self,
        crispasr_exe: str,
        model_path: str,
        codec_model_path: str,
        backend: str = "qwen3-tts-customvoice",
        voice: str = "Sohee",
        host: str = "127.0.0.1",
        port: int = 8765,
        output_path: str = "voice_output.wav",
    ) -> None:
        self.crispasr_exe = str(Path(crispasr_exe))
        self.model_path = str(Path(model_path))
        self.codec_model_path = str(Path(codec_model_path))
        self.backend = backend
        self.voice = voice
        self.host = host
        self.port = port
        self.output_path = Path(output_path)

        self._process: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self, timeout: float = 30.0) -> None:
        if self._is_port_open():
            return

        if not Path(self.crispasr_exe).exists():
            raise FileNotFoundError(
                f"CrispASR executable not found: {self.crispasr_exe}"
            )

        if not Path(self.model_path).exists():
            raise FileNotFoundError(
                f"TTS model not found: {self.model_path}"
            )

        if not Path(self.codec_model_path).exists():
            raise FileNotFoundError(
                f"TTS tokenizer/codec not found: {self.codec_model_path}"
            )

        cmd = [
            self.crispasr_exe,
            "--server",
            "--backend", self.backend,
            "-m", self.model_path,
            "--codec-model", self.codec_model_path,
            "--port", str(self.port),
        ]

        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        self._process = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            creationflags=creationflags,
        )

        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                raise RuntimeError(
                    f"CrispASR TTS server exited with code "
                    f"{self._process.returncode}."
                )

            if self._is_port_open():
                return

            time.sleep(0.1)

        self.stop()
        raise TimeoutError(
            "Timed out waiting for the CrispASR TTS server."
        )

    def _is_port_open(self) -> bool:
        with socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        ) as sock:
            sock.settimeout(0.15)
            return sock.connect_ex(
                (self.host, self.port)
            ) == 0

    def synthesize(self, text: str) -> Path:
        text = text.strip()

        if not text:
            raise ValueError("TTS text cannot be empty.")

        self.start()

        payload = json.dumps({
            "input": text,
            "voice": self.voice,
            "response_format": "wav",
        }).encode("utf-8")

        request = urllib.request.Request(
            f"{self.base_url}/v1/audio/speech",
            data=payload,
            headers={
                "Content-Type": "application/json"
            },
            method="POST",
        )

        with self._lock:
            try:
                with urllib.request.urlopen(
                    request,
                    timeout=60
                ) as response:
                    audio = response.read()

            except urllib.error.HTTPError as exc:
                body = exc.read().decode(
                    "utf-8",
                    errors="replace"
                )

                raise RuntimeError(
                    f"CrispASR TTS HTTP {exc.code}: {body}"
                ) from exc

            self.output_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            self.output_path.write_bytes(audio)

        return self.output_path

    def speak(self, text: str) -> None:
        wav = self.synthesize(text)

        winsound.PlaySound(
            str(wav),
            winsound.SND_FILENAME |
            winsound.SND_NODEFAULT,
        )

    def stop(self) -> None:
        process = self._process
        self._process = None

        if process is not None and process.poll() is None:
            process.terminate()

            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)


class ElevenLabsTTS:
    """ElevenLabs cloud TTS with WAV playback."""

    def __init__(
        self,
        api_key: str,
        voice_id: str,
        model: str = "eleven_flash_v2_5",
        output_path: str = "elevenlabs_output.wav",
    ) -> None:
        if not api_key:
            raise ValueError(
                "ELEVENLABS_API_KEY is not configured."
            )

        if not voice_id:
            raise ValueError(
                "ELEVENLABS_VOICE_ID is not configured."
            )

        self.api_key = api_key
        self.voice_id = voice_id
        self.model = model
        self.output_path = Path(output_path)

        self._lock = threading.Lock()

    def start(self) -> None:
        """No persistent local process is required."""

    def synthesize(self, text: str) -> Path:
        text = text.strip()

        if not text:
            raise ValueError("TTS text cannot be empty.")

        payload = json.dumps({
            "text": text,
            "model_id": self.model,
        }).encode("utf-8")

        url = (
            "https://api.elevenlabs.io/v1/text-to-speech/"
            f"{self.voice_id}"
            "?output_format=pcm_24000"
        )

        request = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "xi-api-key": self.api_key,
            },
            method="POST",
        )

        with self._lock:
            try:
                with urllib.request.urlopen(
                    request,
                    timeout=60
                ) as response:
                    pcm_audio = response.read()

            except urllib.error.HTTPError as exc:
                body = exc.read().decode(
                    "utf-8",
                    errors="replace"
                )

                raise RuntimeError(
                    f"ElevenLabs TTS HTTP {exc.code}: {body}"
                ) from exc

            self.output_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            self._write_wav(
                pcm_audio,
                self.output_path
            )

        return self.output_path

    @staticmethod
    def _write_wav(
        pcm_audio: bytes,
        output_path: Path,
    ) -> None:
        sample_rate = 24000
        channels = 1
        sample_width = 2

        byte_rate = (
            sample_rate *
            channels *
            sample_width
        )

        block_align = channels * sample_width

        with open(output_path, "wb") as wav:
            wav.write(b"RIFF")
            wav.write(
                struct.pack(
                    "<I",
                    36 + len(pcm_audio)
                )
            )
            wav.write(b"WAVE")

            wav.write(b"fmt ")
            wav.write(struct.pack("<I", 16))
            wav.write(struct.pack("<H", 1))
            wav.write(struct.pack("<H", channels))
            wav.write(struct.pack("<I", sample_rate))
            wav.write(struct.pack("<I", byte_rate))
            wav.write(struct.pack("<H", block_align))
            wav.write(struct.pack("<H", sample_width * 8))

            wav.write(b"data")
            wav.write(
                struct.pack(
                    "<I",
                    len(pcm_audio)
                )
            )
            wav.write(pcm_audio)

    def speak(self, text: str) -> None:
        wav = self.synthesize(text)

        winsound.PlaySound(
            str(wav),
            winsound.SND_FILENAME |
            winsound.SND_NODEFAULT,
        )

    def stop(self) -> None:
        """No persistent process to stop."""


def create_tts(config):
    """
    Creates the configured TTS provider.

    ElevenLabs can optionally fall back to local CrispASR/Qwen3-TTS.
    """

    provider = getattr(
        config,
        "TTS_PROVIDER",
        "local"
    ).lower()

    if provider == "elevenlabs":
        try:
            print("🔊 TTS: ElevenLabs")

            return ElevenLabsTTS(
                api_key=config.ELEVENLABS_API_KEY,
                voice_id=config.ELEVENLABS_VOICE_ID,
                model=config.ELEVENLABS_MODEL,
                output_path=config.TTS_OUTPUT_PATH,
            )

        except Exception as exc:
            if not getattr(
                config,
                "TTS_FALLBACK_TO_LOCAL",
                True
            ):
                raise

            print(
                f"⚠️ ElevenLabs unavailable: {exc}"
            )
            print("🔊 TTS: Falling back to local Qwen3-TTS")

    elif provider != "local":
        print(
            f"⚠️ Unknown TTS provider '{provider}'. "
            "Using local TTS."
        )

    return CrispASRTTS(
        crispasr_exe=config.CRISPASR_EXE,
        model_path=config.TTS_MODEL_PATH,
        codec_model_path=config.TTS_CODEC_MODEL_PATH,
        backend=config.TTS_BACKEND,
        voice=config.TTS_VOICE,
        host=config.TTS_SERVER_HOST,
        port=config.TTS_SERVER_PORT,
        output_path=config.TTS_OUTPUT_PATH,
    )
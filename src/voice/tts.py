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


import re

def clean_for_tts(text: str) -> str:
    text = re.sub(r"\*+", "", text)
    text = re.sub(r"_+", "", text)
    text = re.sub(r"`+", "", text)
    return text.strip()

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
            "voice": "D:\\AI\\voice_dataset\\...\\0014.wav",
            "ref_text": "...",
            "consent_attestation": "..."
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
            text = clean_for_tts(text)
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


class CrispASRCosyVoice3TTS:
    """Persistent CosyVoice3 TTS using a baked GGUF voice pack."""

    def __init__(
        self,
        crispasr_exe: str,
        model_path: str,
        flow_model_path: str,
        hift_model_path: str,
        voice_model_path: str,
        voice: str = "yuna",
        backend: str = "cosyvoice3-tts",
        host: str = "127.0.0.1",
        port: int = 8765,
        output_path: str = "voice_output.wav",
        source_language: str = "en",
        target_language: str = "en",
        no_spoken_disclaimer: bool = True,
    ) -> None:

        self.crispasr_exe = str(Path(crispasr_exe))
        self.model_path = str(Path(model_path))
        self.flow_model_path = str(Path(flow_model_path))
        self.hift_model_path = str(Path(hift_model_path))
        self.voice_model_path = str(Path(voice_model_path))

        self.voice = voice
        self.backend = backend

        self.host = host
        self.port = port

        self.output_path = Path(output_path)

        self.source_language = source_language
        self.target_language = target_language

        self.no_spoken_disclaimer = no_spoken_disclaimer

        self._process: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def _is_port_open(self) -> bool:
        with socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        ) as sock:

            sock.settimeout(0.15)

            return (
                sock.connect_ex(
                    (self.host, self.port)
                ) == 0
            )

    def start(self, timeout: float = 60.0) -> None:

        if self._is_port_open():
            return

        required_files = {
            "CrispASR executable": self.crispasr_exe,
            "CosyVoice3 LLM": self.model_path,
            "CosyVoice3 Flow": self.flow_model_path,
            "CosyVoice3 HiFT": self.hift_model_path,
            "CosyVoice3 voice pack": self.voice_model_path,
        }

        for description, path in required_files.items():

            if not Path(path).exists():

                raise FileNotFoundError(
                    f"{description} not found: {path}"
                )

        cmd = [
            self.crispasr_exe,

            "--server",

            "--backend",
            self.backend,

            "-m",
            self.model_path,

            "--codec-model",
            self.flow_model_path,

            "--voice-dir",
            str(Path(self.voice_model_path).parent),

            "--port",
            str(self.port),

            "--gpu-backend",
            "cuda",
        ]

        if self.no_spoken_disclaimer:

            cmd.extend([
                "--no-spoken-disclaimer",
                "--accept-marking-responsibility",
            ])

        creationflags = getattr(
            subprocess,
            "CREATE_NO_WINDOW",
            0,
        )

        self._process = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=None,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creationflags,
        )

        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:

            if self._process.poll() is not None:

                stderr = ""

                if self._process.stderr:

                    try:
                        stderr = self._process.stderr.read()

                    except Exception:
                        pass

                raise RuntimeError(
                    "CrispASR CosyVoice3 server "
                    f"exited with code "
                    f"{self._process.returncode}.\n"
                    f"{stderr}"
                )

            if self._is_port_open():

                # Give the server a tiny moment to finish
                # registering the voice pack.
                time.sleep(0.2)

                return

            time.sleep(0.1)

        self.stop()

        raise TimeoutError(
            "Timed out waiting for the "
            "CrispASR CosyVoice3 server."
        )

    def synthesize(self, text: str) -> Path:

        text = text.strip()

        if not text:

            raise ValueError(
                "TTS text cannot be empty."
            )

        self.start()

        payload = {
            "model": Path(self.model_path).name,
            "input": text,
            "voice": self.voice,
            "response_format": "wav",
            "consent_attestation": (
                "I have the speaker's consent to use this voice, "
                "or this is my own voice."
            ),
            "spoken_disclaimer": False,
        }

        request = urllib.request.Request(
            f"{self.base_url}/v1/audio/speech",

            data=json.dumps(
                payload
            ).encode("utf-8"),

            headers={
                "Content-Type":
                    "application/json"
            },

            method="POST",
        )

        with self._lock:

            try:

                with urllib.request.urlopen(
                    request,
                    timeout=120,
                ) as response:

                    audio = response.read()

            except urllib.error.HTTPError as exc:

                body = exc.read().decode(
                    "utf-8",
                    errors="replace",
                )

                raise RuntimeError(
                    f"CosyVoice3 HTTP "
                    f"{exc.code}: {body}"
                ) from exc

            self.output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            self.output_path.write_bytes(
                audio
            )

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

        if (
            process is not None
            and process.poll() is None
        ):

            process.terminate()

            try:

                process.wait(
                    timeout=2
                )

            except subprocess.TimeoutExpired:

                process.kill()

                process.wait(
                    timeout=2
                )


def create_tts(config):

    provider = getattr(
        config,
        "TTS_PROVIDER",
        "cosyvoice3",
    ).lower()

    if provider == "cosyvoice3":

        print("🔊 TTS: CosyVoice3 SFT — baked Yuna voice")

        return CrispASRCosyVoice3TTS(
            crispasr_exe=config.CRISPASR_EXE,

            model_path=config.TTS_MODEL_PATH,

            flow_model_path=
                config.TTS_FLOW_MODEL_PATH,

            hift_model_path=
                config.TTS_HIFT_MODEL_PATH,

            voice_model_path=
                config.TTS_VOICE_MODEL_PATH,

            voice=config.TTS_VOICE,

            backend=config.TTS_BACKEND,

            host=config.TTS_SERVER_HOST,

            port=config.TTS_SERVER_PORT,

            output_path=config.TTS_OUTPUT_PATH,

            source_language=
                config.TTS_SOURCE_LANGUAGE,

            target_language=
                config.TTS_TARGET_LANGUAGE,

            no_spoken_disclaimer=
                config.TTS_NO_SPOKEN_DISCLAIMER,
        )

    # Keep your existing ElevenLabs/local providers below.
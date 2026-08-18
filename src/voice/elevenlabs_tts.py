from __future__ import annotations

import io
import threading

import winsound

from elevenlabs.client import ElevenLabs


class ElevenLabsTTS:
    """ElevenLabs cloud TTS with local playback."""

    def __init__(
        self,
        api_key: str,
        voice_id: str,
        model_id: str = "eleven_flash_v2_5",
    ) -> None:
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY is not configured.")

        if not voice_id:
            raise ValueError("ElevenLabs voice ID is not configured.")

        self.client = ElevenLabs(api_key=api_key)
        self.voice_id = voice_id
        self.model_id = model_id

        self._lock = threading.Lock()

    def start(self) -> None:
        """No persistent process is required for ElevenLabs."""
        pass

    def speak(self, text: str) -> None:
        text = text.strip()

        if not text:
            return

        with self._lock:
            audio = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                model_id=self.model_id,
                output_format="mp3_22050_32",
                text=text,
            )

            audio_bytes = b"".join(
                chunk for chunk in audio if chunk
            )

            # Save temporarily.
            path = "voice_elevenlabs.mp3"

            with open(path, "wb") as f:
                f.write(audio_bytes)

            # Windows doesn't reliably play MP3 with winsound,
            # so we'll replace this playback layer with a proper
            # audio player in the next step.
            raise RuntimeError(
                "ElevenLabs generation succeeded, "
                "but MP3 playback is not connected yet."
            )

    def stop(self) -> None:
        pass
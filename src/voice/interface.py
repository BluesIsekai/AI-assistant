from typing import Protocol

from .stt import CrispASRListener


class TTSProvider(Protocol):

    def start(self) -> None:
        ...

    def stop(self) -> None:
        ...

    def speak(self, text: str) -> None:
        ...


class VoiceInterface:
    """Desktop voice loop components."""

    def __init__(
        self,
        stt: CrispASRListener,
        tts: TTSProvider,
    ) -> None:
        self.stt = stt
        self.tts = tts

    def start(self) -> None:
        self.stt.start()
        self.tts.start()

    def stop(self) -> None:
        self.stt.stop()
        self.tts.stop()

    def listen(self, timeout: float | None = None) -> str | None:
        return self.stt.listen(timeout)

    def speak(self, text: str) -> None:
        self.stt.pause()

        try:
            self.tts.speak(text)
        finally:
            self.stt.resume()
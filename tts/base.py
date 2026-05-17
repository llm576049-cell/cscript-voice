from abc import ABC, abstractmethod


class TTSBackend(ABC):
    @abstractmethod
    def synthesize(self, text: str, ref_wav: str, instruct_text: str) -> bytes:
        """Return raw WAV bytes for the given text and voice/emotion parameters."""
        ...

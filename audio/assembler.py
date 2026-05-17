import io
from pathlib import Path
from pydub import AudioSegment

_PAUSE_LINE_MS = 400
_PAUSE_SCENE_MS = 1500


class AudioAssembler:
    def __init__(self):
        self._segments: list[AudioSegment] = []

    def add(self, wav_bytes: bytes, scene_break: bool = False) -> None:
        seg = AudioSegment.from_wav(io.BytesIO(wav_bytes))
        if self._segments:
            pause_ms = _PAUSE_SCENE_MS if scene_break else _PAUSE_LINE_MS
            self._segments.append(AudioSegment.silent(duration=pause_ms))
        self._segments.append(seg)

    def export(self, path: Path) -> None:
        if not self._segments:
            raise ValueError("No audio to export")
        combined: AudioSegment = sum(self._segments)  # type: ignore[arg-type]  # pydub __add__ concatenates
        fmt = path.suffix.lstrip(".") or "mp3"
        combined.export(str(path), format=fmt)
        duration_s = len(combined) / 1000
        print(f"Exported {duration_s:.1f}s → {path}")

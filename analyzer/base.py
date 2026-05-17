from abc import ABC, abstractmethod
from dataclasses import dataclass, field

EMOTIONS = frozenset(
    {"happy", "sad", "angry", "fearful", "tender", "surprised", "serious", "neutral"}
)
INTENSITIES = frozenset({"low", "medium", "high"})


@dataclass
class EmotionResult:
    emotion: str = "neutral"
    intensity: str = "medium"

    def __post_init__(self):
        if self.emotion not in EMOTIONS:
            self.emotion = "neutral"
        if self.intensity not in INTENSITIES:
            self.intensity = "medium"


class EmotionAnalyzer(ABC):
    @abstractmethod
    def analyze(
        self, text: str, context: list[str], scene: str | None
    ) -> EmotionResult: ...

    def analyze_batch(self, lines: list) -> list[EmotionResult]:
        results = []
        for i, line in enumerate(lines):
            context = [l.text for l in lines[max(0, i - 3) : i]]
            results.append(self.analyze(line.text, context, line.scene))
        return results

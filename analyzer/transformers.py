from .base import EmotionAnalyzer, EmotionResult

_LABEL_MAP = {
    "高兴": "happy",
    "悲伤": "sad",
    "愤怒": "angry",
    "恐惧": "fearful",
    "温柔": "tender",
    "惊讶": "surprised",
    "严肃": "serious",
    "平静": "neutral",
}
_LABELS_ZH = list(_LABEL_MAP.keys())


class TransformersAnalyzer(EmotionAnalyzer):
    def __init__(self, cfg: dict):
        self.model_name = cfg.get("model", "joeddav/xlm-roberta-large-xnli")
        self._classifier = None  # lazy: avoids importing transformers + ~1.1 GB download until first use

    def _get_classifier(self):
        if self._classifier is None:
            from transformers import pipeline

            print(f"Loading {self.model_name} (first run may download ~1.1 GB)…")
            self._classifier = pipeline(
                "zero-shot-classification",
                model=self.model_name,
                device=-1,
            )
        return self._classifier

    def analyze(
        self, text: str, context: list[str], scene: str | None
    ) -> EmotionResult:
        clf = self._get_classifier()
        result = clf(text, _LABELS_ZH, hypothesis_template="这句话表达了{}的情感。")
        top_label: str = result["labels"][0]
        top_score: float = result["scores"][0]
        emotion = _LABEL_MAP.get(top_label, "neutral")
        intensity = (
            "high" if top_score > 0.7 else ("low" if top_score < 0.4 else "medium")
        )
        return EmotionResult(emotion=emotion, intensity=intensity)

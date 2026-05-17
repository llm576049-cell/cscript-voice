import yaml
from pathlib import Path
from analyzer.base import EmotionResult

_EMOTION_INSTRUCT: dict[tuple[str, str], str] = {
    ("happy", "low"): "用轻松愉快的语气",
    ("happy", "medium"): "用开心喜悦的语气",
    ("happy", "high"): "用非常兴奋欢快的语气",
    ("sad", "low"): "用略带忧伤的语气",
    ("sad", "medium"): "用悲伤的语气",
    ("sad", "high"): "用极度悲痛、带着哭腔的语气",
    ("angry", "low"): "用略显不满的语气",
    ("angry", "medium"): "用愤怒的语气",
    ("angry", "high"): "用非常愤怒激动的语气",
    ("fearful", "low"): "用紧张不安的语气",
    ("fearful", "medium"): "用恐惧颤抖的语气",
    ("fearful", "high"): "用极度恐惧、声音颤抖的语气",
    ("tender", "low"): "用温柔的语气",
    ("tender", "medium"): "用深情温柔的语气",
    ("tender", "high"): "用极度温柔体贴的语气",
    ("serious", "low"): "用认真的语气",
    ("serious", "medium"): "用严肃正经的语气",
    ("serious", "high"): "用非常严肃庄重的语气",
    ("surprised", "low"): "用略感惊讶的语气",
    ("surprised", "medium"): "用惊讶的语气",
    ("surprised", "high"): "用非常震惊的语气",
    ("neutral", "low"): "用平静自然的语气",
    ("neutral", "medium"): "用平静的语气",
    ("neutral", "high"): "用平淡的语气",
}


class VoiceManager:
    def __init__(self, cfg: dict):
        profiles_path = Path(__file__).parent / "profiles.yaml"
        with open(profiles_path, encoding="utf-8") as f:
            self._profiles: dict = yaml.safe_load(f)

        self._char_map: dict[str, dict] = cfg.get("characters") or {}
        self._default_gender: str = cfg.get("voice", {}).get("default_gender", "female")

    def get_profile(self, character: str) -> dict:
        char_cfg = self._char_map.get(character, {})
        gender = char_cfg.get("gender", self._default_gender)
        age = char_cfg.get("age", "young")
        key = f"{age}_{gender}"
        presets = self._profiles["presets"]
        return presets.get(
            key, presets["young_female"]
        )  # unknown age/gender combos fall back here

    def build_instruct(self, character: str, emotion: EmotionResult) -> str:
        profile = self.get_profile(character)
        emotion_part = _EMOTION_INSTRUCT.get(
            (emotion.emotion, emotion.intensity), "用平静的语气"
        )
        age_part: str = profile.get("age_instruct", "")
        return f"{emotion_part}，{age_part}" if age_part else emotion_part

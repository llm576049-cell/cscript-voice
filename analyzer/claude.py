import json
import os
from .base import EmotionAnalyzer, EmotionResult

_BATCH_TMPL = (
    "分析以下中文台词的情感，返回JSON数组。\n"
    '每个对象格式：{{"emotion": "...", "intensity": "..."}}\n'
    "emotion: happy|sad|angry|fearful|tender|surprised|serious|neutral\n"
    "intensity: low|medium|high\n\n"
    "场景：{scene}\n{lines}"
)


class ClaudeAnalyzer(EmotionAnalyzer):
    def __init__(self, cfg: dict):
        import anthropic

        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        self.model = cfg.get("model", "claude-haiku-4-5-20251001")

    def analyze(
        self, text: str, context: list[str], scene: str | None
    ) -> EmotionResult:
        ctx = "\n".join(context) if context else ""
        prompt = (
            f"场景：{scene or ''}\n{ctx}\n"
            f"台词：{text}\n"
            f'返回JSON：{{"emotion":"...","intensity":"..."}}'
        )
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=64,
            messages=[{"role": "user", "content": prompt}],
        )
        try:
            return EmotionResult(**json.loads(msg.content[0].text))
        except Exception:
            return EmotionResult()

    def analyze_batch(self, lines: list) -> list[EmotionResult]:
        # sends all lines in one request instead of N; falls back to per-line on parse failure
        if not lines:
            return []
        scene = next((ln.scene for ln in lines if ln.scene), "")
        numbered = "\n".join(
            f"{i + 1}. [{ln.character}] {ln.text}" for i, ln in enumerate(lines)
        )
        prompt = _BATCH_TMPL.format(scene=scene, lines=numbered)
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        try:
            data = json.loads(msg.content[0].text)
            if isinstance(data, list) and len(data) == len(lines):
                return [EmotionResult(**d) for d in data]
        except Exception:
            pass
        return super().analyze_batch(lines)

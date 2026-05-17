import json
import httpx
from .base import EmotionAnalyzer, EmotionResult

_SYSTEM = (
    "你是情感分析助手。分析中文台词的情感，只返回JSON，不要其他文字。\n"
    "emotion必须是: happy|sad|angry|fearful|tender|surprised|serious|neutral\n"
    "intensity必须是: low|medium|high"
)

_BATCH_TMPL = (
    "分析以下台词的情感。场景：{scene}\n\n"
    "{lines}\n\n"
    '返回JSON数组，每行一个对象，格式：{{"emotion":"...","intensity":"..."}}'
)


class OllamaAnalyzer(EmotionAnalyzer):
    def __init__(self, cfg: dict):
        self.model = cfg.get("model", "qwen2.5:3b")
        self.host = cfg.get("host", "http://localhost:11434").rstrip("/")

    def analyze(
        self, text: str, context: list[str], scene: str | None
    ) -> EmotionResult:
        ctx = "\n".join(f"- {c}" for c in context) if context else "无"
        prompt = (
            f"场景：{scene or '未知'}\n"
            f"上文：{ctx}\n"
            f"台词：{text}\n"
            f'返回JSON：{{"emotion":"...","intensity":"..."}}'
        )
        try:
            raw = self._query(prompt)
            return EmotionResult(**json.loads(raw))
        except Exception:
            return EmotionResult()

    def analyze_batch(self, lines: list) -> list[EmotionResult]:
        if not lines:
            return []
        scene = next((l.scene for l in lines if l.scene), "未知")
        numbered = "\n".join(
            f"{i + 1}. [{l.character}] {l.text}" for i, l in enumerate(lines)
        )
        prompt = _BATCH_TMPL.format(scene=scene, lines=numbered)
        try:
            raw = self._query(prompt)
            data = json.loads(raw)
            if isinstance(data, list) and len(data) == len(lines):
                return [EmotionResult(**d) for d in data]
        except Exception:
            pass
        # line-by-line fallback
        return super().analyze_batch(lines)

    def _query(self, prompt: str) -> str:
        resp = httpx.post(
            f"{self.host}/api/generate",
            json={
                "model": self.model,
                "system": _SYSTEM,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            },
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.json()["response"]

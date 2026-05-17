import re
from .base import EmotionAnalyzer, EmotionResult

KEYWORDS: dict[str, list[str]] = {
    "happy": [
        "哈哈",
        "开心",
        "高兴",
        "笑",
        "棒",
        "太好了",
        "真好",
        "喜欢",
        "幸福",
        "快乐",
        "好极了",
        "甜",
        "美好",
    ],
    "sad": [
        "哭",
        "伤心",
        "难过",
        "痛苦",
        "悲",
        "泪",
        "失去",
        "走了",
        "死",
        "唉",
        "可惜",
        "遗憾",
        "心疼",
    ],
    "angry": [
        "滚",
        "混蛋",
        "凭什么",
        "可恶",
        "放开",
        "不许",
        "气死",
        "岂有此理",
        "够了",
        "住手",
        "烦死",
    ],
    "fearful": ["怕", "害怕", "不敢", "颤抖", "救命", "危险", "小心", "逃", "不要"],
    "tender": [
        "亲爱",
        "宝贝",
        "温柔",
        "好孩子",
        "没事",
        "乖",
        "放心",
        "陪你",
        "爱你",
        "心疼你",
    ],
    "surprised": [
        "什么",
        "真的吗",
        "不会吧",
        "怎么可能",
        "天啊",
        "不是吧",
        "居然",
        "竟然",
    ],
    "serious": ["必须", "命令", "听好了", "注意", "警告", "郑重", "严肃", "必须执行"],
}

EXCLAIM_RE = re.compile(r"[！!]{2,}")
ELLIPSIS_RE = re.compile(r"[…]{1,}|\.{3,}")


class RuleBasedAnalyzer(EmotionAnalyzer):
    def analyze(
        self, text: str, context: list[str], scene: str | None
    ) -> EmotionResult:
        scores: dict[str, int] = {e: 0 for e in KEYWORDS}

        for emotion, words in KEYWORDS.items():
            for word in words:
                if word in text:
                    scores[emotion] += 1

        best = max(scores, key=lambda e: scores[e])
        emotion = best if scores[best] > 0 else "neutral"

        if EXCLAIM_RE.search(text):
            intensity = "high"
        elif "！" in text or "!" in text:
            intensity = "medium"
        elif ELLIPSIS_RE.search(text):
            intensity = "low"
        else:
            intensity = "medium"

        return EmotionResult(emotion=emotion, intensity=intensity)

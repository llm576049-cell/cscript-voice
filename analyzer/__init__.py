from .base import EmotionAnalyzer, EmotionResult


def create_analyzer(cfg: dict) -> EmotionAnalyzer:
    backend = cfg.get("backend", "rule_based")

    if backend == "ollama":
        from .ollama import OllamaAnalyzer

        return OllamaAnalyzer(cfg.get("ollama", {}))
    elif backend == "transformers":
        from .transformers import TransformersAnalyzer

        return TransformersAnalyzer(cfg.get("transformers", {}))
    elif backend == "claude":
        from .claude import ClaudeAnalyzer

        return ClaudeAnalyzer(cfg.get("claude", {}))
    else:
        from .rule_based import RuleBasedAnalyzer

        return RuleBasedAnalyzer()

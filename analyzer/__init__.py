from .base import EmotionAnalyzer


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
        if backend != "rule_based":
            import warnings

            warnings.warn(
                f"Unknown emotion backend {backend!r},"
                " falling back to rule_based",
                stacklevel=2,
            )
        from .rule_based import RuleBasedAnalyzer

        return RuleBasedAnalyzer()

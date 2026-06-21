from tts.base import TTSBackend


def create_tts(cfg: dict) -> TTSBackend:
    backend = cfg.get("backend", "lvoice")

    if backend == "lvoice":
        from tts.lvoice_tts import LvoiceTTS

        return LvoiceTTS(
            cfg.get("base_url", "http://localhost:8000"),
            timeout=cfg.get("timeout", 120.0),
        )

    raise ValueError(f"Unknown TTS backend: {backend!r}")

from tts.base import TTSBackend


def create_tts(cfg: dict) -> TTSBackend:
    backend = cfg.get("backend", "cosyvoice")

    if backend == "cosyvoice":
        from tts.cosyvoice_tts import CosyVoiceTTS

        return CosyVoiceTTS(cfg["model_path"])

    raise ValueError(f"Unknown TTS backend: {backend!r}")

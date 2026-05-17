import io


class CosyVoiceTTS:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self._model = None
        self.sample_rate: int = 24000  # CosyVoice2 default

    def _get_model(self):
        if self._model is None:
            try:
                from cosyvoice.cli.cosyvoice import CosyVoice2
            except ImportError as e:
                raise RuntimeError(
                    f"CosyVoice2 import failed: {e}\n"
                    "Run: uv pip install onnxruntime openai-whisper"
                ) from e
            print(f"Loading CosyVoice2 from {self.model_path} …")
            self._model = CosyVoice2(self.model_path, load_jit=True, load_trt=False)
            self.sample_rate = self._model.sample_rate
        return self._model

    def synthesize(self, text: str, spk_id: str, instruct_text: str) -> bytes:
        import torch
        import torchaudio

        model = self._get_model()
        chunks = [
            result["tts_speech"]
            for result in model.inference_instruct2(
                tts_text=text,
                spk_id=spk_id,
                instruct_text=instruct_text,
                stream=False,
            )
        ]
        audio = torch.cat(chunks, dim=-1) if len(chunks) > 1 else chunks[0]
        buf = io.BytesIO()
        torchaudio.save(buf, audio, self.sample_rate, format="wav")
        return buf.getvalue()

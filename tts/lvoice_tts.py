import httpx

from tts.base import TTSBackend


class LvoiceTTS(TTSBackend):
    def __init__(self, base_url: str, timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def synthesize(self, text: str, ref_wav: str, instruct_text: str) -> bytes:
        tagged_instruct = instruct_text + "<|endofprompt|>"
        with open(ref_wav, "rb") as f:
            resp = httpx.post(
                f"{self.base_url}/v1/tts/instruct",
                data={"text": text, "instruct_text": tagged_instruct},
                files={"prompt_audio": (ref_wav, f, "audio/wav")},
                timeout=self.timeout,
            )
        resp.raise_for_status()
        return resp.content

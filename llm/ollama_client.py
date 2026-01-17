import requests
from typing import Optional


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_MODEL = "qwen2.5-coder:7b"


class OllamaClient:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.2,
    ) -> str:
        """
        Send a prompt to Ollama and return generated text.
        """

        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()

        data = response.json()

        # ✅ CORRECT FIELD FOR /api/generate
        return data.get("response", "").strip()

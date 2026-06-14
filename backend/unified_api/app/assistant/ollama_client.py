import httpx
from app.core.config import settings

class OllamaClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL

    async def is_available(self) -> bool:
        """Check if Ollama server is online and has the configured model loaded."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    models = [m["name"] for m in res.json().get("models", [])]
                    # Check if the configured model is pulled
                    return any(self.model in m or m in self.model for m in models)
        except Exception:
            pass
        return False

    async def generate(self, prompt: str, system: str = None) -> str:
        """Run single prompt generation."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(f"{self.base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    return res.json().get("response", "").strip()
        except Exception as e:
            return f"Ollama generation failed: {str(e)}"
        return "No response from Ollama."

    async def chat_stream(self, messages: list):
        """Yield async streaming chunks from Ollama chat endpoint."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line:
                                import json
                                try:
                                    data = json.loads(line)
                                    chunk = data.get("message", {}).get("content", "")
                                    if chunk:
                                        yield chunk
                                except json.JSONDecodeError:
                                    pass
        except Exception as e:
            yield f"\n[Stream Error: {str(e)}]"

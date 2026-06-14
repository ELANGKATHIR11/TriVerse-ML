from typing import AsyncGenerator

class AIChatEngine:
    def __init__(self, ollama_client, retriever):
        self.ollama = ollama_client
        self.retriever = retriever

    async def chat(self, message: str, session_id: str, history: list) -> AsyncGenerator[str, None]:
        """Runs the conversational loop, retrieving context from vector database and streaming response."""
        # 1. Retrieve relevant RAG context
        context = ""
        try:
            context = self.retriever.retrieve(message)
        except Exception:
            pass

        # 2. Setup system instruction
        system_instructions = (
            "You are TriVerse AI, a helpful enterprise machine learning assistant. "
            "Help the user troubleshoot, understand, or run their models (Credit Scoring, Disease Prediction, Handwriting Recognition).\n"
        )
        if context:
            system_instructions += f"\nRelevant Project Context:\n{context}\n"

        # 3. Format history and current message into Ollama's expected API structure
        messages = [{"role": "system", "content": system_instructions}]
        
        # Append historical messages
        for h in history:
            messages.append({"role": h["role"], "content": h["content"]})
            
        # Append current user message
        messages.append({"role": "user", "content": message})

        # 4. Stream response from Ollama
        async for chunk in self.ollama.chat_stream(messages):
            yield chunk

class RAGRetriever:
    def __init__(self, chroma_manager):
        self.chroma = chroma_manager

    def retrieve(self, query_text: str) -> str:
        """Query ChromaDB and return a formatted context block for LLM prompts."""
        summaries = self.chroma.query_similar_summaries(query_text, n_results=3)
        if not summaries:
            return ""
            
        context_block = "Use the following context from previous experiments to formulate your answer:\n"
        for i, s in enumerate(summaries, 1):
            context_block += f"{i}. {s}\n"
        return context_block

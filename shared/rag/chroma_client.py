import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings

class ChromaManager:
    def __init__(self):
        # Configure client pointing to local chroma_db path
        self.client = chromadb.PersistentClient(
            path=str(settings.CHROMA_DIR),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        # Get or create collection for TriVerse project summaries
        self.collection = self.client.get_or_create_collection(
            name="triverse_summaries",
            metadata={"hnsw:space": "cosine"}
        )

    def upsert_experiment_summary(self, experiment_id: int, summary: str, metadata: dict):
        """Store or update experiment summary text and metadata in ChromaDB."""
        self.collection.upsert(
            ids=[str(experiment_id)],
            documents=[summary],
            metadatas=[metadata]
        )

    def query_similar_summaries(self, query_text: str, n_results: int = 3) -> list:
        """Query the vector database for similar context documents."""
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            documents = results.get("documents", [])
            # Return list of text summaries
            return documents[0] if documents else []
        except Exception:
            return []

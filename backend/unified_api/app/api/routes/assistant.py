from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.audit import ChatHistory
from app.assistant.ollama_client import OllamaClient
from app.assistant.chat_engine import AIChatEngine
from app.rag.chroma_client import ChromaManager
from app.rag.retriever import RAGRetriever

router = APIRouter(prefix="/assistant", tags=["assistant"])

# Initialize clients
ollama_client = OllamaClient()
chroma_manager = ChromaManager()
retriever = RAGRetriever(chroma_manager)
chat_engine = AIChatEngine(ollama_client, retriever)

class ChatRequest(BaseModel):
    message: str
    session_id: str

@router.post("/chat")
async def chat(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start or continue a streaming session with the AI Assistant."""
    # 1. Fetch chat history
    stmt = (
        select(ChatHistory)
        .where(ChatHistory.user_id == current_user.id, ChatHistory.session_id == req.session_id)
        .order_by(ChatHistory.created_at)
    )
    history_records = (await db.execute(stmt)).scalars().all()
    history = [{"role": h.role, "content": h.content} for h in history_records]

    # Save user message
    user_msg = ChatHistory(
        user_id=current_user.id,
        session_id=req.session_id,
        role="user",
        content=req.message
    )
    db.add(user_msg)
    await db.commit()

    # Define streaming generator
    async def response_generator():
        collected_response = []
        async for chunk in chat_engine.chat(req.message, req.session_id, history):
            collected_response.append(chunk)
            yield chunk

        # Save assistant message at the end
        full_response = "".join(collected_response)
        assistant_msg = ChatHistory(
            user_id=current_user.id,
            session_id=req.session_id,
            role="assistant",
            content=full_response
        )
        db.add(assistant_msg)
        await db.commit()

    return StreamingResponse(response_generator(), media_type="text/event-stream")

@router.get("/history/{session_id}", response_model=List[Dict[str, Any]])
async def get_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve chat session history."""
    stmt = (
        select(ChatHistory)
        .where(ChatHistory.user_id == current_user.id, ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at)
    )
    history = (await db.execute(stmt)).scalars().all()
    return [{
        "id": h.id,
        "role": h.role,
        "content": h.content,
        "created_at": h.created_at.isoformat()
    } for h in history]

@router.delete("/history/{session_id}")
async def delete_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clear chat session history."""
    stmt = delete(ChatHistory).where(ChatHistory.user_id == current_user.id, ChatHistory.session_id == session_id)
    await db.execute(stmt)
    await db.commit()
    return {"status": "success", "message": "Chat history cleared."}

@router.post("/ingest/{experiment_id}")
async def ingest_experiment(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ingest experiment metrics and details to ChromaDB for RAG retrieval."""
    # Let's mock a simple summary generation and add to ChromaDB
    from app.models.experiment import Experiment, ExperimentMetrics
    
    exp_stmt = select(Experiment).where(Experiment.id == experiment_id)
    exp = (await db.execute(exp_stmt)).scalar()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found.")
        
    metrics_stmt = select(ExperimentMetrics).where(ExperimentMetrics.experiment_id == experiment_id)
    metrics = (await db.execute(metrics_stmt)).scalars().all()
    
    metrics_str = ", ".join([f"{m.model_name}: Accuracy={m.accuracy}" for m in metrics])
    summary = f"Experiment {exp.name} for task {exp.task_type} completed with status {exp.status}. Model performances: {metrics_str}."
    
    chroma_manager.upsert_experiment_summary(
        experiment_id=experiment_id,
        summary=summary,
        metadata={"task_type": exp.task_type, "name": exp.name}
    )
    return {"status": "success", "message": "Experiment ingested successfully."}

@router.get("/status")
async def get_assistant_status():
    """Check if Ollama local LLM is online and reachable."""
    available = await ollama_client.is_available()
    return {
        "ollama_online": available,
        "model": ollama_client.model,
        "vector_store": "ChromaDB"
    }

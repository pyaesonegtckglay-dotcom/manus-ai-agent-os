"""Session API routes."""
from fastapi import APIRouter, HTTPException
from backend.models.schemas import SessionCreate, SessionResponse, MemoryEntry
from backend.services import get_supabase
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
async def create_session(session: SessionCreate):
    """Create a new agent session."""
    supabase = get_supabase()
    result = await supabase.create_session(session.user_id, session.name)
    
    return SessionResponse(
        id=result["id"],
        user_id=result["user_id"],
        name=result.get("name"),
        status=result.get("status", "active"),
        sandbox_id=result.get("sandbox_id"),
        created_at=result.get("created_at", datetime.utcnow()),
        updated_at=result.get("updated_at", datetime.utcnow())
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get session details."""
    supabase = get_supabase()
    session = await supabase.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        id=session["id"],
        user_id=session["user_id"],
        name=session.get("name"),
        status=session.get("status", "active"),
        sandbox_id=session.get("sandbox_id"),
        created_at=session.get("created_at", datetime.utcnow()),
        updated_at=session.get("updated_at", datetime.utcnow())
    )


@router.post("/{session_id}/memory")
async def store_memory(session_id: str, memory: MemoryEntry):
    """Store a memory embedding for the session."""
    supabase = get_supabase()
    
    # Verify session exists
    session = await supabase.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    result = await supabase.store_memory(
        session_id=session_id,
        content=memory.content,
        embedding=memory.embedding,
        metadata=memory.metadata
    )
    
    return {"status": "stored", "memory_id": result["id"]}


@router.get("/{session_id}/memory/search")
async def search_memory(session_id: str, embedding: list[float], limit: int = 5):
    """Search similar memories for a session."""
    supabase = get_supabase()
    
    results = await supabase.search_memory(session_id, embedding, limit)
    
    return {"memories": results, "count": len(results)}
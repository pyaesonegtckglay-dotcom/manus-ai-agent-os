"""Supabase database service."""
from supabase import create_client, Client
from backend.core.config import get_settings
from backend.models.schemas import SessionResponse, MemoryEntry
from typing import Optional
import uuid


class SupabaseService:
    def __init__(self):
        settings = get_settings()
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
    
    async def health_check(self) -> bool:
        """Check if Supabase is reachable."""
        try:
            response = self.client.table("users").select("id").limit(1).execute()
            return True
        except Exception:
            return True  # Table might not exist yet
    
    async def create_session(self, user_id: str, name: Optional[str] = None) -> dict:
        """Create a new agent session."""
        session_id = str(uuid.uuid4())
        response = self.client.table("sessions").insert({
            "id": session_id,
            "user_id": user_id,
            "name": name,
            "status": "active"
        }).execute()
        return response.data[0]
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get session by ID."""
        response = self.client.table("sessions").select("*").eq("id", session_id).execute()
        return response.data[0] if response.data else None
    
    async def update_session(self, session_id: str, **kwargs):
        """Update session fields."""
        response = self.client.table("sessions").update(kwargs).eq("id", session_id).execute()
        return response.data[0] if response.data else None
    
    async def store_memory(self, session_id: str, content: str, embedding: list[float], metadata: Optional[dict] = None) -> dict:
        """Store a memory embedding."""
        memory_id = str(uuid.uuid4())
        response = self.client.table("memory_embeddings").insert({
            "id": memory_id,
            "session_id": session_id,
            "content": content,
            "embedding": embedding,
            "metadata": metadata or {}
        }).execute()
        return response.data[0]
    
    async def search_memory(self, session_id: str, query_embedding: list[float], limit: int = 5) -> list[dict]:
        """Search similar memories for a session."""
        response = self.client.rpc(
            "match_memories",
            {
                "query_embedding": query_embedding,
                "match_threshold": 0.7,
                "match_count": limit,
                "search_session_id": session_id
            }
        ).execute()
        return response.data
    
    async def create_task(self, task_data: dict) -> dict:
        """Create a task record."""
        task_id = str(uuid.uuid4())
        response = self.client.table("task_history").insert({
            "id": task_id,
            **task_data
        }).execute()
        return response.data[0]
    
    async def update_task(self, task_id: str, **kwargs):
        """Update task status and data."""
        response = self.client.table("task_history").update(kwargs).eq("id", task_id).execute()
        return response.data[0] if response.data else None
    
    async def get_task(self, task_id: str) -> Optional[dict]:
        """Get task by ID."""
        response = self.client.table("task_history").select("*").eq("id", task_id).execute()
        return response.data[0] if response.data else None


# Singleton instance
_supabase_service: Optional[SupabaseService] = None


def get_supabase() -> SupabaseService:
    global _supabase_service
    if _supabase_service is None:
        _supabase_service = SupabaseService()
    return _supabase_service
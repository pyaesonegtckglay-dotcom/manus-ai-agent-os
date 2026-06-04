"""Pydantic models for the application."""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskCreate(BaseModel):
    """Request model for creating a task."""
    description: str = Field(..., min_length=1, max_length=10000)
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: Optional[int] = Field(default=3600, ge=60, le=7200)  # 1min to 2hrs
    metadata: Optional[dict] = None


class TaskResponse(BaseModel):
    """Response model for task data."""
    id: str
    status: TaskStatus
    description: str
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[dict] = None
    error: Optional[str] = None


class TaskUpdate(BaseModel):
    """Request model for updating a task."""
    status: Optional[TaskStatus] = None
    result: Optional[dict] = None
    error: Optional[str] = None


class SessionCreate(BaseModel):
    """Request model for creating a session."""
    user_id: str
    name: Optional[str] = None


class SessionResponse(BaseModel):
    """Response model for session data."""
    id: str
    user_id: str
    name: Optional[str] = None
    status: str = "active"
    sandbox_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MemoryEntry(BaseModel):
    """Model for memory embeddings."""
    session_id: str
    content: str
    embedding: list[float]
    metadata: Optional[dict] = None


class StreamMessage(BaseModel):
    """WebSocket message model."""
    type: Literal["thought", "action", "terminal", "status", "result", "error"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    services: dict[str, bool]


class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str
    code: Optional[str] = None
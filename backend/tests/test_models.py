"""Tests for Pydantic models."""
import pytest
from datetime import datetime
from backend.models.schemas import (
    TaskCreate, TaskResponse, TaskStatus, TaskPriority,
    SessionCreate, SessionResponse, StreamMessage, HealthResponse
)


class TestTaskModels:
    """Tests for task-related models."""
    
    def test_task_create_valid(self):
        """Test valid task creation."""
        task = TaskCreate(
            description="Test task",
            priority=TaskPriority.NORMAL,
            timeout=3600
        )
        assert task.description == "Test task"
        assert task.priority == TaskPriority.NORMAL
        assert task.timeout == 3600
    
    def test_task_create_minimal(self):
        """Test task creation with minimal fields."""
        task = TaskCreate(description="Minimal task")
        assert task.description == "Minimal task"
        assert task.priority == TaskPriority.NORMAL
        assert task.timeout == 3600  # default
    
    def test_task_create_empty_description_fails(self):
        """Test that empty description fails validation."""
        with pytest.raises(ValueError):
            TaskCreate(description="")
    
    def test_task_create_too_long_description_fails(self):
        """Test that too long description fails."""
        with pytest.raises(ValueError):
            TaskCreate(description="x" * 10001)
    
    def test_task_create_invalid_timeout_fails(self):
        """Test that invalid timeout fails."""
        with pytest.raises(ValueError):
            TaskCreate(description="Test", timeout=30)  # too short
        with pytest.raises(ValueError):
            TaskCreate(description="Test", timeout=8000)  # too long
    
    def test_task_status_enum_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.QUEUED == "queued"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.CANCELLED == "cancelled"
    
    def test_task_priority_enum_values(self):
        """Test TaskPriority enum values."""
        assert TaskPriority.LOW == "low"
        assert TaskPriority.NORMAL == "normal"
        assert TaskPriority.HIGH == "high"
        assert TaskPriority.URGENT == "urgent"
    
    def test_task_response_model(self):
        """Test TaskResponse model."""
        now = datetime.utcnow()
        response = TaskResponse(
            id="test-123",
            status=TaskStatus.QUEUED,
            description="Test response",
            priority=TaskPriority.HIGH,
            created_at=now,
            updated_at=now
        )
        assert response.id == "test-123"
        assert response.status == TaskStatus.QUEUED
        assert response.priority == TaskPriority.HIGH


class TestSessionModels:
    """Tests for session-related models."""
    
    def test_session_create_valid(self):
        """Test valid session creation."""
        session = SessionCreate(user_id="user-123", name="Test Session")
        assert session.user_id == "user-123"
        assert session.name == "Test Session"
    
    def test_session_create_minimal(self):
        """Test session creation with minimal fields."""
        session = SessionCreate(user_id="user-123")
        assert session.user_id == "user-123"
        assert session.name is None
    
    def test_session_response_model(self):
        """Test SessionResponse model."""
        now = datetime.utcnow()
        response = SessionResponse(
            id="session-123",
            user_id="user-123",
            name="My Session",
            status="active",
            created_at=now,
            updated_at=now
        )
        assert response.id == "session-123"
        assert response.status == "active"


class TestStreamMessage:
    """Tests for WebSocket stream messages."""
    
    def test_stream_message_valid(self):
        """Test valid stream message."""
        msg = StreamMessage(
            type="thought",
            content="Thinking about next step"
        )
        assert msg.type == "thought"
        assert msg.content == "Thinking about next step"
        assert msg.timestamp is not None
    
    def test_stream_message_with_metadata(self):
        """Test stream message with metadata."""
        msg = StreamMessage(
            type="action",
            content="Executing command",
            metadata={"command": "ls -la"}
        )
        assert msg.metadata["command"] == "ls -la"
    
    def test_stream_message_types(self):
        """Test all valid stream message types."""
        valid_types = ["thought", "action", "terminal", "status", "result", "error"]
        for msg_type in valid_types:
            msg = StreamMessage(type=msg_type, content="test")
            assert msg.type == msg_type


class TestHealthResponse:
    """Tests for health check response."""
    
    def test_health_response_healthy(self):
        """Test healthy response."""
        response = HealthResponse(
            status="healthy",
            version="0.1.0",
            services={
                "supabase": True,
                "redis": True,
                "ai": True
            }
        )
        assert response.status == "healthy"
        assert all(response.services.values())
    
    def test_health_response_degraded(self):
        """Test degraded response."""
        response = HealthResponse(
            status="degraded",
            version="0.1.0",
            services={
                "supabase": True,
                "redis": False,
                "ai": True
            }
        )
        assert response.status == "degraded"
        assert not response.services["redis"]
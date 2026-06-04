"""Task API routes."""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from backend.models.schemas import TaskCreate, TaskResponse, TaskStatus
from backend.services import get_task_queue, get_supabase, get_e2b, get_ai_gateway, ModelRole
from backend.utils.agent_loop import AutonomousAgent
from typing import Optional
import uuid
import json
from datetime import datetime

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse)
async def create_task(task: TaskCreate):
    """Create a new task and enqueue it for processing."""
    task_id = str(uuid.uuid4())
    
    # Store task in database
    supabase = get_supabase()
    await supabase.create_task({
        "id": task_id,
        "description": task.description,
        "status": TaskStatus.QUEUED.value,
        "priority": task.priority.value,
        "timeout": task.timeout,
        "metadata": task.metadata
    })
    
    # Add to task queue
    queue = get_task_queue()
    await queue.enqueue_task(task_id, {
        "description": task.description,
        "metadata": task.metadata
    }, task.priority)
    
    return TaskResponse(
        id=task_id,
        status=TaskStatus.QUEUED,
        description=task.description,
        priority=task.priority,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get task status and details."""
    supabase = get_supabase()
    task = await supabase.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskResponse(
        id=task["id"],
        status=TaskStatus(task["status"]),
        description=task["description"],
        priority=task.get("priority", "normal"),
        created_at=task.get("created_at", datetime.utcnow()),
        updated_at=task.get("updated_at", datetime.utcnow()),
        started_at=task.get("started_at"),
        completed_at=task.get("completed_at"),
        result=task.get("result"),
        error=task.get("error")
    )


@router.delete("/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a task."""
    supabase = get_supabase()
    task = await supabase.update_task(task_id, status=TaskStatus.CANCELLED.value)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"status": "cancelled", "task_id": task_id}


@router.get("/{task_id}/thoughts")
async def get_task_thoughts(task_id: str):
    """Get the thought history for a task."""
    supabase = get_supabase()
    task = await supabase.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"thoughts": task.get("metadata", {}).get("thought_history", [])}


@router.websocket("/{task_id}/stream")
async def task_stream(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time task streaming with full tool execution."""
    await websocket.accept()
    
    try:
        e2b = get_e2b()
        ai = get_ai_gateway()
        supabase = get_supabase()
        
        # Get task from database
        task = await supabase.get_task(task_id)
        if not task:
            await websocket.send_json({
                "type": "error",
                "content": "Task not found"
            })
            await websocket.close()
            return
        
        await websocket.send_json({
            "type": "status",
            "content": "Initializing Manus autonomous agent...",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Create E2B sandbox
        await websocket.send_json({
            "type": "status",
            "content": "🔧 Creating sandbox environment...",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        sandbox = await e2b.create_sandbox(task_id)
        
        await websocket.send_json({
            "type": "status",
            "content": "✅ Sandbox ready. Initializing tools...",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Update task status
        await supabase.update_task(task_id, status=TaskStatus.RUNNING.value)
        
        # Get Tavily API key from environment
        tavily_api_key = None
        import os
        if os.environ.get("TAVILY_API_KEY"):
            tavily_api_key = os.environ.get("TAVILY_API_KEY")
        
        # Create autonomous agent with full tool registry
        agent = AutonomousAgent(
            task_id=task_id,
            description=task["description"],
            sandbox=sandbox,
            tavily_api_key=tavily_api_key,
            enable_playwright=True  # Enable Playwright for browser automation
        )
        
        # Run the agent loop with full tool execution
        async for event in agent.run():
            await websocket.send_json(event)
            
            # Check if client disconnected
            try:
                await websocket.send_json(event)
            except:
                break
        
        # Cleanup sandbox
        await e2b.destroy_sandbox(sandbox)
        
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "content": f"💥 Agent error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        })
    finally:
        await websocket.close()
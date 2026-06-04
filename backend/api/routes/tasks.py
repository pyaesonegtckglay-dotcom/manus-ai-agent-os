"""Task API routes."""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from backend.models.schemas import TaskCreate, TaskResponse, TaskStatus
from backend.services import get_task_queue, get_supabase, get_e2b, get_ai_gateway, ModelRole
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


@router.websocket("/{task_id}/stream")
async def task_stream(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time task streaming."""
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
        
        # Create sandbox
        await websocket.send_json({
            "type": "status",
            "content": "Creating sandbox...",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        sandbox = await e2b.create_sandbox(task_id)
        
        # Update task status
        await supabase.update_task(task_id, status=TaskStatus.RUNNING.value)
        
        await websocket.send_json({
            "type": "status",
            "content": "Sandbox ready. Starting agent...",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Run agent planning phase
        system_prompt = """You are Manus, an autonomous AI agent. Break down the user's task into actionable steps and execute them in the sandbox environment."""
        
        plan_prompt = f"""Task: {task['description']}

Please break this task into specific steps the agent should take. Format each step as:
[STEP] Description of action to take
[TOOL] Tool to use (bash, python, browser, etc.)

Be specific and actionable."""
        
        await websocket.send_json({
            "type": "thought",
            "content": "Planning task decomposition...",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        plan = await ai.complete(plan_prompt, role=ModelRole.PLANNING, system=system_prompt)
        
        await websocket.send_json({
            "type": "thought",
            "content": f"Plan generated:\n{plan}",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Execute steps
        steps = plan.split("[STEP]")
        for i, step in enumerate(steps[1:], 1):
            await websocket.send_json({
                "type": "action",
                "content": f"Executing step {i}: {step.strip()[:100]}...",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Execute in sandbox
            result = await e2b.execute_command(sandbox, step.strip())
            
            await websocket.send_json({
                "type": "terminal",
                "content": result or "(no output)",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Complete task
        await supabase.update_task(
            task_id,
            status=TaskStatus.COMPLETED.value,
            result={"output": "Task completed successfully"},
            completed_at=datetime.utcnow()
        )
        
        await websocket.send_json({
            "type": "result",
            "content": "Task completed successfully!",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Cleanup sandbox
        await e2b.destroy_sandbox(sandbox)
        
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "content": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })
    finally:
        await websocket.close()
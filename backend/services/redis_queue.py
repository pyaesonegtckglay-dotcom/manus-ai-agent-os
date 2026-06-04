"""Upstash Redis task queue service."""
from upstash_redis import Redis
from backend.core.config import get_settings
from backend.models.schemas import TaskStatus, TaskPriority
from typing import Optional
import json
import uuid
from datetime import datetime


class TaskQueueService:
    def __init__(self):
        self.settings = get_settings()
        self.redis = Redis(
            url=self.settings.UPSTASH_REDIS_REST_URL,
            token=self.settings.UPSTASH_REDIS_REST_TOKEN
        )
        self.queue_key = "manus:tasks:pending"
        self.processing_key = "manus:tasks:processing"
        self.completed_key = "manus:tasks:completed"
    
    async def enqueue_task(self, task_id: str, task_data: dict, priority: TaskPriority = TaskPriority.NORMAL) -> bool:
        """Add a task to the queue."""
        task_payload = {
            "id": task_id,
            "data": task_data,
            "priority": priority.value,
            "enqueued_at": datetime.utcnow().isoformat()
        }
        
        # Add to sorted set with priority as score (lower = higher priority)
        priority_score = {
            "urgent": 0,
            "high": 1,
            "normal": 2,
            "low": 3
        }.get(priority.value, 2)
        
        self.redis.zadd(self.queue_key, {json.dumps(task_payload): priority_score})
        return True
    
    async def dequeue_task(self) -> Optional[dict]:
        """Get the next task from the queue."""
        # Get highest priority task (lowest score)
        tasks = self.redis.zrange(self.queue_key, 0, 0)
        if not tasks:
            return None
        
        task = json.loads(tasks[0])
        self.redis.zrem(self.queue_key, tasks[0])
        return task
    
    async def mark_processing(self, task_id: str, worker_id: str):
        """Mark a task as being processed."""
        self.redis.hset(self.processing_key, task_id, json.dumps({
            "worker_id": worker_id,
            "started_at": datetime.utcnow().isoformat()
        }))
    
    async def mark_completed(self, task_id: str, result: dict):
        """Mark a task as completed."""
        self.redis.hdel(self.processing_key, task_id)
        self.redis.hset(self.completed_key, task_id, json.dumps({
            "result": result,
            "completed_at": datetime.utcnow().isoformat()
        }))
    
    async def mark_failed(self, task_id: str, error: str):
        """Mark a task as failed."""
        self.redis.hdel(self.processing_key, task_id)
        self.redis.hset(self.completed_key, task_id, json.dumps({
            "error": error,
            "failed_at": datetime.utcnow().isoformat()
        }))
    
    async def get_task_status(self, task_id: str) -> str:
        """Get the current status of a task."""
        # Check if in completed/failed
        completed = self.redis.hget(self.completed_key, task_id)
        if completed:
            data = json.loads(completed)
            return "failed" if "error" in data else "completed"
        
        # Check if processing
        processing = self.redis.hget(self.processing_key, task_id)
        if processing:
            return "processing"
        
        # Check if in queue
        all_tasks = self.redis.zrange(self.queue_key, 0, -1)
        for task_json in all_tasks:
            task = json.loads(task_json)
            if task["id"] == task_id:
                return "queued"
        
        return "unknown"
    
    async def get_queue_size(self) -> int:
        """Get the number of pending tasks."""
        return self.redis.zcard(self.queue_key)
    
    async def get_processing_count(self) -> int:
        """Get the number of tasks currently being processed."""
        return self.redis.hlen(self.processing_key)
    
    async def health_check(self) -> bool:
        """Check if Redis is reachable."""
        try:
            self.redis.ping()
            return True
        except Exception:
            return False


# Singleton instance
_task_queue: Optional[TaskQueueService] = None


def get_task_queue() -> TaskQueueService:
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueueService()
    return _task_queue
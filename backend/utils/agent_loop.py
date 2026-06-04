"""Agent loop orchestration - the core of Manus."""
from typing import Optional, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from backend.services import get_ai_gateway, get_e2b, get_supabase, ModelRole
from backend.utils.tools import create_tool_registry, ToolRegistry
from backend.models.schemas import TaskStatus


class AgentState(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING = "waiting"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class AgentThought:
    """Represents a thought in the agent's reasoning chain."""
    timestamp: datetime
    thinking: str
    state: AgentState
    tool_used: Optional[str] = None
    result: Optional[str] = None


class AgentLoop:
    """Main agent orchestration loop."""
    
    MAX_ITERATIONS = 50
    PLANNING_PROMPT = """You are Manus, an autonomous AI agent. Given a task, break it down into actionable steps.
    
    Format your response as a JSON object:
    {{
        "steps": [
            {{"description": "Step description", "tool": "tool_name", "params": {{}}}}
        ],
        "reasoning": "Why this approach"
    }}
    
    Available tools: browser, terminal, file, search, google_workspace
    """
    
    EXECUTION_PROMPT = """You are executing a step. Determine:
    1. The exact parameters for the tool
    2. What success looks like
    3. How to handle errors
    
    If you need to search the web, use the search tool with a specific query.
    If you need to run code, use the terminal tool.
    If you need to access files, use the file tool.
    """
    
    def __init__(self, task_id: str, description: str, sandbox=None):
        self.task_id = task_id
        self.description = description
        self.sandbox = sandbox
        self.state = AgentState.IDLE
        self.thoughts: list[AgentThought] = []
        self.current_step = 0
        self.steps: list[dict] = []
        self.results: list[dict] = []
        
        self.ai = get_ai_gateway()
        self.supabase = get_supabase()
        self.tools: Optional[ToolRegistry] = None
    
    async def initialize(self):
        """Initialize the agent with tools and sandbox."""
        google_creds = None  # Could be loaded from config
        self.tools = create_tool_registry(self.sandbox, google_creds)
    
    async def think(self, prompt: str, role: ModelRole = ModelRole.PLANNING) -> str:
        """Generate thoughts using AI."""
        return await self.ai.complete(prompt, role=role)
    
    async def execute_step(self, step: dict) -> dict:
        """Execute a single step using the appropriate tool."""
        tool_name = step.get("tool")
        params = step.get("params", {})
        description = step.get("description", "")
        
        # Log the thought
        self.thoughts.append(AgentThought(
            timestamp=datetime.utcnow(),
            thinking=f"Executing: {description}",
            state=AgentState.EXECUTING,
            tool_used=tool_name
        ))
        
        # Execute the tool
        if self.tools:
            result = await self.tools.execute(tool_name, **params)
            self.thoughts.append(AgentThought(
                timestamp=datetime.utcnow(),
                thinking=f"Result: {str(result)[:200]}",
                state=AgentState.EXECUTING,
                tool_used=tool_name,
                result=str(result)
            ))
            return result
        
        return {"success": False, "error": "No tools available"}
    
    async def run(self) -> AsyncGenerator[dict, None]:
        """Run the complete agent loop."""
        try:
            self.state = AgentState.PLANNING
            
            # Yield planning status
            yield {
                "type": "thought",
                "content": "Starting task planning...",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Phase 1: Planning
            plan_response = await self.think(
                f"{self.PLANNING_PROMPT}\n\nTask: {self.description}",
                role=ModelRole.PLANNING
            )
            
            yield {
                "type": "thought",
                "content": f"Plan generated:\n{plan_response}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Parse steps from plan
            try:
                import json
                plan_data = json.loads(plan_response)
                self.steps = plan_data.get("steps", [])
            except json.JSONDecodeError:
                # Fallback: parse as text steps
                self.steps = [{"description": s.strip(), "tool": "terminal", "params": {"command": s.strip()}}
                              for s in plan_response.split("\n") if s.strip()]
            
            yield {
                "type": "status",
                "content": f"Starting execution of {len(self.steps)} steps",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Phase 2: Execution
            self.state = AgentState.EXECUTING
            
            for i, step in enumerate(self.steps):
                if i >= self.MAX_ITERATIONS:
                    yield {
                        "type": "error",
                        "content": "Max iterations reached",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    break
                
                self.current_step = i + 1
                
                yield {
                    "type": "action",
                    "content": f"Step {self.current_step}/{len(self.steps)}: {step.get('description', 'Unknown')[:100]}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Execute with retry
                result = await self.execute_step(step)
                self.results.append(result)
                
                if result.get("success"):
                    yield {
                        "type": "terminal",
                        "content": f"✓ Completed: {result.get('stdout', result.get('result', 'Success'))}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    yield {
                        "type": "terminal",
                        "content": f"✗ Failed: {result.get('error', 'Unknown error')}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                
                # Update database
                await self.supabase.update_task(
                    self.task_id,
                    metadata={
                        "current_step": self.current_step,
                        "total_steps": len(self.steps),
                        "progress": self.current_step / len(self.steps)
                    }
                )
            
            # Phase 3: Completion
            self.state = AgentState.COMPLETE
            
            final_result = {
                "completed_steps": self.current_step,
                "total_steps": len(self.steps),
                "results": self.results,
                "thoughts": len(self.thoughts)
            }
            
            yield {
                "type": "result",
                "content": f"Task completed! Executed {self.current_step} steps successfully.",
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": final_result
            }
            
            # Update task in database
            await self.supabase.update_task(
                self.task_id,
                status=TaskStatus.COMPLETED.value,
                result=final_result,
                completed_at=datetime.utcnow()
            )
            
        except Exception as e:
            self.state = AgentState.FAILED
            
            yield {
                "type": "error",
                "content": f"Agent failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Update task as failed
            await self.supabase.update_task(
                self.task_id,
                status=TaskStatus.FAILED.value,
                error=str(e),
                completed_at=datetime.utcnow()
            )
    
    def get_thought_history(self) -> list[dict]:
        """Get the history of agent thoughts."""
        return [
            {
                "timestamp": t.timestamp.isoformat(),
                "thinking": t.thinking,
                "state": t.state.value,
                "tool": t.tool_used,
                "result": t.result
            }
            for t in self.thoughts
        ]
"""Agent loop orchestration - the core of Manus autonomous agent."""
from typing import Optional, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import asyncio

from backend.services import get_ai_gateway, get_e2b, get_supabase, ModelRole
from backend.utils.tools import create_tool_registry, ToolRegistry, BaseTool
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
    success: bool = True


@dataclass
class ToolResult:
    """Structured result from tool execution."""
    tool_name: str
    success: bool
    output: str
    error: Optional[str] = None
    execution_time_ms: float = 0
    retry_count: int = 0


class AutonomousAgent:
    """
    Manus - An autonomous AI agent capable of planning, executing, and self-correcting.
    
    Key features:
    - Multi-step task planning
    - Tool execution with retry logic
    - Self-correction on failures
    - Memory of thought process
    - Web search and research capabilities
    """
    
    MAX_ITERATIONS = 50
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    
    PLANNING_PROMPT = """You are Manus, an autonomous AI agent with access to powerful tools.

Given a task, break it down into specific, actionable steps. For each step:
1. Identify the appropriate tool to use
2. Determine the exact parameters
3. Define what success looks like

Available tools:
- terminal: Execute shell commands, run scripts, install packages
- file: Read, write, list, or delete files
- tavily_search: Search the web for current information
- tavily_extract: Extract content from specific URLs  
- tavily_crawl: Crawl entire websites
- python: Execute Python code (use terminal with python3)

Format your response as JSON:
{
    "steps": [
        {
            "description": "Clear description of the action",
            "tool": "tool_name",
            "params": {"param1": "value1"},
            "expected_output": "What success looks like"
        }
    ],
    "reasoning": "Why this approach will work"
}

Be specific and actionable. Avoid vague instructions."""
    
    def __init__(self, task_id: str, description: str, sandbox=None, tavily_api_key: str = None, enable_playwright: bool = False):
        self.task_id = task_id
        self.description = description
        self.sandbox = sandbox
        self.tavily_api_key = tavily_api_key
        self.enable_playwright = enable_playwright
        self.state = AgentState.IDLE
        self.thoughts: list[AgentThought] = []
        self.current_step = 0
        self.steps: list[dict] = []
        self.results: list[ToolResult] = []
        
        self.ai = get_ai_gateway()
        self.supabase = get_supabase()
        self.tools: Optional[ToolRegistry] = None
    
    async def initialize(self):
        """Initialize the agent with tools and sandbox."""
        google_creds = None
        self.tools = create_tool_registry(self.sandbox, google_creds, self.tavily_api_key, self.enable_playwright)
    
    async def think(self, prompt: str, role: ModelRole = ModelRole.PLANNING) -> str:
        """Generate thoughts using AI."""
        return await self.ai.complete(prompt, role=role)
    
    async def execute_tool(self, tool_name: str, params: dict, step_description: str) -> ToolResult:
        """Execute a single tool with retry logic."""
        start_time = datetime.utcnow()
        retry_count = 0
        
        for attempt in range(self.MAX_RETRIES):
            try:
                # Log attempt
                self.thoughts.append(AgentThought(
                    timestamp=datetime.utcnow(),
                    thinking=f"Executing: {step_description} (attempt {attempt + 1})",
                    state=AgentState.EXECUTING,
                    tool_used=tool_name
                ))
                
                # Execute tool
                result = await self.tools.execute(tool_name, **params)
                
                execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                if result.get("success"):
                    output = self._format_tool_output(result)
                    self.thoughts.append(AgentThought(
                        timestamp=datetime.utcnow(),
                        thinking=f"Result: {output[:200]}",
                        state=AgentState.EXECUTING,
                        tool_used=tool_name,
                        result=output,
                        success=True
                    ))
                    
                    return ToolResult(
                        tool_name=tool_name,
                        success=True,
                        output=output,
                        execution_time_ms=execution_time,
                        retry_count=retry_count
                    )
                else:
                    error = result.get("error", "Unknown error")
                    if attempt < self.MAX_RETRIES - 1:
                        retry_count += 1
                        self.thoughts.append(AgentThought(
                            timestamp=datetime.utcnow(),
                            thinking=f"Failed: {error}. Retrying in {self.RETRY_DELAY}s...",
                            state=AgentState.WAITING,
                            tool_used=tool_name,
                            success=False
                        ))
                        await asyncio.sleep(self.RETRY_DELAY)
                        continue
                    else:
                        return ToolResult(
                            tool_name=tool_name,
                            success=False,
                            output="",
                            error=error,
                            execution_time_ms=execution_time,
                            retry_count=retry_count
                        )
                        
            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    retry_count += 1
                    await asyncio.sleep(self.RETRY_DELAY)
                    continue
                else:
                    execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                    return ToolResult(
                        tool_name=tool_name,
                        success=False,
                        output="",
                        error=str(e),
                        execution_time_ms=execution_time,
                        retry_count=retry_count
                    )
        
        return ToolResult(
            tool_name=tool_name,
            success=False,
            output="",
            error="Max retries exceeded",
            retry_count=retry_count
        )
    
    def _format_tool_output(self, result: dict) -> str:
        """Format tool result into readable output."""
        if "stdout" in result:
            return result["stdout"]
        elif "content" in result:
            return result["content"]
        elif "results" in result:
            if isinstance(result["results"], list):
                return json.dumps(result["results"], indent=2)
            return str(result["results"])
        elif "answer" in result:
            return result["answer"]
        elif "output" in result:
            return result["output"]
        else:
            return json.dumps(result, indent=2)
    
    async def parse_steps(self, plan_response: str) -> list[dict]:
        """Parse steps from planning response."""
        try:
            plan_data = json.loads(plan_response)
            return plan_data.get("steps", [])
        except json.JSONDecodeError:
            return self._parse_text_steps(plan_response)
    
    def _parse_text_steps(self, text: str) -> list[dict]:
        """Parse steps from plain text format."""
        steps = []
        lines = text.split("\n")
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("//"):
                continue
            
            tool = None
            params = {}
            
            if "terminal" in line.lower() or "bash" in line.lower() or "command" in line.lower():
                tool = "terminal"
                params = {"command": line.split("```")[-1].strip() if "```" in line else line}
            elif "search" in line.lower() or "google" in line.lower() or "find" in line.lower():
                tool = "tavily_search"
                params = {"query": line.split("search")[-1].strip() if "search" in line.lower() else line}
            elif "file" in line.lower() or "write" in line.lower() or "create" in line.lower():
                tool = "file"
                params = {"action": "write", "path": "/tmp/output.txt", "content": line}
            else:
                tool = "terminal"
                params = {"command": line}
            
            steps.append({
                "description": line,
                "tool": tool,
                "params": params
            })
        
        return steps
    
    async def self_correct(self, failed_step: dict, error: str, context: list[ToolResult]) -> dict:
        """Attempt to self-correct after a failed step."""
        self.thoughts.append(AgentThought(
            timestamp=datetime.utcnow(),
            thinking=f"Analyzing failure: {error}",
            state=AgentState.PLANNING,
            tool_used=None
        ))
        
        context_summary = "\n".join([
            f"- {r.tool_name}: {'SUCCESS' if r.success else 'FAILED'}: {r.output[:100] if r.output else r.error}"
            for r in context[-5:]
        ])
        
        correction_prompt = f"""The following step failed:
Step: {failed_step.get('description', 'Unknown')}
Tool: {failed_step.get('tool', 'Unknown')}
Error: {error}

Previous context:
{context_summary}

Task: {self.description}

Suggest an alternative approach. Return JSON:
{{
    "analysis": "Why this failed",
    "alternative": "What to try instead",
    "new_tool": "tool_name or null",
    "new_params": {{}} or null
}}"""
        
        try:
            response = await self.think(correction_prompt, role=ModelRole.PLANNING)
            correction = json.loads(response)
            
            if correction.get("new_tool"):
                self.thoughts.append(AgentThought(
                    timestamp=datetime.utcnow(),
                    thinking=f"Correction: Using {correction['new_tool']} instead",
                    state=AgentState.PLANNING,
                    tool_used=correction["new_tool"]
                ))
                
                return {
                    "description": correction.get("alternative", failed_step.get("description")),
                    "tool": correction["new_tool"],
                    "params": correction.get("new_params", {})
                }
        except:
            pass
        
        return {
            "description": f"Retry: {failed_step.get('description', 'Unknown')}",
            "tool": failed_step.get("tool", "terminal"),
            "params": failed_step.get("params", {})
        }
    
    async def run(self) -> AsyncGenerator[dict, None]:
        """Run the complete agent loop with self-correction."""
        try:
            self.state = AgentState.PLANNING
            
            yield {
                "type": "status",
                "content": "🚀 Manus initializing...",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.initialize()
            
            yield {
                "type": "status", 
                "content": f"📦 Tools loaded: {[t['name'] for t in self.tools.list_tools()]}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Phase 1: Planning
            yield {
                "type": "thought",
                "content": "🧠 Planning task decomposition...",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            plan_response = await self.think(
                f"{self.PLANNING_PROMPT}\n\nTask: {self.description}",
                role=ModelRole.PLANNING
            )
            
            yield {
                "type": "thought",
                "content": f"📋 Plan generated:\n{plan_response[:500]}...",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.steps = await self.parse_steps(plan_response)
            
            if not self.steps:
                self.steps = [{
                    "description": f"Execute task: {self.description}",
                    "tool": "terminal",
                    "params": {"command": f"echo 'Task: {self.description}'"}
                }]
            
            yield {
                "type": "status",
                "content": f"📌 Executing {len(self.steps)} steps",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Phase 2: Execution with self-correction
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
                    "content": f"⚡ Step {self.current_step}/{len(self.steps)}: {step.get('description', 'Unknown')[:80]}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                result = await self.execute_tool(
                    step.get("tool", "terminal"),
                    step.get("params", {}),
                    step.get("description", "Unknown step")
                )
                
                self.results.append(result)
                
                if result.success:
                    yield {
                        "type": "success",
                        "content": f"✅ {result.tool_name}: {result.output[:300]}",
                        "timestamp": datetime.utcnow().isoformat(),
                        "metadata": {
                            "tool": result.tool_name,
                            "execution_time_ms": result.execution_time_ms,
                            "retries": result.retry_count
                        }
                    }
                else:
                    yield {
                        "type": "warning",
                        "content": f"⚠️ {result.tool_name} failed: {result.error}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    if result.retry_count > 0:
                        corrected_step = await self.self_correct(step, result.error, self.results)
                        
                        yield {
                            "type": "thought",
                            "content": "🔧 Attempting self-correction...",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        
                        corrected_result = await self.execute_tool(
                            corrected_step.get("tool", "terminal"),
                            corrected_step.get("params", {}),
                            corrected_step.get("description", "Corrected step")
                        )
                        
                        if corrected_result.success:
                            yield {
                                "type": "success",
                                "content": f"✅ Self-corrected: {corrected_result.output[:300]}",
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            self.results.append(corrected_result)
                        else:
                            yield {
                                "type": "error",
                                "content": f"❌ Self-correction failed: {corrected_result.error}",
                                "timestamp": datetime.utcnow().isoformat()
                            }
                
                await self.supabase.update_task(
                    self.task_id,
                    metadata={
                        "current_step": self.current_step,
                        "total_steps": len(self.steps),
                        "progress": self.current_step / len(self.steps),
                        "last_tool": result.tool_name,
                        "last_success": result.success
                    }
                )
            
            # Phase 3: Completion
            self.state = AgentState.COMPLETE
            
            success_count = sum(1 for r in self.results if r.success)
            total_time = sum(r.execution_time_ms for r in self.results)
            
            final_result = {
                "completed_steps": success_count,
                "total_steps": len(self.steps),
                "total_execution_time_ms": total_time,
                "results": [
                    {"tool": r.tool_name, "success": r.success, "output": r.output[:500], "error": r.error}
                    for r in self.results
                ],
                "thoughts": len(self.thoughts)
            }
            
            yield {
                "type": "result",
                "content": f"🎉 Task completed! {success_count}/{len(self.steps)} steps successful.",
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": final_result
            }
            
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
                "content": f"💥 Agent failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
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
                "success": t.success
            }
            for t in self.thoughts
        ]


# Keep legacy class name for compatibility
AgentLoop = AutonomousAgent
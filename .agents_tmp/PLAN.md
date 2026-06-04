# 1. OBJECTIVE

**Primary Goal:** Build a production-ready AI Agent OS MVP in **8-10 weeks** using the user's locked-in managed services stack.

**Target Capabilities:**
- Autonomous task execution in E2B cloud sandboxes
- Real-time streaming of agent thoughts/terminal via WebSocket + xterm.js
- Long-term memory via Supabase pgvector
- Async task processing via Upstash Redis
- Multi-model AI gateway (Gemini/Claude for planning, Llama/DeepSeek for execution)
- Google Workspace integration (Drive, Sheets, Docs) inside sandbox

---

# 2. CONTEXT SUMMARY

## Your Stack — Architecture Mapping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (Vercel)                                 │
│              Next.js 14 + WebSocket + xterm.js                              │
│         User Dashboard │ Live Activity Monitor │ Results View              │
└────────────────────────────┬───────────────────────────────────────────────┘
                             │ HTTPS / WebSocket
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       BACKEND ENGINE (HuggingFace Spaces)                    │
│                      FastAPI in Docker Container                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Task Handler  │  │ Agent Loop   │  │ Tool Router  │  │ Session Mgr  │    │
│  │ (REST API)    │  │ (Orchestrate)│  │ (Google APIs)│  │ (State/Check)│    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└────────────────────────────┬───────────────────────────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  UPSTASH REDIS  │  │    E2B SANDBOX  │  │    SUPABASE     │
│  (Task Queue)   │  │  (Firecracker)  │  │  (pgvector DB)  │
│                 │  │                 │  │                 │
│ BullMQ for      │  │ Agent executes  │  │ Session memory  │
│ async jobs      │  │ here            │  │ Vector search   │
│                 │  │                 │  │ User data       │
└─────────────────┘  └────────┬────────┘  └────────┬────────┘
                               │                    │
                               ▼                    │
                    ┌──────────────────┐            │
                    │   AI GATEWAY     │◄───────────┘
                    │                  │
                    ├──────────────────┤
                    │ PLANNING MODELS  │  EXECUTION MODELS
                    │ ──────────────── │  ────────────────
                    │ Gemini 1.5 Pro   │  SambaNova (Llama-3)
                    │ Claude 3.5 Sonnet│  GitHub Models (DeepSeek)
                    │ (via OpenRouter)  │
                    └──────────────────┘
```

## Component Communication Flow (Standard Agent Loop)

```
1. USER SUBMITS TASK
   └── Frontend (Vercel) → POST /api/tasks
                           ↓
2. TASK ENQUEUED
   └── FastAPI → Upstash Redis (BullMQ job)
                ↓
3. SANDBOX ALLOCATED
   └── FastAPI → E2B SDK.createSandbox()
                ↓
4. PLANNING PHASE
   └── E2B Sandbox → Gemini 1.5 Pro (task decomposition)
                   → Claude 3.5 Sonnet (refinement)
                ↓
5. EXECUTION PHASE (loop until done)
   ├── E2B → SambaNova/Llama (code generation, parsing)
   ├── E2B → Tool calls (browser, terminal, file ops)
   ├── E2B → Google APIs (Drive/Sheet ops)
   └── Real-time: E2B → WebSocket → Frontend (live streaming)
                ↓
6. MEMORY STORE
   └── E2B → Supabase (session state, vector embeddings)
                ↓
7. TASK COMPLETE
   └── FastAPI → Supabase (final results)
   └── WebSocket → Frontend (notification + results)
```

---

# 3. APPROACH OVERVIEW

## Why This Stack Cuts Timeline from 24 weeks → 8-10 weeks

| Previous Plan (24 weeks) | New Plan (8-10 weeks) | Why |
|-------------------------|------------------------|-----|
| Custom Firecracker setup (Weeks 1-4) | E2B SDK (Days 1-3) | Pre-built, managed |
| Kubernetes cluster setup | HuggingFace Spaces Docker | Managed K8s |
| PostgreSQL + pgvector install | Supabase (one-click) | Managed DB |
| Redis cluster + BullMQ | Upstash Redis (serverless) | Zero-ops |
| Custom WebSocket server | Vercel native + FastAPI | Built-in |
| Custom terminal emulator | xterm.js integration | Drop-in |

## MVP Scope (8 weeks)

**Must-have for launch:**
- Task submission via natural language
- E2B sandbox execution with browser + terminal
- Real-time activity streaming to dashboard
- Basic memory (session persistence)
- 3-5 core tools (web search, file ops, code execution)
- Claude 3.5 Sonnet integration

**Post-MVP (Weeks 9-10):**
- Gemini 1.5 Pro planning
- SambaNova/Llama execution layer
- Google Workspace integration
- pgvector semantic memory
- Multi-agent orchestration

---

# 4. IMPLEMENTATION STEPS

## PHASE 0: Environment Setup (Days 1-3)

### Step 0.1: Repository & Stack Initialization

**Goal:** Set up project structure and verify all services work.

**Method:**
1. Create monorepo: `frontend/` (Next.js) + `backend/` (FastAPI)
2. Configure environment variables for all services
3. Verify credentials: E2B API key, Supabase, Upstash, Google Service Account
4. Test connectivity: Backend → E2B, Supabase, Upstash

**Reference Files:**
- `.env.example` — All environment variables template
- `docker/Dockerfile` — FastAPI container
- `docker/docker-compose.yml` — Local dev stack

**Required Env Vars:**
```bash
# E2B
E2B_API_KEY=xxx

# Supabase
SUPABASE_URL=xxx
SUPABASE_KEY=xxx

# Upstash Redis
UPSTASH_REDIS_REST_URL=xxx
UPSTASH_REDIS_REST_TOKEN=xxx

# AI Providers
GEMINI_API_KEY=xxx
OPENROUTER_API_KEY=xxx
SAMBANOVA_API_KEY=xxx
GITHUB_TOKEN=xxx

# Google
GOOGLE_APPLICATION_CREDENTIALS=/app/service-account.json
```

### Step 0.2: Supabase Schema Setup

**Goal:** Initialize database tables and vector extensions.

**Method:**
1. Enable pgvector extension
2. Create tables:
   - `users` — User accounts & preferences
   - `sessions` — Agent sessions with metadata
   - `task_history` — Completed task records
   - `memory_embeddings` — Vector store for semantic memory
   - `tool_configs` — Custom tool definitions

**SQL Schema:**
```sql
-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sessions table
CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  status TEXT DEFAULT 'active',
  sandbox_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Memory embeddings (for semantic search)
CREATE TABLE memory_embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES sessions(id),
  content TEXT,
  embedding vector(1536),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for vector similarity search
CREATE INDEX ON memory_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

---

## PHASE 1: Backend Core (Weeks 1-2)

### Step 1.1: FastAPI Project Structure

**Goal:** Build the FastAPI backend on HuggingFace Spaces.

**Method:**
1. Create FastAPI app with router structure
2. Implement core routes:
   - `POST /api/tasks` — Submit new task
   - `GET /api/tasks/{id}` — Get task status
   - `GET /api/tasks/{id}/stream` — WebSocket for live updates
   - `DELETE /api/tasks/{id}` — Cancel task
3. Add health check endpoint
4. Configure CORS for Vercel frontend

**Reference:**
- `backend/main.py` — FastAPI app entry point
- `backend/api/routes/` — API route handlers
- `backend/core/` — Business logic

**Directory Structure:**
```
backend/
├── main.py
├── api/
│   ├── __init__.py
│   ├── tasks.py       # Task endpoints
│   └── sessions.py    # Session endpoints
├── core/
│   ├── agent.py       # Agent orchestration
│   ├── sandbox.py     # E2B wrapper
│   ├── llm.py         # AI gateway
│   └── tools/         # Tool implementations
├── db/
│   ├── supabase.py    # Supabase client
│   └── redis.py       # Upstash client
└── models/
    ├── task.py
    └── session.py
```

### Step 1.2: E2B Sandbox Integration

**Goal:** Connect FastAPI to E2B for sandbox execution.

**Method:**
1. Install E2B SDK: `pip install e2b`
2. Implement sandbox manager:
   - `SandboxManager.create(task_id)` — Spawn new sandbox
   - `SandboxManager.execute(code)` — Run code in sandbox
   - `SandboxManager.stream()` — Get terminal output
   - `SandboxManager.destroy()` — Clean up
3. Implement sandbox lifecycle in task handler
4. Add timeout and resource limits

**Reference:**
- `backend/core/sandbox.py` — E2B wrapper class
- `backend/core/agent.py` — Main agent loop

**E2B Sandbox Template (for custom environments):**
```python
from e2b import Sandbox

# Create sandbox with Ubuntu + tools
sandbox = await Sandbox.create(
    template="ubuntu",
    metadata={"task_id": task_id}
)

# Install tools inside sandbox
await sandbox.commands.run("apt-get install -y chromium-browser")
await sandbox.commands.run("pip install playwright")
await sandbox.commands.run("npm install -g playwright")
```

### Step 1.3: Upstash Redis Task Queue

**Goal:** Implement async task processing with BullMQ pattern.

**Method:**
1. Install Upstash SDK: `pip install upstash-redis`
2. Create task queue wrapper:
   - `TaskQueue.enqueue(task_data)` — Add task to queue
   - `TaskQueue.dequeue()` — Get next task (worker)
   - `TaskQueue.update_status(task_id, status)` — Update progress
3. Implement task worker that:
   - Dequeues tasks from Redis
   - Creates E2B sandbox
   - Runs agent loop
   - Updates status in Supabase
4. Configure retry logic and dead-letter queue

**Reference:**
- `backend/workers/task_worker.py` — Background worker
- `backend/db/redis.py` — Upstash client

### Step 1.4: AI Gateway Implementation

**Goal:** Abstract multi-model routing for planning vs execution.

**Method:**
1. Create LLM gateway with provider abstraction
2. Implement model routers:
   - **Planning Router**: Gemini 1.5 Pro, Claude 3.5 Sonnet
   - **Execution Router**: SambaNova (Llama-3), GitHub Models (DeepSeek)
3. Add prompt templates for each use case
4. Implement fallback chain (if primary fails, try next)
5. Add cost tracking per model

**Reference:**
- `backend/core/llm/gateway.py` — Unified LLM interface
- `backend/core/llm/providers/` — Provider implementations
- `backend/core/llm/prompts/` — Prompt templates

**Model Selection Logic:**
```python
async def select_model(task_type: str) -> str:
    if task_type in ["planning", "reasoning", "analysis"]:
        # Use high-logic models
        return await try_models(["gemini-1.5-pro", "claude-3.5-sonnet"])
    elif task_type in ["code", "parsing", "fast-response"]:
        # Use fast execution models
        return await try_models(["llama-3-samba", "deepseek-coder"])
```

---

## PHASE 2: Agent Loop (Weeks 3-4)

### Step 2.1: Core Agent Loop Implementation

**Goal:** Implement the Analyze → Plan → Execute → Observe loop.

**Method:**
1. Build `AgentLoop` class:
   - `analyze(task)` — Initial task understanding
   - `plan()` — Decompose into steps
   - `execute(step)` — Run step in sandbox
   - `observe()` — Check results, adapt
   - `complete()` — Finalize and store results
2. Implement state machine with checkpoints
3. Add error handling and recovery
4. Implement step-by-step logging

**Reference:**
- `backend/core/agent.py` — Main agent class
- `backend/core/agent_loop.py` — Loop implementation

**Agent Loop Pseudocode:**
```python
class AgentLoop:
    async def run(self, task: Task):
        self.log("Analyzing task...")
        context = await self.analyze(task)
        
        self.log("Planning steps...")
        plan = await self.planner.create_plan(context)
        
        for step in plan.steps:
            self.log(f"Executing: {step.description}")
            result = await self.execute_step(step)
            
            if not result.success:
                self.log("Adapting approach...")
                plan = await self.planner.replan(result.error)
            
            await self.save_checkpoint(step, result)
        
        return await self.complete(plan.results)
```

### Step 2.2: Tool System

**Goal:** Implement the 27 tools Manus uses (or core subset for MVP).

**Method:**
1. Create tool registry with schema definitions
2. Implement MVP tools (core 8):
   - **WebBrowser** — Playwright-based (uses Chromium in E2B)
   - **Terminal** — Bash command execution
   - **FileSystem** — Read/write/list files
   - **CodeInterpreter** — Python/Node.js execution
   - **WebSearch** — SerpAPI or DuckDuckGo
   - **GoogleDrive** — File upload/download via Service Account
   - **GoogleSheets** — Read/write spreadsheet data
   - **WebpageCapture** — Screenshot and content extraction

3. Add tool permissioning and rate limiting
4. Implement tool chaining for complex operations

**Reference:**
- `backend/core/tools/base.py` — Tool base class
- `backend/core/tools/browser.py` — Playwright implementation
- `backend/core/tools/google.py` — Google Workspace tools

**Tool Definition Schema:**
```python
class Tool:
    name: str
    description: str
    parameters: dict  # JSON schema
    permissions: list[str]  # e.g., ["google-drive", "browser"]
    
    async def execute(self, params: dict, sandbox: Sandbox) -> ToolResult:
        pass
```

### Step 2.3: Session & Memory Management

**Goal:** Implement persistent context across tasks.

**Method:**
1. Create session manager:
   - `Session.create(user_id)` — New session
   - `Session.save_state()` — Persist to Supabase
   - `Session.restore(session_id)` — Resume session
   - `Session.summarize()` — Context compression for long tasks

2. Implement memory layers:
   - **Working Memory** — Current task context (Redis)
   - **Short-term** — Session history (Supabase)
   - **Long-term** — Semantic embeddings (pgvector)

3. Add context window management (avoid token overflow)

**Reference:**
- `backend/core/memory.py` — Memory manager
- `backend/db/supabase.py` — Database client

### Step 2.4: WebSocket Streaming

**Goal:** Real-time updates from agent to frontend.

**Method:**
1. Implement WebSocket handler in FastAPI
2. Create event types:
   - `thought` — Agent thinking/reasoning
   - `action` — Tool being executed
   - `observation` — Result of action
   - `error` — Something went wrong
   - `complete` — Task finished

3. Bridge E2B terminal output to WebSocket
4. Add reconnection handling on frontend

**Reference:**
- `backend/api/websocket.py` — WebSocket handler
- `frontend/hooks/useAgentStream.ts` — React hook

**WebSocket Message Schema:**
```json
{
  "type": "action",
  "timestamp": "2025-01-15T10:30:00Z",
  "data": {
    "tool": "WebBrowser",
    "action": "navigate",
    "target": "https://example.com",
    "status": "in_progress"
  }
}
```

---

## PHASE 3: Frontend (Weeks 5-6)

### Step 3.1: Next.js Project Setup

**Goal:** Set up Vercel-hosted Next.js 14 application.

**Method:**
1. Create Next.js 14 app with App Router
2. Configure Tailwind CSS + shadcn/ui components
3. Set up environment variables for API endpoint
4. Implement authentication (NextAuth.js or Supabase Auth)
5. Configure Vercel deployment settings

**Reference:**
- `frontend/` — Next.js application
- `frontend/app/page.tsx` — Landing/task input
- `frontend/app/dashboard/` — User dashboard

### Step 3.2: Task Input Interface

**Goal:** Build natural language task submission UI.

**Method:**
1. Create task input component with:
   - Text area for task description
   - File upload support (for context)
   - Optional: task type selector
2. Implement task submission flow:
   - Validate input
   - POST to backend API
   - Start WebSocket connection
   - Show loading state with progress

**Reference:**
- `frontend/components/task-input.tsx`
- `frontend/lib/api.ts` — API client

### Step 3.3: "Manus's Computer" Live Monitor

**Goal:** Real-time activity panel with terminal + actions.

**Method:**
1. Implement WebSocket client hook
2. Build activity panel with:
   - **Thought Stream** — Agent's reasoning (scrollable)
   - **Terminal View** — Live xterm.js terminal
   - **Action Timeline** — Step-by-step actions
   - **Resource Monitor** — Sandbox CPU/memory

3. Integrate xterm.js for terminal emulation
4. Add screen capture viewer (if E2B supports screenshots)

**Reference:**
- `frontend/components/activity-panel.tsx`
- `frontend/components/terminal-view.tsx` — xterm.js integration
- `frontend/hooks/useAgentStream.ts` — WebSocket hook

**Terminal Integration:**
```tsx
import { Terminal } from 'xterm'
import { WebLinksAddon } from 'xterm-addon-web-links'
import 'xterm/css/xterm.css'

const TerminalView = ({ sessionId }) => {
  const terminal = useRef<Terminal>(null)
  
  useEffect(() => {
    const ws = new WebSocket(`${API_URL}/tasks/${sessionId}/stream`)
    ws.onmessage = (event) => {
      terminal.current?.write(event.data)
    }
  }, [sessionId])
  
  return <Terminal ref={terminal} />
}
```

### Step 3.4: Results View & History

**Goal:** Display completed task results.

**Method:**
1. Build results viewer:
   - Markdown/text rendering
   - File download links
   - Code syntax highlighting
   - Image gallery for screenshots
2. Implement task history page:
   - List of past tasks with status
   - Re-run functionality
   - Share/export options

**Reference:**
- `frontend/app/dashboard/results/[id].tsx`
- `frontend/app/dashboard/history.tsx`

---

## PHASE 4: Integration & Testing (Weeks 7-8)

### Step 4.1: End-to-End Integration

**Goal:** Verify all components work together.

**Method:**
1. Connect frontend → backend → E2B flow
2. Test WebSocket streaming
3. Verify Supabase data persistence
4. Test Upstash task queue processing
5. Validate AI gateway model routing

### Step 4.2: MVP Feature Testing

**Goal:** Validate core functionality with test tasks.

**Test Scenarios:**
1. **Research Task**: "Find top 5 competitors of Tesla and summarize their pricing"
2. **Data Analysis**: "Upload this CSV and give me 5 key insights"
3. **Code Generation**: "Write a Python script that automates X"
4. **Web Scraping**: "Extract all job listings from this site"
5. **Google Integration**: "Create a new Google Sheet with this data"

### Step 4.3: Performance & Error Handling

**Goal:** Ensure system is production-ready.

**Method:**
1. Test concurrent task handling (10+ simultaneous)
2. Implement circuit breakers for API failures
3. Add retry logic for E2B sandbox creation
4. Set up monitoring (error tracking, latency)
5. Test WebSocket reconnection handling

### Step 4.4: Vercel & HuggingFace Deployment

**Goal:** Deploy to production endpoints.

**Method:**
1. Deploy FastAPI to HuggingFace Spaces
2. Configure custom subdomain
3. Deploy Next.js to Vercel
4. Set up environment variables in both platforms
5. Configure CORS for cross-origin requests

---

## POST-MVP ENHANCEMENTS (Weeks 9-10)

### Week 9: Advanced AI Features

| Feature | Implementation |
|---------|----------------|
| **Gemini 1.5 Pro Planning** | Implement planning agent with Gemini for complex task decomposition |
| **SambaNova/Llama Execution** | Route code generation to Llama-3 for speed |
| **pgvector Semantic Memory** | Implement vector similarity search for context retrieval |

### Week 10: Enterprise Tools

| Feature | Implementation |
|---------|----------------|
| **Google Workspace Full** | Complete Drive, Sheets, Docs, Gmail integration |
| **Multi-Agent Orchestration** | Implement parallel executor agents |
| **Custom Tool Builder** | UI for users to define custom tools |
| **Analytics Dashboard** | Usage tracking, cost analysis, performance metrics |

---

# 5. TESTING AND VALIDATION

## Validation Checklist

| Component | Test | Success Criteria |
|-----------|------|------------------|
| E2B Sandbox | Create and destroy sandbox | < 5 seconds |
| Task Queue | Enqueue and process task | Task executes in sandbox |
| WebSocket | Stream terminal output | < 500ms latency |
| Supabase | Save and retrieve session | Data persists |
| AI Gateway | Route to different models | Correct model called |
| Frontend | Submit task and see results | Full flow works |

## Test Scenarios

### Scenario 1: Simple Task
```
User: "What is 2+2?"
Expected: Agent calculates in sandbox, returns "4"
Time: < 10 seconds
```

### Scenario 2: Research Task
```
User: "Find the latest news about AI agents"
Expected: Agent browses web, extracts info, summarizes
Time: < 2 minutes
```

### Scenario 3: Code Generation
```
User: "Write a Python script to sort a list"
Expected: Agent generates code, executes in sandbox, shows output
Time: < 30 seconds
```

### Scenario 4: Long-Running Task
```
User: "Research and write a 5-page report on renewable energy"
Expected: Agent works for 10+ minutes, user sees progress, gets complete report
Time: 10-20 minutes
```

---

# APPENDIX: Full Stack Mapping

## Component → Service Assignment

| Component | Service | Responsibility |
|-----------|---------|-----------------|
| **Frontend** | Vercel (Next.js) | User interface, WebSocket client, xterm.js terminal |
| **Backend API** | HuggingFace Spaces (FastAPI) | Task handling, agent orchestration, tool routing |
| **Task Queue** | Upstash Redis | Async job processing, status tracking |
| **Sandbox Runtime** | E2B (Firecracker) | Agent code execution, browser, terminal |
| **Database** | Supabase (PostgreSQL + pgvector) | User data, session storage, vector memory |
| **LLM Planning** | Gemini 1.5 Pro / Claude 3.5 Sonnet | Task planning, reasoning, complex decisions |
| **LLM Execution** | SambaNova / GitHub Models | Code generation, fast parsing, bulk operations |
| **Google Tools** | Google Service Account | Drive, Sheets, Docs operations in sandbox |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/tasks` | Create new task |
| `GET` | `/api/tasks/{id}` | Get task status |
| `DELETE` | `/api/tasks/{id}` | Cancel task |
| `WS` | `/api/tasks/{id}/stream` | WebSocket for live updates |
| `GET` | `/api/sessions/{id}` | Get session details |
| `POST` | `/api/sessions/{id}/memory` | Store memory in vector DB |
| `GET` | `/api/tools` | List available tools |
| `POST` | `/api/tools/execute` | Execute custom tool |

## Estimated Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 0 | 3 days | Dev environment, Supabase schema |
| Phase 1 | 2 weeks | FastAPI backend, E2B integration, Upstash queue, AI gateway |
| Phase 2 | 2 weeks | Agent loop, tool system, memory, WebSocket streaming |
| Phase 3 | 2 weeks | Next.js frontend, live monitor, results view |
| Phase 4 | 2 weeks | Integration, testing, deployment |
| **Total** | **8 weeks** | **Production MVP** |

## Team Recommendation

| Role | Count | Focus |
|------|-------|-------|
| Backend Engineer | 1-2 | FastAPI, E2B, AI gateway |
| Frontend Engineer | 1 | Next.js, WebSocket, UI |
| AI/ML Engineer | 1 | Agent loop, prompt engineering |
| **Total** | **3-4** | |

---

**Ready to proceed?** Click **Build** below to start implementing this 8-week MVP plan with your exact managed services stack.

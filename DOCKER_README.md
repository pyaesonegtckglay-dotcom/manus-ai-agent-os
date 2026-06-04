# Manus AI Agent OS - Docker Deployment

A fully autonomous AI agent like Manus AI, capable of planning, executing, and self-correcting tasks.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Network                         │
│                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────┐  │
│  │   Frontend   │────▶│   Backend   │────▶│   E2B      │  │
│  │   (Next.js)  │◀────│   (FastAPI)  │◀────│  Sandbox   │  │
│  │   :3000      │     │   :8000      │     │            │  │
│  └──────────────┘     └──────────────┘     └────────────┘  │
│         │                    │                     │        │
│         │                    ▼                     ▼        │
│         │            ┌──────────────┐     ┌────────────┐  │
│         │            │  Supabase DB  │     │  Tavily    │  │
│         │            │              │     │  Search    │  │
│         │            └──────────────┘     └────────────┘  │
│         │                                                  │
│         ▼                                                  │
│  ┌──────────────┐                                          │
│  │    Nginx    │                                          │
│  │  Reverse    │                                          │
│  │   Proxy     │                                          │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

## Features

- 🤖 **Autonomous Agent** - Plans, executes, and self-corrects tasks
- 🌐 **Web Search** - Tavily AI-powered search, extraction, and crawling
- 🖥️ **Sandbox Execution** - E2B sandbox for safe terminal commands
- 🔧 **Browser Automation** - Playwright for web interactions
- 🧠 **AI Gateway** - Multi-model support via OpenRouter
- ⚡ **Real-time Streaming** - WebSocket support for live updates
- 🔄 **Task Queue** - Upstash Redis for async processing

## Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### 1. Clone and Setup

```bash
git clone https://github.com/pyaesonegtckglay-dotcom/manus-ai-agent-os.git
cd manus-ai-agent-os

# Copy environment variables
cp .env.example .env
# Edit .env with your actual API keys
```

### 2. Start Services

```bash
# Build and start all services
docker-compose up -d --build

# Or run in foreground for debugging
docker-compose up --build
```

### 3. Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Nginx Proxy:** http://localhost:80

## Docker Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild services
docker-compose up -d --build --no-cache

# Remove all containers and volumes
docker-compose down -v
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `E2B_API_KEY` | E2B Sandbox API key | ✅ |
| `SUPABASE_KEY` | Supabase anon key | ✅ |
| `SUPABASE_SERVICE_KEY` | Supabase service key | ✅ |
| `UPSTASH_REDIS_REST_TOKEN` | Upstash Redis token | ✅ |
| `OPENROUTER_API_KEY` | OpenRouter API key | ✅ |
| `TAVILY_API_KEY` | Tavily search API key | ✅ |

## Available Tools

| Tool | Description |
|------|-------------|
| **terminal** | Execute shell commands in E2B sandbox |
| **file** | Read/write files in sandbox |
| **tavily_search** | AI-powered web search |
| **tavily_extract** | Extract content from URLs |
| **tavily_crawl** | Crawl entire websites |
| **playwright_browser** | Full browser automation |

## API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /api/tasks` - Create new task
- `GET /api/tasks/{id}` - Get task status
- `WS /ws/tasks/{id}/stream` - WebSocket for real-time streaming

## Development

### Run locally without Docker

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Debug Backend in Docker

```bash
# Enter backend container
docker exec -it manus-backend bash

# Check logs
docker logs -f manus-backend
```

## Production Deployment

For production, use:

1. **Cloud Platforms:** AWS ECS, Google Cloud Run, Azure Container Instances
2. **Orchestration:** Kubernetes, Docker Swarm
3. **CI/CD:** GitHub Actions, GitLab CI

### Example: Deploy to Railway

```bash
# Connect GitHub repo to Railway
# Add environment variables in Railway dashboard
# Deploy "manus-backend" and "manus-frontend" services
```

### Example: Deploy to Fly.io

```bash
fly launch
fly secrets set E2B_API_KEY=your_key
fly deploy
```

## License

MIT
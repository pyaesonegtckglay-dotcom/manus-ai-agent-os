# Manus AI Agent OS

## Hugging Face Space Deployment

### Quick Start

1. **Create a new Space** at [hf.co/new-space](https://hf.co/new-space)
2. **Select SDK**: Gradio
3. **Select Hardware**: t4-small (or higher for better performance)
4. **Import from GitHub**: Connect your repo or upload files

### Required Environment Variables

Set in Space Settings:
- `E2B_API_KEY` - E2B Sandbox API key
- `SUPABASE_KEY` - Supabase anon key  
- `SUPABASE_SERVICE_KEY` - Supabase service key
- `UPSTASH_REDIS_REST_TOKEN` - Upstash Redis token
- `OPENROUTER_API_KEY` - OpenRouter API key
- `TAVILY_API_KEY` - Tavily search API key

### Files Required

- `app.py` - Gradio interface (entry point)
- `backend/` - FastAPI backend with tools
- `backend/requirements.txt` - Python dependencies
- `huggingface-space.json` - Space configuration

### Features

- 🌐 Web search with Tavily AI
- 🖥️ Terminal command execution
- 📁 File operations in sandbox
- 🔧 Browser automation with Playwright
- ⚡ Real-time progress streaming
- 🔄 Automatic retry and self-correction

## Local Development

```bash
pip install -r backend/requirements.txt
python app.py
# Opens at http://localhost:7860
```

## Backend API

The backend runs as a FastAPI server alongside the Gradio interface.

**Endpoints:**
- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /api/tasks` - Create a task
- `GET /api/tasks/{id}` - Get task status
- `WS /api/tasks/{id}/stream` - WebSocket for real-time streaming

## Architecture

```
app.py (Gradio)
    └── backend/ (FastAPI)
            ├── utils/agent_loop.py (AutonomousAgent)
            ├── utils/tools.py (ToolRegistry)
            └── services/
                    ├── e2b.py (Sandbox)
                    ├── ai_gateway.py (AI providers)
                    └── supabase.py (Database)
```

## License

MIT
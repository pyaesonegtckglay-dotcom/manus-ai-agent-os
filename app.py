"""
Manus AI Agent OS - Hugging Face Space Entry Point
A Gradio interface for the autonomous AI agent with web search and sandbox execution.
"""
import os
import sys
import json
import asyncio
import gradio as gr
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.main import app as fastapi_app
from backend.utils.agent_loop import AutonomousAgent
from backend.services import get_e2b, get_ai_gateway, get_supabase

# Initialize services
e2b = get_e2b()
ai = get_ai_gateway()
supabase = get_supabase()

# Global state
current_task_id = None
task_history = []


def get_tools_description():
    """Return available tools description."""
    return """
## Available Tools

| Tool | Description |
|------|-------------|
| **terminal** | Execute shell commands, run scripts |
| **file** | Read, write, list files in sandbox |
| **tavily_search** | Search the web with AI-powered results |
| **tavily_extract** | Extract content from URLs |
| **tavily_crawl** | Crawl entire websites |
| **playwright_browser** | Full browser automation |

## Features

- Multi-step task planning
- Automatic retry on failures (3 attempts)
- Self-correction on errors
- Real-time progress updates
"""


async def run_agent_task(task_description: str, progress_callback=None):
    """Run the autonomous agent on a task."""
    global current_task_id, task_history
    
    results = []
    task_id = f"hf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    current_task_id = task_id
    
    try:
        # Create sandbox
        if progress_callback:
            await progress_callback("🔧 Creating sandbox environment...")
        
        sandbox = await e2b.create_sandbox(task_id)
        results.append("✅ Sandbox created")
        
        # Get Tavily API key
        tavily_api_key = os.environ.get("TAVILY_API_KEY")
        
        # Create and run agent
        if progress_callback:
            await progress_callback("🚀 Initializing Manus agent...")
        
        agent = AutonomousAgent(
            task_id=task_id,
            description=task_description,
            sandbox=sandbox,
            tavily_api_key=tavily_api_key,
            enable_playwright=True
        )
        
        # Run agent
        async for event in agent.run():
            event_type = event.get("type", "")
            content = event.get("content", "")
            
            if event_type == "status":
                results.append(f"📦 {content}")
                if progress_callback:
                    await progress_callback(content)
            elif event_type == "thought":
                results.append(f"🧠 {content}")
            elif event_type == "action":
                results.append(f"⚡ {content}")
                if progress_callback:
                    await progress_callback(content)
            elif event_type == "success":
                results.append(f"✅ {content}")
            elif event_type == "warning":
                results.append(f"⚠️ {content}")
            elif event_type == "error":
                results.append(f"❌ {content}")
            elif event_type == "result":
                results.append(f"🎉 {content}")
                if progress_callback:
                    await progress_callback("complete")
        
        # Cleanup
        await e2b.destroy_sandbox(sandbox)
        
        # Add to history
        task_history.append({
            "task": task_description,
            "results": results,
            "timestamp": datetime.now().isoformat()
        })
        
        return "\n".join(results)
        
    except Exception as e:
        error_msg = f"💥 Error: {str(e)}"
        results.append(error_msg)
        return "\n".join(results)


def gradio_run_task(task_description, status_placeholder):
    """Gradio wrapper for running tasks."""
    async def async_run():
        results = []
        task_id = f"hf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Create sandbox
            sandbox = await e2b.create_sandbox(task_id)
            results.append("✅ Sandbox created")
            
            tavily_api_key = os.environ.get("TAVILY_API_KEY")
            
            agent = AutonomousAgent(
                task_id=task_id,
                description=task_description,
                sandbox=sandbox,
                tavily_api_key=tavily_api_key,
                enable_playwright=True
            )
            
            async for event in agent.run():
                content = event.get("content", "")
                event_type = event.get("type", "")
                
                if event_type == "status":
                    results.append(f"📦 {content}")
                    status_placeholder = content
                elif event_type == "thought":
                    results.append(f"🧠 {content}")
                elif event_type == "action":
                    results.append(f"⚡ {content}")
                elif event_type == "success":
                    results.append(f"✅ {content}")
                elif event_type == "warning":
                    results.append(f"⚠️ {content}")
                elif event_type == "error":
                    results.append(f"❌ {content}")
                elif event_type == "result":
                    results.append(f"🎉 {content}")
            
            await e2b.destroy_sandbox(sandbox)
            
            task_history.append({
                "task": task_description,
                "results": results,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            results.append(f"💥 Error: {str(e)}")
        
        return "\n".join(results)
    
    return asyncio.run(async_run())


def gradio_stream_task(task_description, progress_display):
    """Gradio streaming version."""
    async def stream_results():
        results = []
        task_id = f"hf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            sandbox = await e2b.create_sandbox(task_id)
            results.append("✅ Sandbox created\n")
            yield "\n".join(results)
            
            tavily_api_key = os.environ.get("TAVILY_API_KEY")
            
            agent = AutonomousAgent(
                task_id=task_id,
                description=task_description,
                sandbox=sandbox,
                tavily_api_key=tavily_api_key,
                enable_playwright=True
            )
            
            async for event in agent.run():
                content = event.get("content", "")
                event_type = event.get("type", "")
                
                prefix = {
                    "status": "📦",
                    "thought": "🧠",
                    "action": "⚡",
                    "success": "✅",
                    "warning": "⚠️",
                    "error": "❌",
                    "result": "🎉"
                }.get(event_type, "•")
                
                results.append(f"{prefix} {content}\n")
                yield "\n".join(results)
            
            await e2b.destroy_sandbox(sandbox)
            
        except Exception as e:
            results.append(f"💥 Error: {str(e)}\n")
            yield "\n".join(results)
    
    return stream_results()


def gradio_simple_run(task_description):
    """Simple synchronous wrapper."""
    async def run():
        results = []
        task_id = f"hf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            sandbox = await e2b.create_sandbox(task_id)
            results.append("✅ Sandbox created\n")
            
            tavily_api_key = os.environ.get("TAVILY_API_KEY")
            
            agent = AutonomousAgent(
                task_id=task_id,
                description=task_description,
                sandbox=sandbox,
                tavily_api_key=tavily_api_key,
                enable_playwright=True
            )
            
            async for event in agent.run():
                content = event.get("content", "")
                event_type = event.get("type", "")
                
                prefix = {
                    "status": "📦",
                    "thought": "🧠",
                    "action": "⚡",
                    "success": "✅",
                    "warning": "⚠️",
                    "error": "❌",
                    "result": "🎉"
                }.get(event_type, "•")
                
                results.append(f"{prefix} {content}\n")
            
            await e2b.destroy_sandbox(sandbox)
            
        except Exception as e:
            results.append(f"💥 Error: {str(e)}\n")
        
        return "\n".join(results)
    
    return asyncio.run(run())


def get_history():
    """Get task history."""
    if not task_history:
        return "No tasks completed yet."
    return "\n\n".join([
        f"## Task: {t['task'][:50]}...\n**Time:** {t['timestamp']}\n\n**Results:**\n{t['results'][-1] if t['results'] else 'No results'}"
        for t in task_history[-5:]
    ])


def get_model_info():
    """Get AI model info."""
    try:
        models = ai.list_models()
        return f"""
## AI Gateway Status

**Available Models:** {len(models) if models else 'Unknown'}

**Configured Providers:**
- OpenRouter: {'✅' if os.environ.get('OPENROUTER_API_KEY') else '❌'}
- HuggingFace: {'✅' if os.environ.get('HF_TOKEN') else '❌'}
- Anthropic: {'✅' if os.environ.get('ANTHROPIC_API_KEY') else '❌'}
- Gemini: {'✅' if os.environ.get('GEMINI_API_KEY') else '❌'}
"""
    except Exception as e:
        return f"**Error:** {str(e)}"


# Gradio Interface
with gr.Blocks(title="Manus AI Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🤖 Manus AI Agent OS
    
    An autonomous AI agent that can plan, execute, and self-correct tasks.
    
    ## Features
    - 🌐 Web search with Tavily AI
    - 🖥️ Terminal command execution
    - 📁 File operations in sandbox
    - 🔧 Self-correction on failures
    - ⚡ Real-time progress streaming
    """)
    
    with gr.Tab("Agent"):
        with gr.Row():
            task_input = gr.Textbox(
                label="Task Description",
                placeholder="Enter a task for Manus to execute... (e.g., 'Search for Manus AI on the web and summarize what it is')",
                lines=3
            )
        
        with gr.Row():
            run_button = gr.Button("🚀 Execute Task", variant="primary")
            clear_button = gr.Button("Clear")
        
        output = gr.Textbox(label="Results", lines=15, show_label=True)
    
    with gr.Tab("Tools Info"):
        gr.Markdown(get_tools_description())
    
    with gr.Tab("History"):
        history_output = gr.Markdown(value=get_history())
        refresh_btn = gr.Button("🔄 Refresh")
        refresh_btn.click(fn=get_history, outputs=history_output)
    
    with gr.Tab("Status"):
        status_output = gr.Markdown(value=get_model_info())
        refresh_status_btn = gr.Button("🔄 Refresh Status")
        refresh_status_btn.click(fn=get_model_info, outputs=status_output)
    
    # Run button handler
    run_button.click(
        fn=gradio_simple_run,
        inputs=[task_input],
        outputs=[output]
    )
    
    clear_button.click(
        fn=lambda: ("", ""),
        inputs=[],
        outputs=[task_input, output]
    )


# Launch
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
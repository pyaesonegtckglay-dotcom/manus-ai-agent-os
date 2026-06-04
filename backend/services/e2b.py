"""E2B Sandbox service for AI agent execution."""
from e2b import Sandbox, SandboxTemplate
from backend.core.config import get_settings
from typing import Optional, AsyncGenerator
import asyncio
import json


class E2BService:
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.E2B_API_KEY
        self.template = self.settings.E2B_SANDBOX_TEMPLATE
    
    async def create_sandbox(self, session_id: str) -> Sandbox:
        """Create a new E2B sandbox."""
        sandbox = await Sandbox.create(
            template=self.template,
            timeout=3600,  # 1 hour max
            metadata={"session_id": session_id}
        )
        return sandbox
    
    async def destroy_sandbox(self, sandbox: Sandbox):
        """Destroy an E2B sandbox."""
        await sandbox.close()
    
    async def execute_command(self, sandbox: Sandbox, command: str, timeout: int = 60) -> str:
        """Execute a command in the sandbox."""
        result = await sandbox.commands.run(command, timeout=timeout)
        return result.stdout + result.stderr
    
    async def execute_python(self, sandbox: Sandbox, code: str) -> str:
        """Execute Python code in the sandbox."""
        escaped_code = code.replace("'", "\\'").replace("\n", "\\n")
        result = await sandbox.commands.run(f"python3 -c '{escaped_code}'", timeout=120)
        return result.stdout + result.stderr
    
    async def stream_terminal(self, sandbox: Sandbox, command: str) -> AsyncGenerator[str, None]:
        """Stream terminal output from a command."""
        proc = await sandbox.commands.run_background(command)
        
        while not proc.is_done:
            if proc.stdout:
                yield proc.stdout
            await asyncio.sleep(0.1)
        
        # Get remaining output
        if proc.stdout:
            yield proc.stdout
    
    async def upload_file(self, sandbox: Sandbox, content: bytes, path: str):
        """Upload a file to the sandbox."""
        await sandbox.files.write(path, content)
    
    async def download_file(self, sandbox: Sandbox, path: str) -> bytes:
        """Download a file from the sandbox."""
        return await sandbox.files.read(path)
    
    async def list_files(self, sandbox: Sandbox, path: str = "/") -> list[dict]:
        """List files in the sandbox."""
        files = await sandbox.files.list(path)
        return [{"name": f.name, "type": f.type, "size": f.size} for f in files]
    
    async def take_screenshot(self, sandbox: Sandbox) -> Optional[bytes]:
        """Take a screenshot of the sandbox display."""
        try:
            screenshot = await sandbox.screenshot.get()
            return screenshot
        except Exception:
            return None


# Singleton instance
_e2b_service: Optional[E2BService] = None


def get_e2b() -> E2BService:
    global _e2b_service
    if _e2b_service is None:
        _e2b_service = E2BService()
    return _e2b_service
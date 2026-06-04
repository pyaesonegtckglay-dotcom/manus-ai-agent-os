"""Tool system for the AI agent."""
from abc import ABC, abstractmethod
from typing import Any, Optional
from enum import Enum
import os


class ToolType(str, Enum):
    BROWSE = "browse"
    TERMINAL = "terminal"
    FILE = "file"
    SEARCH = "search"
    API = "api"
    CUSTOM = "custom"


class BaseTool(ABC):
    """Base class for all tools."""
    
    name: str
    description: str
    tool_type: ToolType
    
    @abstractmethod
    async def execute(self, **kwargs) -> dict[str, Any]:
        """Execute the tool with given parameters."""
        pass
    
    def validate_params(self, **kwargs) -> bool:
        """Validate tool parameters before execution."""
        return True


class BrowserTool(BaseTool):
    """Browser automation tool using Playwright."""
    
    name = "browser"
    description = "Navigate web pages, interact with elements, take screenshots"
    tool_type = ToolType.BROWSE
    
    def __init__(self, sandbox):
        self.sandbox = sandbox
    
    async def execute(self, action: str, url: Optional[str] = None, selector: Optional[str] = None, 
                      value: Optional[str] = None, **kwargs) -> dict[str, Any]:
        """Execute browser action."""
        try:
            if action == "navigate":
                result = await self.sandbox.browser.navigate(url)
                return {"success": True, "url": url}
            
            elif action == "click":
                result = await self.sandbox.browser.click(selector)
                return {"success": True, "selector": selector}
            
            elif action == "type":
                result = await self.sandbox.browser.type(selector, value)
                return {"success": True, "selector": selector, "value": value}
            
            elif action == "screenshot":
                screenshot = await self.sandbox.screenshot.get()
                return {"success": True, "screenshot": "captured"}
            
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


class PlaywrightBrowserTool(BaseTool):
    """
    Standalone Playwright browser tool for Manus.
    Can be used outside of E2B sandbox for local browsing.
    """
    
    name = "playwright_browser"
    description = "Full browser automation using Playwright. Navigate, click, type, get content, screenshot"
    tool_type = ToolType.BROWSE
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Playwright browser."""
        if self._initialized:
            return
        
        try:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context(viewport={"width": 1920, "height": 1080})
            self.page = await self.context.new_page()
            self._initialized = True
        except ImportError:
            raise Exception("Playwright not installed. Run: pip install playwright")
        except Exception as e:
            raise Exception(f"Browser init failed: {e}")
    
    async def execute(self, action: str, url: Optional[str] = None, selector: Optional[str] = None,
                      value: Optional[str] = None, **kwargs) -> dict[str, Any]:
        """Execute browser action."""
        try:
            if not self._initialized:
                await self.initialize()
            
            if action == "navigate" or action == "goto":
                if not url:
                    return {"success": False, "error": "URL required"}
                response = await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
                title = await self.page.title()
                return {
                    "success": True,
                    "url": str(self.page.url),
                    "title": title,
                    "status_code": response.status if response else None
                }
            
            elif action == "click":
                if not selector:
                    return {"success": False, "error": "Selector required"}
                await self.page.click(selector, timeout=5000)
                return {"success": True, "selector": selector}
            
            elif action == "type" or action == "fill":
                if not selector or value is None:
                    return {"success": False, "error": "Selector and value required"}
                await self.page.fill(selector, value)
                return {"success": True, "selector": selector, "value": value}
            
            elif action == "get_content" or action == "get_text":
                if selector:
                    content = await self.page.text_content(selector)
                else:
                    content = await self.page.content()
                return {"success": True, "content": content}
            
            elif action == "screenshot":
                encoded = await self.page.screenshot()
                return {"success": True, "screenshot": "captured", "size": len(encoded)}
            
            elif action == "evaluate" or action == "script":
                script = kwargs.get("script", "")
                if not script:
                    return {"success": False, "error": "Script required"}
                result = await self.page.evaluate(script)
                return {"success": True, "result": result}
            
            elif action == "wait":
                selector = kwargs.get("selector")
                timeout = kwargs.get("timeout", 5000)
                if selector:
                    await self.page.wait_for_selector(selector, timeout=timeout)
                return {"success": True}
            
            elif action == "close":
                if self.browser:
                    await self.browser.close()
                if self.playwright:
                    await self.playwright.stop()
                self._initialized = False
                return {"success": True}
            
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}


class TerminalTool(BaseTool):
    """Terminal execution tool."""
    
    name = "terminal"
    description = "Execute shell commands in the sandbox environment"
    tool_type = ToolType.TERMINAL
    
    def __init__(self, sandbox):
        self.sandbox = sandbox
    
    async def execute(self, command: str, timeout: int = 60, **kwargs) -> dict[str, Any]:
        """Execute a terminal command."""
        try:
            result = await self.sandbox.commands.run(command, timeout=timeout)
            return {
                "success": True,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class FileTool(BaseTool):
    """File operations tool."""
    
    name = "file"
    description = "Read, write, and manipulate files in the sandbox"
    tool_type = ToolType.FILE
    
    def __init__(self, sandbox):
        self.sandbox = sandbox
    
    async def execute(self, action: str, path: str, content: Optional[str] = None, **kwargs) -> dict[str, Any]:
        """Execute file operation."""
        try:
            if action == "read":
                content = await self.sandbox.files.read(path)
                return {"success": True, "content": content}
            
            elif action == "write":
                await self.sandbox.files.write(path, content)
                return {"success": True, "path": path}
            
            elif action == "list":
                files = await self.sandbox.files.list(path)
                return {"success": True, "files": [{"name": f.name} for f in files]}
            
            elif action == "delete":
                await self.sandbox.files.delete(path)
                return {"success": True, "path": path}
            
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


class SearchTool(BaseTool):
    """Web search tool."""
    
    name = "search"
    description = "Search the web for information"
    tool_type = ToolType.SEARCH
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    async def execute(self, query: str, limit: int = 10, **kwargs) -> dict[str, Any]:
        """Execute a web search."""
        try:
            import httpx
            
            # Use DuckDuckGo for free search
            url = f"https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_redirect": 1
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for topic in data.get("RelatedTopics", [])[:limit]:
                    if "Text" in topic:
                        results.append({
                            "title": topic.get("Text", "").split(" - ")[0] if " - " in topic.get("Text", "") else "",
                            "url": topic.get("FirstURL", ""),
                            "snippet": topic.get("Text", "")
                        })
                
                return {
                    "success": True,
                    "query": query,
                    "results": results
                }
        except Exception as e:
            return {"success": False, "error": str(e)}


class TavilySearchTool(BaseTool):
    """Tavily AI web search tool - for comprehensive, accurate search results."""
    
    name = "tavily_search"
    description = "Search the web for current information using Tavily AI. Returns relevant results with sources."
    tool_type = ToolType.SEARCH
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY")
        self._client = None
    
    def _get_client(self):
        if not self._client and self.api_key:
            from tavily import TavilyClient
            self._client = TavilyClient(api_key=self.api_key)
        return self._client
    
    async def execute(self, query: str, max_results: int = 10, search_depth: str = "basic", 
                     include_answer: bool = True, **kwargs) -> dict[str, Any]:
        """Execute a web search using Tavily AI."""
        try:
            client = self._get_client()
            if not client:
                return {"success": False, "error": "Tavily API key not configured"}
            
            results = client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_answer=include_answer
            )
            
            return {
                "success": True,
                "query": query,
                "answer": results.get("answer"),
                "results": [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "content": r.get("content", "")[:500]
                    }
                    for r in results.get("results", [])[:max_results]
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class TavilyExtractTool(BaseTool):
    """Extract content from URLs using Tavily."""
    
    name = "tavily_extract"
    description = "Extract and crawl content from specific URLs"
    tool_type = ToolType.SEARCH
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY")
        self._client = None
    
    def _get_client(self):
        if not self._client and self.api_key:
            from tavily import TavilyClient
            self._client = TavilyClient(api_key=self.api_key)
        return self._client
    
    async def execute(self, urls: list, **kwargs) -> dict[str, Any]:
        """Extract content from URLs."""
        try:
            client = self._get_client()
            if not client:
                return {"success": False, "error": "Tavily API key not configured"}
            
            results = client.extract(urls=urls)
            
            return {
                "success": True,
                "results": [
                    {
                        "url": r.get("url", ""),
                        "raw_content": r.get("raw_content", "")[:2000]
                    }
                    for r in results.get("results", [])
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class TavilyCrawlTool(BaseTool):
    """Crawl a website and extract content using Tavily."""
    
    name = "tavily_crawl"
    description = "Crawl a website starting from a URL with configurable depth and breadth"
    tool_type = ToolType.SEARCH
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY")
        self._client = None
    
    def _get_client(self):
        if not self._client and self.api_key:
            from tavily import TavilyClient
            self._client = TavilyClient(api_key=self.api_key)
        return self._client
    
    async def execute(self, url: str, max_depth: int = 2, max_breadth: int = 10, 
                     include_images: bool = False, **kwargs) -> dict[str, Any]:
        """Crawl a website and extract content."""
        try:
            client = self._get_client()
            if not client:
                return {"success": False, "error": "Tavily API key not configured"}
            
            results = client.crawl(
                url=url,
                max_depth=max_depth,
                max_breadth=max_breadth,
                include_images=include_images
            )
            
            return {
                "success": True,
                "url": url,
                "results": [
                    {
                        "url": r.get("url", ""),
                        "content": r.get("content", "")[:1000]
                    }
                    for r in results.get("results", [])[:20]
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class GoogleWorkspaceTool(BaseTool):
    """Google Workspace integration tool (Drive, Sheets, Docs)."""
    
    name = "google_workspace"
    description = "Access and manipulate Google Drive, Sheets, and Docs"
    tool_type = ToolType.API
    
    def __init__(self, credentials_path: str):
        self.credentials_path = credentials_path
        self._service = None
    
    async def execute(self, service: str, action: str, **kwargs) -> dict[str, Any]:
        """Execute Google Workspace action."""
        try:
            if not self._service:
                from google.oauth2 import service_account
                self._service = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=[
                        "https://www.googleapis.com/auth/drive",
                        "https://www.googleapis.com/auth/spreadsheets",
                        "https://www.googleapis.com/auth/documents"
                    ]
                )
            
            if service == "sheets":
                return await self._sheets_action(action, **kwargs)
            elif service == "drive":
                return await self._drive_action(action, **kwargs)
            elif service == "docs":
                return await self._docs_action(action, **kwargs)
            else:
                return {"success": False, "error": f"Unknown service: {service}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _sheets_action(self, action: str, spreadsheet_id: str, range: str = "A1:Z100", 
                              values: Optional[list] = None, **kwargs) -> dict[str, Any]:
        """Execute Google Sheets action."""
        from googleapiclient.discovery import build
        
        service = build("sheets", "v4", credentials=self._service)
        
        if action == "read":
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range
            ).execute()
            return {"success": True, "values": result.get("values", [])}
        
        elif action == "write":
            body = {"values": values}
            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range=range, 
                valueInputOption="USER_ENTERED", body=body
            ).execute()
            return {"success": True, "updated_cells": result.get("updatedCells")}
        
        return {"success": False, "error": f"Unknown action: {action}"}
    
    async def _drive_action(self, action: str, name: Optional[str] = None, 
                            file_id: Optional[str] = None, **kwargs) -> dict[str, Any]:
        """Execute Google Drive action."""
        from googleapiclient.discovery import build
        
        service = build("drive", "v3", credentials=self._service)
        
        if action == "list":
            results = service.files().list(
                pageSize=10, fields="files(id, name, mimeType)"
            ).execute()
            return {"success": True, "files": results.get("files", [])}
        
        elif action == "create":
            file_metadata = {"name": name, "mimeType": "application/json"}
            result = service.files().create(body=file_metadata, fields="id").execute()
            return {"success": True, "file_id": result.get("id")}
        
        return {"success": False, "error": f"Unknown action: {action}"}
    
    async def _docs_action(self, action: str, document_id: str, text: Optional[str] = None, **kwargs) -> dict[str, Any]:
        """Execute Google Docs action."""
        from googleapiclient.discovery import build
        
        service = build("docs", "v1", credentials=self._service)
        
        if action == "read":
            doc = service.documents().get(documentId=document_id).execute()
            return {"success": True, "content": doc.get("body").get("content")}
        
        elif action == "insert":
            # Insert text at the end
            doc = service.documents().get(documentId=document_id).execute()
            end_index = doc.get("body").get("content")[-1].get("endIndex")
            
            requests = [{
                "insertText": {
                    "location": {"index": end_index - 1},
                    "text": text
                }
            }]
            service.documents().batchUpdate(
                documentId=document_id, body={"requests": requests}
            ).execute()
            return {"success": True}
        
        return {"success": False, "error": f"Unknown action: {action}"}


class ToolRegistry:
    """Registry for all available tools."""
    
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool):
        """Register a tool."""
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> list[dict]:
        """List all available tools."""
        return [
            {"name": tool.name, "description": tool.description, "type": tool.tool_type.value}
            for tool in self._tools.values()
        ]
    
    async def execute(self, tool_name: str, **kwargs) -> dict[str, Any]:
        """Execute a tool by name."""
        tool = self.get(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool not found: {tool_name}"}
        return await tool.execute(**kwargs)


# Default tool registry factory
def create_tool_registry(sandbox=None, google_creds: Optional[str] = None, tavily_api_key: Optional[str] = None,
                         enable_playwright: bool = False) -> ToolRegistry:
    """Create a default tool registry with all built-in tools."""
    registry = ToolRegistry()
    
    if sandbox:
        # E2B sandbox-based tools
        registry.register(BrowserTool(sandbox))
        registry.register(TerminalTool(sandbox))
        registry.register(FileTool(sandbox))
    
    # Always register search tools
    registry.register(SearchTool())  # DuckDuckGo fallback
    
    # Register Tavily tools if API key provided
    tavily_key = tavily_api_key or os.environ.get("TAVILY_API_KEY")
    if tavily_key:
        registry.register(TavilySearchTool(tavily_key))
        registry.register(TavilyExtractTool(tavily_key))
        registry.register(TavilyCrawlTool(tavily_key))
    
    # Register standalone Playwright browser tool
    if enable_playwright:
        registry.register(PlaywrightBrowserTool())
    
    if google_creds:
        registry.register(GoogleWorkspaceTool(google_creds))
    
    return registry
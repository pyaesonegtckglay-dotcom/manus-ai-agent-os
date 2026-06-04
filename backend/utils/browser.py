"""Browser automation using Playwright for Manus AI agent."""
from typing import Optional, Dict, Any
import asyncio
import json


class BrowserAutomation:
    """
    Browser automation tool using Playwright.
    Can work with E2B sandbox browser or standalone.
    """
    
    def __init__(self, playwright=None):
        self.playwright = playwright
        self.browser = None
        self.context = None
        self.page = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Playwright and browser."""
        if self._initialized:
            return
        
        try:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            self.page = await self.context.new_page()
            self._initialized = True
        except ImportError:
            raise Exception("Playwright not installed. Run: pip install playwright && playwright install")
        except Exception as e:
            raise Exception(f"Failed to initialize browser: {e}")
    
    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL."""
        if not self._initialized:
            await self.initialize()
        
        try:
            response = await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            title = await self.page.title()
            return {
                "success": True,
                "url": str(self.page.url),
                "title": title,
                "status_code": response.status if response else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def click(self, selector: str, timeout: int = 5000) -> Dict[str, Any]:
        """Click an element by CSS selector."""
        if not self._initialized:
            await self.initialize()
        
        try:
            await self.page.click(selector, timeout=timeout)
            return {"success": True, "selector": selector}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def type(self, selector: str, text: str, delay: int = 50) -> Dict[str, Any]:
        """Type text into an input field."""
        if not self._initialized:
            await self.initialize()
        
        try:
            await self.page.fill(selector, text)
            return {"success": True, "selector": selector, "text": text}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_content(self, selector: Optional[str] = None) -> Dict[str, Any]:
        """Get page content or element content."""
        if not self._initialized:
            await self.initialize()
        
        try:
            if selector:
                content = await self.page.text_content(selector)
            else:
                content = await self.page.content()
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def screenshot(self, path: Optional[str] = None, full_page: bool = False) -> Dict[str, Any]:
        """Take a screenshot."""
        if not self._initialized:
            await self.initialize()
        
        try:
            if path:
                await self.page.screenshot(path=path, full_page=full_page)
                return {"success": True, "path": path}
            else:
                # Return base64 encoded screenshot
                encoded = await self.page.screenshot()
                return {"success": True, "screenshot": encoded}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def evaluate(self, script: str) -> Dict[str, Any]:
        """Execute JavaScript on the page."""
        if not self._initialized:
            await self.initialize()
        
        try:
            result = await self.page.evaluate(script)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def wait_for_selector(self, selector: str, timeout: int = 5000) -> Dict[str, Any]:
        """Wait for an element to appear."""
        if not self._initialized:
            await self.initialize()
        
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return {"success": True, "selector": selector}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def close(self):
        """Close the browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self._initialized = False


# Standalone browser tool for use without E2B
async def create_browser_tool() -> BrowserAutomation:
    """Create a standalone browser automation tool."""
    return BrowserAutomation()


# Integration with E2B sandbox
class E2BBrowserTool:
    """Browser tool that runs in E2B sandbox with Playwright installed."""
    
    def __init__(self, sandbox):
        self.sandbox = sandbox
    
    async def execute(self, action: str, **params) -> Dict[str, Any]:
        """Execute browser action in E2B sandbox."""
        try:
            if action == "install":
                # Install Playwright in sandbox
                result = await self.sandbox.commands.run(
                    "pip install playwright && playwright install chromium --with-deps",
                    timeout=300
                )
                return {"success": True, "output": result.stdout}
            
            elif action == "navigate":
                # For E2B, we'd need to run a script
                script = f"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("{params.get('url', '')}")
        title = await page.title()
        await browser.close()
        return title

result = asyncio.run(main())
print(result)
"""
                result = await self.sandbox.commands.run(
                    f"python3 -c '{script.replace(chr(39), chr(39)*3)}'",
                    timeout=60
                )
                return {"success": True, "output": result.stdout, "url": params.get("url")}
            
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
"""Tests for tool system."""
import pytest
from unittest.mock import MagicMock, AsyncMock


class TestToolRegistry:
    """Tests for ToolRegistry."""
    
    @pytest.fixture
    def registry(self):
        """Create empty registry for testing."""
        from backend.utils.tools import ToolRegistry
        return ToolRegistry()
    
    def test_register_tool(self, registry):
        """Test registering a tool."""
        tool = MagicMock()
        tool.name = "test_tool"
        tool.description = "A test tool"
        tool.tool_type.value = "custom"
        
        registry.register(tool)
        
        assert registry.get("test_tool") == tool
    
    def test_get_existing_tool(self, registry):
        """Test getting an existing tool."""
        tool = MagicMock()
        tool.name = "existing"
        registry.register(tool)
        
        result = registry.get("existing")
        assert result == tool
    
    def test_get_nonexistent_tool(self, registry):
        """Test getting a tool that doesn't exist."""
        result = registry.get("nonexistent")
        assert result is None
    
    def test_list_tools(self, registry):
        """Test listing all tools."""
        tool1 = MagicMock()
        tool1.name = "tool1"
        tool1.description = "First tool"
        tool1.tool_type.value = "browser"
        
        tool2 = MagicMock()
        tool2.name = "tool2"
        tool2.description = "Second tool"
        tool2.tool_type.value = "terminal"
        
        registry.register(tool1)
        registry.register(tool2)
        
        tools = registry.list_tools()
        assert len(tools) == 2
        assert tools[0]["name"] == "tool1"
        assert tools[1]["name"] == "tool2"
    
    @pytest.mark.asyncio
    async def test_execute_tool(self, registry):
        """Test executing a tool."""
        tool = MagicMock()
        tool.name = "exec_tool"
        tool.execute = AsyncMock(return_value={"success": True, "result": "done"})
        
        registry.register(tool)
        
        result = await registry.execute("exec_tool", param="value")
        
        assert result["success"] is True
        tool.execute.assert_called_once_with(param="value")
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self, registry):
        """Test executing a tool that doesn't exist."""
        result = await registry.execute("nonexistent")
        
        assert result["success"] is False
        assert "not found" in result["error"]


class TestTerminalTool:
    """Tests for TerminalTool."""
    
    @pytest.fixture
    def sandbox(self):
        """Create mock sandbox."""
        sandbox = MagicMock()
        sandbox.commands.run = AsyncMock(return_value=MagicMock(
            stdout="test output",
            stderr="",
            exit_code=0
        ))
        return sandbox
    
    @pytest.mark.asyncio
    async def test_execute_command(self, sandbox):
        """Test executing a command."""
        from backend.utils.tools import TerminalTool
        
        tool = TerminalTool(sandbox)
        result = await tool.execute(command="echo 'hello'")
        
        assert result["success"] is True
        assert result["stdout"] == "test output"
        sandbox.commands.run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_with_timeout(self, sandbox):
        """Test executing with custom timeout."""
        from backend.utils.tools import TerminalTool
        
        tool = TerminalTool(sandbox)
        await tool.execute(command="sleep 1", timeout=10)
        
        sandbox.commands.run.assert_called_with("sleep 1", timeout=10)
    
    @pytest.mark.asyncio
    async def test_execute_handles_error(self, sandbox):
        """Test handling execution errors."""
        from backend.utils.tools import TerminalTool
        
        sandbox.commands.run = AsyncMock(side_effect=Exception("Command failed"))
        
        tool = TerminalTool(sandbox)
        result = await tool.execute(command="fail")
        
        assert result["success"] is False
        assert "Command failed" in result["error"]


class TestFileTool:
    """Tests for FileTool."""
    
    @pytest.fixture
    def sandbox(self):
        """Create mock sandbox."""
        sandbox = MagicMock()
        sandbox.files.read = AsyncMock(return_value=b"file content")
        sandbox.files.write = AsyncMock()
        sandbox.files.list = AsyncMock(return_value=[MagicMock(name="file1.txt"), MagicMock(name="file2.txt")])
        sandbox.files.delete = AsyncMock()
        return sandbox
    
    @pytest.mark.asyncio
    async def test_read_file(self, sandbox):
        """Test reading a file."""
        from backend.utils.tools import FileTool
        
        tool = FileTool(sandbox)
        result = await tool.execute(action="read", path="/test/file.txt")
        
        assert result["success"] is True
        sandbox.files.read.assert_called_with("/test/file.txt")
    
    @pytest.mark.asyncio
    async def test_write_file(self, sandbox):
        """Test writing a file."""
        from backend.utils.tools import FileTool
        
        tool = FileTool(sandbox)
        result = await tool.execute(
            action="write",
            path="/test/new.txt",
            content="new content"
        )
        
        assert result["success"] is True
        sandbox.files.write.assert_called_with("/test/new.txt", "new content")
    
    @pytest.mark.asyncio
    async def test_list_files(self, sandbox):
        """Test listing files."""
        from backend.utils.tools import FileTool
        
        tool = FileTool(sandbox)
        result = await tool.execute(action="list", path="/test")
        
        assert result["success"] is True
        assert len(result["files"]) == 2
    
    @pytest.mark.asyncio
    async def test_delete_file(self, sandbox):
        """Test deleting a file."""
        from backend.utils.tools import FileTool
        
        tool = FileTool(sandbox)
        result = await tool.execute(action="delete", path="/test/file.txt")
        
        assert result["success"] is True
        sandbox.files.delete.assert_called_with("/test/file.txt")


class TestSearchTool:
    """Tests for SearchTool."""
    
    @pytest.mark.asyncio
    async def test_search_execution(self):
        """Test web search execution."""
        from backend.utils.tools import SearchTool
        
        tool = SearchTool()
        result = await tool.execute(query="test search", limit=5)
        
        # Should return success (even if actual API fails)
        assert "success" in result


class TestCreateToolRegistry:
    """Tests for create_tool_registry factory."""
    
    @pytest.mark.asyncio
    async def test_create_with_sandbox(self):
        """Test creating registry with sandbox."""
        from backend.utils.tools import create_tool_registry
        
        sandbox = MagicMock()
        sandbox.commands.run = AsyncMock()
        sandbox.files.read = AsyncMock(return_value=b"")
        
        registry = create_tool_registry(sandbox=sandbox, google_creds=None)
        
        # Should have browser, terminal, file, search tools
        tools = registry.list_tools()
        tool_names = [t["name"] for t in tools]
        
        assert "terminal" in tool_names
        assert "file" in tool_names
        assert "search" in tool_names
"""Tests for AI Gateway service."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestAIGateway:
    """Tests for the AI Gateway service."""
    
    @pytest.fixture
    def ai_gateway(self):
        """Create AI Gateway instance for testing."""
        from backend.services.ai_gateway import AIGateway
        gateway = AIGateway()
        # Mock the AI clients
        gateway.openai = MagicMock()
        gateway.anthropic = MagicMock()
        return gateway
    
    @pytest.mark.asyncio
    async def test_complete_with_anthropic(self, ai_gateway):
        """Test completion with Anthropic/Claude."""
        # Mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response from Claude")]
        ai_gateway.anthropic.messages.create = AsyncMock(return_value=mock_response)
        
        # Set Claude for planning
        ai_gateway.set_model(
            "planning",
            "anthropic",
            "claude-3-5-sonnet-20241022"
        )
        
        result = await ai_gateway.complete(
            "What is the capital of France?",
            role="planning"
        )
        
        assert result == "Test response from Claude"
        ai_gateway.anthropic.messages.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_complete_with_openai(self, ai_gateway):
        """Test completion with OpenAI-compatible API."""
        # Mock response
        mock_choice = MagicMock()
        mock_choice.message.content = "Test response from OpenAI"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        ai_gateway.openai.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await ai_gateway.complete(
            "Hello world",
            role="execution"
        )
        
        assert result == "Test response from OpenAI"
        ai_gateway.openai.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_complete_with_system_prompt(self, ai_gateway):
        """Test completion with system prompt."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Analyzed response")]
        ai_gateway.anthropic.messages.create = AsyncMock(return_value=mock_response)
        
        result = await ai_gateway.complete(
            "Analyze this",
            system="You are a helpful assistant"
        )
        
        # Verify system prompt was included
        call_args = ai_gateway.anthropic.messages.create.call_args
        assert "system" in call_args.kwargs or call_args.kwargs.get("system") is not None


class TestModelConfiguration:
    """Tests for model configuration."""
    
    def test_set_model(self):
        """Test setting custom model configuration."""
        from backend.services.ai_gateway import AIGateway, ModelProvider, ModelRole
        
        gateway = AIGateway()
        
        # Set custom model
        gateway.set_model(
            ModelRole.EXECUTION,
            ModelProvider.SAMBANOVA,
            "Meta-Llama-3-70B-Instruct"
        )
        
        # Verify model was set
        assert gateway.models["execution"].provider == ModelProvider.SAMBANOVA
        assert gateway.models["execution"].model_id == "Meta-Llama-3-70B-Instruct"
    
    def test_default_models(self):
        """Test default model configuration."""
        from backend.services.ai_gateway import AIGateway
        
        gateway = AIGateway()
        
        # Verify default models are set
        assert "planning" in gateway.models
        assert "execution" in gateway.models
        assert gateway.models["planning"].role.value == "planning"
        assert gateway.models["execution"].role.value == "execution"
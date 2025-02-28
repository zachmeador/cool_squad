"""
Tests for the integration of internal monologue with bots.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import json

from cool_squad.bots.base import Bot, create_bot_with_tools
from cool_squad.core.models import Message
from cool_squad.core.monologue import InternalMonologue


@pytest.fixture
def test_bot_with_monologue():
    """Create a test bot with monologue enabled."""
    personality = "You are a helpful test bot."
    bot = Bot(
        name="test_bot",
        personality=personality,
        use_monologue=True
    )
    return bot


@pytest.fixture
def test_bot_without_monologue():
    """Create a test bot with monologue disabled."""
    personality = "You are a helpful test bot."
    bot = Bot(
        name="test_bot",
        personality=personality,
        use_monologue=False
    )
    return bot


@pytest.mark.asyncio
async def test_bot_monologue_initialization():
    """Test that a bot initializes with an internal monologue."""
    bot = Bot("test_bot", "Test personality", use_monologue=True)
    
    assert hasattr(bot, "monologue")
    assert isinstance(bot.monologue, InternalMonologue)
    assert bot.use_monologue is True


@pytest.mark.asyncio
async def test_bot_adds_input_thought(test_bot_with_monologue):
    """Test that a bot adds the user message to its monologue."""
    # Mock the OpenAI API to avoid actual calls
    with patch('cool_squad.bots.base.client') as mock_openai:
        # Set up the mock to return a response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].message.tool_calls = None
        
        # Create a mock async method
        async def mock_create(*args, **kwargs):
            return mock_response
        
        # Set up the mock chat completions create method
        mock_openai.chat.completions.create = mock_create
        
        # Process a message
        message = Message(content="Hello, bot!", author="user")
        await test_bot_with_monologue.process_message(message, channel="test")
        
        # Check that the bot added the input to its monologue
        assert len(test_bot_with_monologue.monologue.thoughts) > 0
        input_thoughts = [t for t in test_bot_with_monologue.monologue.thoughts if t.category == "input"]
        assert len(input_thoughts) > 0
        assert "Hello, bot!" in input_thoughts[0].content


@pytest.mark.asyncio
async def test_bot_without_monologue():
    """Test that a bot with monologue disabled doesn't use it."""
    # Create a bot with monologue disabled
    bot = Bot(
        name="test_bot",
        personality="You are a helpful test bot.",
        use_monologue=False
    )
    
    # Mock the OpenAI API to avoid actual calls
    with patch('cool_squad.bots.base.client') as mock_openai:
        # Set up the mock to return a response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].message.tool_calls = None
        
        # Create a mock async method
        async def mock_create(*args, **kwargs):
            return mock_response
        
        # Set up the mock chat completions create method
        mock_openai.chat.completions.create = mock_create
        
        # Process a message
        message = Message(content="Hello, bot!", author="user")
        await bot.process_message(message, channel="test")
        
        # Check that the bot didn't add anything to its monologue
        assert bot.use_monologue is False
        assert hasattr(bot, "monologue")
        assert len(bot.monologue.thoughts) == 0


@pytest.mark.asyncio
async def test_debug_mode():
    """Test that debug mode includes monologue in responses."""
    # Create a bot with debug mode enabled
    bot = Bot(
        name="debug_bot",
        personality="You are a helpful test bot.",
        use_monologue=True,
        debug_mode=True
    )
    
    # Mock the OpenAI API to avoid actual calls
    with patch('cool_squad.bots.base.client') as mock_openai:
        # Set up the mock to return a response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].message.tool_calls = None
        
        # Create a mock async method
        async def mock_create(*args, **kwargs):
            return mock_response
        
        # Set up the mock chat completions create method
        mock_openai.chat.completions.create = mock_create
        
        # Add a thought to the monologue
        bot.monologue.add_thought("Test thought", "general")
        
        # Process a message
        message = Message(content="Hello, bot!", author="user")
        response = await bot.process_message(message, channel="test")
        
        # Check that the response includes the debug info
        assert "[DEBUG: Internal Monologue]" in response
        assert "Test thought" in response
        assert "[RESPONSE]" in response
        assert "Test response" in response


@pytest.mark.asyncio
async def test_monologue_with_tools():
    """Test that a bot uses monologue to drive tool selection."""
    # Create a bot with tools and monologue
    bot = create_bot_with_tools(
        name="tool_bot",
        personality="You are a helpful test bot.",
        use_monologue=True
    )
    
    # Mock the OpenAI API for the internal monologue generation
    with patch('cool_squad.bots.base.client') as mock_openai:
        # Mock for _generate_internal_monologue
        monologue_response = MagicMock()
        monologue_response.choices = [MagicMock()]
        monologue_response.choices[0].message.content = "I should check recent messages in the channel."
        
        # Mock for _consider_tools_from_monologue
        tool_analysis_response = MagicMock()
        tool_analysis_response.choices = [MagicMock()]
        tool_analysis_response.choices[0].message.content = json.dumps({
            "read_channel_messages": {
                "relevance": 0.9,
                "reasoning": "Need to check recent messages"
            }
        })
        
        # Mock for the main API call
        main_response = MagicMock()
        main_response.choices = [MagicMock()]
        main_response.choices[0].message.content = "Here's what I found"
        main_response.choices[0].message.tool_calls = None
        
        # Create a sequence of responses for different calls
        responses = [monologue_response, tool_analysis_response, main_response]
        response_iter = iter(responses)
        
        # Create a mock async method that returns the next response
        async def mock_create(*args, **kwargs):
            try:
                return next(response_iter)
            except StopIteration:
                return main_response
        
        # Set up the mock chat completions create method
        mock_openai.chat.completions.create = mock_create
        
        # Process a message
        message = Message(content="What's been discussed recently?", author="user")
        await bot.process_message(message, channel="test")
        
        # Check that the bot generated thoughts and considered tools
        assert len(bot.monologue.thoughts) > 0
        assert len(bot.monologue.tool_considerations) > 0
        assert "read_channel_messages" in bot.monologue.tool_considerations


@pytest.mark.asyncio
async def test_create_bot_with_tools_monologue_params():
    """Test that create_bot_with_tools respects monologue parameters."""
    # Create a bot with monologue enabled
    bot1 = create_bot_with_tools(
        name="bot1",
        personality="Test personality",
        use_monologue=True,
        debug_mode=True
    )
    
    # Create a bot with monologue disabled
    bot2 = create_bot_with_tools(
        name="bot2",
        personality="Test personality",
        use_monologue=False,
        debug_mode=False
    )
    
    assert bot1.use_monologue is True
    assert bot1.debug_mode is True
    
    assert bot2.use_monologue is False
    assert bot2.debug_mode is False 
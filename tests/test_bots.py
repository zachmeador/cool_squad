"""
Tests for the bot functionality of cool_squad.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
from cool_squad.bots import Bot
from cool_squad.core import Message


@pytest.fixture
def test_bot():
    """Create a test bot with a simple personality."""
    personality = """
    You are a helpful test bot.
    When asked a question, respond with 'Test response: [question]'
    """
    return Bot("test_bot", personality)


@pytest.mark.asyncio
async def test_bot_initialization():
    """Test that a bot can be initialized with a personality."""
    personality = "You are a test bot."
    bot = Bot("test_bot", personality)
    
    assert bot.name == "test_bot"
    assert bot.personality == personality
    assert bot.memory == []


@pytest.mark.asyncio
async def test_process_message(test_bot):
    """Test that a bot can process a message and generate a response."""
    # Mock the OpenAI API
    with patch('cool_squad.bots.openai') as mock_openai:
        # Set up the mock to return a response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response: How are you?"
        mock_response.choices[0].message.tool_calls = None
        
        # Create a mock async method
        async def mock_create(*args, **kwargs):
            return mock_response
        
        # Set up the mock chat completions create method
        mock_openai.chat = MagicMock()
        mock_openai.chat.completions = MagicMock()
        mock_openai.chat.completions.create = mock_create
        
        # Create a test message
        message = Message(content="How are you?", author="test_user")
        
        # Process the message
        response = await test_bot.process_message(message, "test_channel")
        
        # Verify the response
        assert response == "Test response: How are you?"
        
        # Verify the messages were added to the bot's memory (user message and assistant response)
        assert len(test_bot.memory) == 2
        assert test_bot.memory[0]["role"] == "user"
        assert test_bot.memory[0]["content"].startswith("[#test_channel] test_user: How are you?")
        assert test_bot.memory[1]["role"] == "assistant"
        assert test_bot.memory[1]["content"] == "Test response: How are you?"


@pytest.mark.asyncio
async def test_memory_management(test_bot):
    """Test that a bot can manage its memory correctly."""
    # Mock the OpenAI API
    with patch('cool_squad.bots.openai') as mock_openai:
        # Set up the mock to return a response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].message.tool_calls = None
        
        # Create a mock async method
        async def mock_create(*args, **kwargs):
            return mock_response
        
        # Set up the mock chat completions create method
        mock_openai.chat = MagicMock()
        mock_openai.chat.completions = MagicMock()
        mock_openai.chat.completions.create = mock_create
        
        # Create test messages
        for i in range(60):  # Create more messages than max_memory
            message = Message(content=f"Message {i}", author="test_user")
            await test_bot.process_message(message, "test_channel")
        
        # Verify the memory size is limited by max_memory
        # Each message adds 2 entries (user + assistant), so we expect 2 * max_memory entries
        assert len(test_bot.memory) <= 2 * test_bot.max_memory
        
        # Verify the most recent messages are kept
        last_user_message = None
        for msg in test_bot.memory:
            if msg["role"] == "user" and "Message 59" in msg["content"]:
                last_user_message = msg
                break
        
        assert last_user_message is not None
        assert last_user_message["content"].startswith("[#test_channel] test_user: Message 59")


@pytest.mark.asyncio
async def test_different_channels(test_bot):
    """Test that a bot can handle messages from different channels."""
    # Mock the OpenAI API
    with patch('cool_squad.bots.openai') as mock_openai:
        # Set up the mock to return a response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].message.tool_calls = None
        
        # Create a mock async method
        async def mock_create(*args, **kwargs):
            return mock_response
        
        # Set up the mock chat completions create method
        mock_openai.chat = MagicMock()
        mock_openai.chat.completions = MagicMock()
        mock_openai.chat.completions.create = mock_create
        
        # Process messages from different channels
        message1 = Message(content="Message in channel 1", author="user1")
        message2 = Message(content="Message in channel 2", author="user2")
        
        await test_bot.process_message(message1, "channel1")
        await test_bot.process_message(message2, "channel2")
        
        # Verify both messages are in memory with channel context
        channel1_found = False
        channel2_found = False
        
        for msg in test_bot.memory:
            if msg["role"] == "user":
                if "[#channel1]" in msg["content"]:
                    channel1_found = True
                if "[#channel2]" in msg["content"]:
                    channel2_found = True
        
        assert channel1_found, "Message from channel1 not found in memory"
        assert channel2_found, "Message from channel2 not found in memory" 
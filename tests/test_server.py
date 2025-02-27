"""
Tests for the server functionality of cool_squad.
"""

import pytest
import asyncio
import json
import websockets
from unittest.mock import MagicMock, patch
from cool_squad.server import ChatServer
from cool_squad.core import Message, Channel


@pytest.fixture
def chat_server():
    """Create a chat server for testing."""
    server = ChatServer()
    # Mock the storage to avoid file operations
    server.storage = MagicMock()
    server.storage.load_channel.return_value = Channel(name="test_channel")
    return server


@pytest.mark.asyncio
async def test_register(chat_server):
    """Test registering a websocket connection to a channel."""
    # Create a mock websocket
    websocket = MagicMock()
    
    # Register the websocket to a channel
    await chat_server.register(websocket, "test_channel")
    
    # Verify the websocket was added to the channel
    assert "test_channel" in chat_server.connections
    assert websocket in chat_server.connections["test_channel"]
    assert "test_channel" in chat_server.channels


@pytest.mark.asyncio
async def test_unregister(chat_server):
    """Test unregistering a websocket connection from a channel."""
    # Create a mock websocket
    websocket = MagicMock()
    
    # Register the websocket to a channel
    await chat_server.register(websocket, "test_channel")
    
    # Unregister the websocket
    await chat_server.unregister(websocket, "test_channel")
    
    # Verify the websocket was removed
    # The channel might be completely removed if it was the last connection
    if "test_channel" in chat_server.connections:
        assert len(chat_server.connections["test_channel"]) == 0
    else:
        # If the channel was removed, this is also correct behavior
        assert "test_channel" not in chat_server.connections


@pytest.mark.asyncio
async def test_broadcast(chat_server):
    """Test broadcasting a message to all websockets in a channel."""
    # Create mock websockets with async send method
    websocket1 = MagicMock()
    future1 = asyncio.Future()
    future1.set_result(None)
    websocket1.send_json.return_value = future1
    
    websocket2 = MagicMock()
    future2 = asyncio.Future()
    future2.set_result(None)
    websocket2.send_json.return_value = future2
    
    # Register the websockets to a channel
    await chat_server.register(websocket1, "test_channel")
    await chat_server.register(websocket2, "test_channel")
    
    # Broadcast a message
    message = {"type": "message", "content": "Hello", "author": "test_user"}
    await chat_server.broadcast("test_channel", message)
    
    # Verify the message was sent to both websockets
    websocket1.send_json.assert_called_once_with(message)
    websocket2.send_json.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_handle_bot_mentions(chat_server):
    """Test handling bot mentions in messages."""
    # Mock the bot process_message method
    for bot in chat_server.bots:
        future = asyncio.Future()
        future.set_result(f"Response from {bot.name}")
        bot.process_message = MagicMock(return_value=future)
    
    # Create a message mentioning a bot
    message = Message(content="Hey @curator, how are you?", author="test_user")
    
    # Handle bot mentions
    responses = await chat_server.handle_bot_mentions(message, "test_channel")
    
    # Verify the bot was called and a response was generated
    assert len(responses) == 1
    assert responses[0].content == "Response from curator"
    assert responses[0].author == "curator"
    
    # Test mentioning multiple bots
    message = Message(content="@curator and @normie, help me!", author="test_user")
    responses = await chat_server.handle_bot_mentions(message, "test_channel")
    
    # Verify both bots were called and responses were generated
    assert len(responses) == 2
    assert any(r.author == "curator" for r in responses)
    assert any(r.author == "normie" for r in responses) 
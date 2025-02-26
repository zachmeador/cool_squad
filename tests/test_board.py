"""
Tests for the board functionality of cool_squad.
"""

import pytest
import asyncio
import json
from unittest.mock import MagicMock, patch, AsyncMock
from cool_squad.board import BoardServer
from cool_squad.core import Message, Board, Thread
from cool_squad.storage import Storage


@pytest.fixture
def mock_storage():
    """Create a mock storage instance."""
    storage = MagicMock(spec=Storage)
    
    # Set up the mock to return an empty board
    empty_board = Board("test_board")
    storage.load_board.return_value = empty_board
    
    return storage


@pytest.fixture
def board_server(mock_storage):
    """Create a board server with mock storage."""
    return BoardServer(storage=mock_storage)


@pytest.fixture
def mock_websocket():
    """Create a mock websocket."""
    websocket = AsyncMock()
    return websocket


@pytest.mark.asyncio
async def test_register(board_server, mock_websocket):
    """Test that a websocket can be registered to a board."""
    # Register the websocket
    await board_server.register(mock_websocket, "test_board")
    
    # Verify the websocket was added to the connections
    assert "test_board" in board_server.connections
    assert mock_websocket in board_server.connections["test_board"]
    
    # Verify the board was loaded
    assert "test_board" in board_server.boards
    board_server.storage.load_board.assert_called_once_with("test_board")


@pytest.mark.asyncio
async def test_unregister(board_server, mock_websocket):
    """Test that a websocket can be unregistered from a board."""
    # Register the websocket first
    await board_server.register(mock_websocket, "test_board")
    
    # Unregister the websocket
    await board_server.unregister(mock_websocket, "test_board")
    
    # Verify the websocket was removed
    assert "test_board" not in board_server.connections


@pytest.mark.asyncio
async def test_broadcast(board_server, mock_websocket):
    """Test that messages can be broadcast to all websockets in a board."""
    # Register the websocket
    await board_server.register(mock_websocket, "test_board")
    
    # Broadcast a message
    test_message = {"type": "test", "content": "Hello, world!"}
    await board_server.broadcast("test_board", test_message)
    
    # Verify the message was sent
    mock_websocket.send.assert_called_once_with(json.dumps(test_message))


@pytest.mark.asyncio
async def test_create_thread(board_server):
    """Test creating a thread in a board."""
    # Create a board
    board = Board("test_board")
    board_server.boards["test_board"] = board
    
    # Create a thread
    message = Message(content="Hello, world!", author="test_user")
    thread = board.create_thread(title="Test Thread", first_message=message)
    
    # Add tags to the thread
    thread.tags = {"test", "example"}
    
    # Verify the thread was created
    assert len(board.threads) == 1
    assert board.threads[0].title == "Test Thread"
    assert board.threads[0].first_message.content == "Hello, world!"
    assert board.threads[0].first_message.author == "test_user"
    assert board.threads[0].tags == {"test", "example"} 
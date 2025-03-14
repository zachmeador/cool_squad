"""
Tests for the board client functionality of cool_squad.
"""

import pytest
import asyncio
import json
from unittest.mock import MagicMock, patch, AsyncMock
from cool_squad.clients.cli import CLIClient

@pytest.mark.asyncio
async def test_receive_board_messages():
    """Test receiving board messages via SSE."""
    client = CLIClient("test_user", "test_board")
    
    # Mock aiohttp ClientSession and response
    mock_response = AsyncMock()
    mock_response.content.__aiter__.return_value = [
        b'data: {"type":"board_update","board":{"threads":[{"title":"Test Thread","author":"user1"}]}}\n\n',
        b'data: {"type":"thread_update","thread":{"title":"Test Thread","messages":[{"author":"user1","content":"Hello"}]}}\n\n'
    ]
    
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        # Run receive_board_messages for a short time
        task = asyncio.create_task(client.receive_board_messages())
        await asyncio.sleep(0.1)  # Give it time to process messages
        client.running = False  # Stop the loop
        await task

@pytest.mark.asyncio
async def test_send_board_messages():
    """Test sending board messages."""
    client = CLIClient("test_user", "test_board")
    
    # Mock aiohttp ClientSession and responses
    mock_response = AsyncMock()
    mock_response.status = 200
    
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.post.return_value.__aenter__.return_value = mock_response
    
    # Mock input function to simulate user commands
    inputs = ["t", "Test Thread", "Hello, world!", "q"]
    input_iter = iter(inputs)
    
    with patch('builtins.input', side_effect=lambda _: next(input_iter)), \
         patch('aiohttp.ClientSession', return_value=mock_session):
        await client.send_board_messages()
    
    # Verify that the post request was made with correct data
    mock_session.post.assert_called_once_with(
        "http://localhost:8000/api/boards/test_board/threads",
        json={
            "title": "Test Thread",
            "message": "Hello, world!",
            "author": "test_user"
        }
    ) 
"""
Tests for the board client functionality of cool_squad.
"""

import pytest
import asyncio
import json
from unittest.mock import MagicMock, patch, AsyncMock
from cool_squad.clients.cli import send_board_messages


@pytest.mark.asyncio
async def test_send_messages_view_thread():
    """Test sending view thread command."""
    # Create a mock websocket
    websocket = AsyncMock()
    
    # Mock the input function to return "/view 0" and then "/quit"
    inputs = ["/view 0", "/quit"]
    input_index = 0
    
    async def mock_run_in_executor(*args, **kwargs):
        nonlocal input_index
        result = inputs[input_index]
        input_index += 1
        return result
    
    with patch('asyncio.get_event_loop') as mock_loop:
        mock_executor = AsyncMock()
        mock_executor.run_in_executor.side_effect = mock_run_in_executor
        mock_loop.return_value = mock_executor
        
        # Test the send_messages function
        await send_board_messages(websocket, "test_user", "test_board")
        
        # Verify that the view thread message was sent
        expected_message = json.dumps({
            "type": "get_thread",
            "thread_id": 0
        })
        websocket.send.assert_any_call(expected_message)


@pytest.mark.asyncio
async def test_send_messages_new_thread():
    """Test sending new thread command."""
    # Create a mock websocket
    websocket = AsyncMock()
    
    # Mock the input function to return "/new Test Thread", "Hello, world!" and then "/quit"
    inputs = ["/new Test Thread", "Hello, world!", "/quit"]
    input_index = 0
    
    async def mock_run_in_executor(*args, **kwargs):
        nonlocal input_index
        result = inputs[input_index]
        input_index += 1
        return result
    
    with patch('asyncio.get_event_loop') as mock_loop:
        mock_executor = AsyncMock()
        mock_executor.run_in_executor.side_effect = mock_run_in_executor
        mock_loop.return_value = mock_executor
        
        # Test the send_messages function
        await send_board_messages(websocket, "test_user", "test_board")
        
        # Verify that the new thread message was sent
        expected_message = json.dumps({
            "type": "create_thread",
            "title": "Test Thread",
            "content": "Hello, world!",
            "author": "test_user"
        })
        websocket.send.assert_any_call(expected_message) 
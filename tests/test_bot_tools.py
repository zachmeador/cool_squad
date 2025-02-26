import pytest
import asyncio
from unittest.mock import MagicMock, patch
from cool_squad.core import Message, Channel, Board, Thread
from cool_squad.bot_tools import BotTools

@pytest.fixture
def mock_storage():
    """Create a mock storage instance."""
    storage = MagicMock()
    
    # Mock channel
    channel = Channel(name="test-channel")
    channel.add_message(Message(content="Test message 1", author="user1"))
    channel.add_message(Message(content="Test message 2", author="user2"))
    
    # Mock board
    board = Board(name="test-board")
    thread = Thread(
        title="Test thread",
        first_message=Message(content="First post", author="user1")
    )
    thread.add_message(Message(content="Reply 1", author="user2"))
    thread.tags.add("test")
    board.threads.append(thread)
    
    # Configure storage mock
    storage.load_channel.return_value = channel
    storage.load_board.return_value = board
    
    return storage

@pytest.mark.asyncio
async def test_read_channel_messages(mock_storage):
    """Test reading channel messages."""
    tools = BotTools(storage=mock_storage)
    result = await tools.read_channel_messages("test-channel")
    
    assert "Recent messages in #test-channel" in result
    assert "[user1]: Test message 1" in result
    assert "[user2]: Test message 2" in result
    mock_storage.load_channel.assert_called_once_with("test-channel")

@pytest.mark.asyncio
async def test_post_channel_message(mock_storage):
    """Test posting a message to a channel."""
    tools = BotTools(storage=mock_storage)
    result = await tools.post_channel_message("test-channel", "New message", "bot")
    
    assert "Message posted to #test-channel" in result
    mock_storage.load_channel.assert_called_once_with("test-channel")
    mock_storage.save_channel.assert_called_once()

@pytest.mark.asyncio
async def test_read_board_threads(mock_storage):
    """Test reading board threads."""
    tools = BotTools(storage=mock_storage)
    result = await tools.read_board_threads("test-board")
    
    assert "Threads on board 'test-board'" in result
    assert "Test thread" in result
    assert "[tags: test]" in result
    mock_storage.load_board.assert_called_once_with("test-board")

@pytest.mark.asyncio
async def test_read_thread(mock_storage):
    """Test reading a thread."""
    tools = BotTools(storage=mock_storage)
    result = await tools.read_thread("test-board", 1)
    
    assert "Thread: Test thread" in result
    assert "Tags: test" in result
    assert "[user1]: First post" in result
    assert "[user2]: Reply 1" in result
    mock_storage.load_board.assert_called_once_with("test-board")

@pytest.mark.asyncio
async def test_post_thread_reply(mock_storage):
    """Test posting a reply to a thread."""
    tools = BotTools(storage=mock_storage)
    result = await tools.post_thread_reply("test-board", 1, "Bot reply", "bot")
    
    assert "Reply posted to thread 'Test thread'" in result
    mock_storage.load_board.assert_called_once_with("test-board")
    mock_storage.save_board.assert_called_once()

@pytest.mark.asyncio
async def test_create_thread(mock_storage):
    """Test creating a new thread."""
    tools = BotTools(storage=mock_storage)
    result = await tools.create_thread(
        "test-board", "New thread", "First post", "bot", ["new", "important"]
    )
    
    assert "Created new thread 'New thread'" in result
    mock_storage.load_board.assert_called_once_with("test-board")
    mock_storage.save_board.assert_called_once() 
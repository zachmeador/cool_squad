"""
Tests for the storage functionality of cool_squad.
"""

import os
import tempfile
import pytest
from cool_squad.core.models import Message, Channel, Board, Thread
from cool_squad.storage.storage import Storage


@pytest.fixture
def temp_storage():
    """Create a temporary storage for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = Storage(data_dir=temp_dir)
        yield storage


def test_channel_save_load(temp_storage):
    """Test saving and loading a channel."""
    # Create a channel with messages
    channel = Channel(name="test_channel")
    channel.add_message(Message(content="Message 1", author="user1"))
    channel.add_message(Message(content="Message 2", author="user2"))
    
    # Save the channel
    temp_storage.save_channel(channel)
    
    # Load the channel
    loaded_channel = temp_storage.load_channel("test_channel")
    
    # Verify the loaded channel
    assert loaded_channel.name == "test_channel"
    assert len(loaded_channel.messages) == 2
    assert loaded_channel.messages[0].content == "Message 1"
    assert loaded_channel.messages[0].author == "user1"
    assert loaded_channel.messages[1].content == "Message 2"
    assert loaded_channel.messages[1].author == "user2"


def test_board_save_load(temp_storage):
    """Test saving and loading a board."""
    # Create a board with threads
    board = Board(name="test_board")
    
    # Create first thread
    first_msg = Message(content="Thread 1 first post", author="user1")
    thread1 = board.create_thread(title="Thread 1", first_message=first_msg)
    thread1.add_message(Message(content="Thread 1 reply", author="user2"))
    thread1.tags = {"tag1", "tag2"}
    thread1.pinned = True
    
    # Create second thread
    second_msg = Message(content="Thread 2 first post", author="user3")
    thread2 = board.create_thread(title="Thread 2", first_message=second_msg)
    
    # Save the board
    temp_storage.save_board(board)
    
    # Load the board
    loaded_board = temp_storage.load_board("test_board")
    
    # Verify the loaded board
    assert loaded_board.name == "test_board"
    assert len(loaded_board.threads) == 2
    
    # Verify first thread
    assert loaded_board.threads[0].title == "Thread 1"
    assert len(loaded_board.threads[0].messages) == 2
    assert loaded_board.threads[0].messages[0].content == "Thread 1 first post"
    assert loaded_board.threads[0].messages[1].content == "Thread 1 reply"
    assert loaded_board.threads[0].pinned is True
    assert "tag1" in loaded_board.threads[0].tags
    assert "tag2" in loaded_board.threads[0].tags
    
    # Verify second thread
    assert loaded_board.threads[1].title == "Thread 2"
    assert len(loaded_board.threads[1].messages) == 1
    assert loaded_board.threads[1].messages[0].content == "Thread 2 first post"
    assert loaded_board.threads[1].pinned is False
    assert len(loaded_board.threads[1].tags) == 0


def test_nonexistent_channel(temp_storage):
    """Test loading a channel that doesn't exist."""
    channel = temp_storage.load_channel("nonexistent")
    assert channel.name == "nonexistent"
    assert len(channel.messages) == 0


def test_nonexistent_board(temp_storage):
    """Test loading a board that doesn't exist."""
    board = temp_storage.load_board("nonexistent")
    assert board.name == "nonexistent"
    assert len(board.threads) == 0 
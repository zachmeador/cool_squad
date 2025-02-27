"""
Tests for the core components of cool_squad.
"""

import pytest
from cool_squad.core.models import Message, Channel, Thread, Board


def test_message_creation():
    """Test that messages can be created correctly."""
    msg = Message(content="Hello, world!", author="test_user")
    assert msg.content == "Hello, world!"
    assert msg.author == "test_user"
    assert msg.timestamp is not None


def test_channel_creation():
    """Test that channels can be created and messages added."""
    channel = Channel(name="test_channel")
    assert channel.name == "test_channel"
    assert len(channel.messages) == 0
    
    # Add a message
    msg = Message(content="Hello, channel!", author="test_user")
    channel.add_message(msg)
    assert len(channel.messages) == 1
    assert channel.messages[0].content == "Hello, channel!"


def test_thread_creation():
    """Test that threads can be created and messages added."""
    first_msg = Message(content="First post!", author="test_user")
    thread = Thread(title="Test Thread", first_message=first_msg)
    
    assert thread.title == "Test Thread"
    assert len(thread.messages) == 1
    assert thread.messages[0].content == "First post!"
    
    # Add a reply
    reply = Message(content="First reply!", author="another_user")
    thread.add_message(reply)
    assert len(thread.messages) == 2
    assert thread.messages[1].content == "First reply!"


def test_board_creation():
    """Test that boards can be created and threads added."""
    board = Board(name="test_board")
    assert board.name == "test_board"
    assert len(board.threads) == 0
    
    # Create a thread
    first_msg = Message(content="First post!", author="test_user")
    thread = board.create_thread(title="Test Thread", first_message=first_msg)
    
    assert len(board.threads) == 1
    assert board.threads[0].title == "Test Thread"
    assert len(board.threads[0].messages) == 1 
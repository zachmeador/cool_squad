"""
Tests for the knowledge base functionality of cool_squad.
"""

import pytest
import os
import tempfile
import asyncio
from unittest.mock import MagicMock, patch
from cool_squad.knowledge import KnowledgeBase
from cool_squad.core import Message, Thread, Board
from cool_squad.storage import Storage


@pytest.fixture
def temp_knowledge_base():
    """Create a temporary knowledge base for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = Storage(data_dir=temp_dir)
        kb = KnowledgeBase(storage=storage)
        yield kb


@pytest.fixture
def sample_board():
    """Create a sample board with threads for testing."""
    board = Board(name="test_board")
    
    # Create first thread
    first_msg = Message(content="This is a thread about Python", author="user1")
    thread1 = board.create_thread(title="Python Programming", first_message=first_msg)
    thread1.add_message(Message(content="Python is great for data science", author="user2"))
    thread1.add_message(Message(content="I love using pandas and numpy", author="user1"))
    thread1.tags = {"python", "programming"}
    
    # Create second thread
    second_msg = Message(content="Let's talk about JavaScript", author="user3")
    thread2 = board.create_thread(title="JavaScript Basics", first_message=second_msg)
    thread2.add_message(Message(content="React is a popular framework", author="user1"))
    thread2.tags = {"javascript", "web"}
    
    return board


@pytest.mark.asyncio
async def test_generate_thread_summary(temp_knowledge_base, sample_board):
    """Test generating a summary for a thread."""
    # Test the placeholder implementation
    thread = sample_board.threads[0]
    summary = await temp_knowledge_base.summarize_thread(thread)
    assert summary == "Thread summary feature coming soon."


@pytest.mark.asyncio
async def test_create_page_from_thread(temp_knowledge_base, sample_board):
    """Test creating a knowledge page from a thread."""
    # Test the placeholder implementation
    thread = sample_board.threads[0]
    page_path = await temp_knowledge_base.create_page_from_thread(thread)
    expected_path = temp_knowledge_base._page_path(thread.title)
    assert page_path == expected_path


@pytest.mark.asyncio
async def test_update_index(temp_knowledge_base):
    """Test updating the knowledge base index."""
    # Test the placeholder implementation
    result = await temp_knowledge_base.update_index()
    assert result is None


@pytest.mark.asyncio
async def test_update_knowledge_base(temp_knowledge_base):
    """Test updating the entire knowledge base."""
    # Test the placeholder implementation
    result = await temp_knowledge_base.update_knowledge_base()
    assert result == temp_knowledge_base.knowledge_dir 
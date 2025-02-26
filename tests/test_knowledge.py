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
    # Mock the OpenAI API
    with patch('cool_squad.knowledge.openai') as mock_openai:
        # Set up the mock to return a response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a summary about Python programming."
        
        # Create a mock async method
        async def mock_create(*args, **kwargs):
            return mock_response
        
        # Set up the mock chat completions create method
        mock_openai.chat = MagicMock()
        mock_openai.chat.completions = MagicMock()
        mock_openai.chat.completions.create = mock_create
        
        # Generate a summary for the first thread
        thread = sample_board.threads[0]
        summary = await temp_knowledge_base.summarize_thread(thread)
        
        # Verify the summary
        assert summary == "This is a summary about Python programming."


@pytest.mark.asyncio
async def test_create_page_from_thread(temp_knowledge_base, sample_board):
    """Test generating an HTML page for a thread."""
    # Mock the thread summary generation
    with patch.object(temp_knowledge_base, 'summarize_thread') as mock_summarize:
        future = asyncio.Future()
        future.set_result("Thread summary")
        mock_summarize.return_value = future
        
        # Generate the thread page
        thread = sample_board.threads[0]
        page_path = await temp_knowledge_base.create_page_from_thread(thread)
        
        # Verify the HTML file was created
        assert os.path.exists(page_path)
        
        # Check the content of the file
        with open(page_path, 'r') as f:
            content = f.read()
            assert "Python Programming" in content
            assert "Thread summary" in content
            assert "user1" in content
            assert "user2" in content


@pytest.mark.asyncio
async def test_update_index(temp_knowledge_base):
    """Test updating the index HTML page."""
    # Create mock pages
    os.makedirs(os.path.join(temp_knowledge_base.knowledge_dir, "pages"), exist_ok=True)
    with open(os.path.join(temp_knowledge_base.knowledge_dir, "pages", "page1.html"), 'w') as f:
        f.write("<html><head><title>Page 1</title></head><body>Test page 1</body></html>")
    with open(os.path.join(temp_knowledge_base.knowledge_dir, "pages", "page2.html"), 'w') as f:
        f.write("<html><head><title>Page 2</title></head><body>Test page 2</body></html>")
    
    # Update the index
    await temp_knowledge_base.update_index()
    
    # Verify the index file was created
    index_path = temp_knowledge_base._index_path()
    assert os.path.exists(index_path)
    
    # Check the content of the file
    with open(index_path, 'r') as f:
        content = f.read()
        assert "Knowledge Base" in content 
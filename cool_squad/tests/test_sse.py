import pytest
import asyncio
from fastapi.testclient import TestClient
from cool_squad.main import app
from cool_squad.storage.storage import Storage
from cool_squad.core.models import Channel, Message

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def mock_storage(monkeypatch):
    """Mock storage with test data."""
    storage = Storage()
    
    # Create a test channel with messages
    test_channel = Channel(name="test")
    test_channel.add_message(Message(content="test message 1", author="user1"))
    test_channel.add_message(Message(content="test message 2", author="user2"))
    
    # Mock the load_channel method
    def mock_load_channel(channel_name):
        if channel_name == "test":
            return test_channel
        return Channel(name=channel_name)
    
    monkeypatch.setattr(Storage, "load_channel", mock_load_channel)
    return storage

def test_sse_endpoint(test_client, mock_storage):
    """Test the SSE endpoint."""
    # This is a basic test to ensure the endpoint exists and returns a 200 status
    response = test_client.get("/api/sse/chat/test?client_id=test-client")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"
    
    # Note: Testing the actual event stream is more complex and would require
    # a more sophisticated approach with async testing

def test_post_message(test_client, mock_storage):
    """Test posting a message to a channel."""
    response = test_client.post(
        "/api/channels/test/messages",
        json={"content": "hello world", "author": "test_user"}
    )
    assert response.status_code == 200
    
    # In a real test, we would verify that the message was added to the channel
    # and that connected clients received the message via SSE 
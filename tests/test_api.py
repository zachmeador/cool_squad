import pytest
from fastapi.testclient import TestClient
import os
import shutil
import tempfile

from cool_squad.main import app
from cool_squad.storage.storage import Storage
from cool_squad.core.models import Channel, Message

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def temp_data_dir():
    # create a temporary directory for test data
    temp_dir = tempfile.mkdtemp()
    os.environ["COOL_SQUAD_DATA_DIR"] = temp_dir
    
    yield temp_dir
    
    # cleanup after test
    shutil.rmtree(temp_dir)

def test_get_channels_empty(test_client, temp_data_dir):
    """Test getting channels when none exist"""
    response = test_client.get("/api/channels")
    assert response.status_code == 200
    assert response.json() == []

def test_post_message_and_get_channel(test_client, temp_data_dir):
    """Test posting a message to a channel and then retrieving it"""
    # post a message to a new channel
    message_data = {
        "content": "test message",
        "author": "test_user"
    }
    response = test_client.post("/api/channels/test_channel/messages", json=message_data)
    assert response.status_code == 200
    
    # verify the message was posted
    posted_message = response.json()
    assert posted_message["content"] == "test message"
    assert posted_message["author"] == "test_user"
    assert "timestamp" in posted_message
    
    # get the channel
    response = test_client.get("/api/channels/test_channel")
    assert response.status_code == 200
    
    # verify the channel contains the message
    channel_data = response.json()
    assert channel_data["name"] == "test_channel"
    assert len(channel_data["messages"]) == 1
    assert channel_data["messages"][0]["content"] == "test message"
    assert channel_data["messages"][0]["author"] == "test_user"

def test_get_channels_after_creating(test_client, temp_data_dir):
    """Test that channels list includes newly created channels"""
    # create a channel by posting a message
    message_data = {"content": "hello", "author": "user"}
    test_client.post("/api/channels/channel1/messages", json=message_data)
    
    # create another channel
    test_client.post("/api/channels/channel2/messages", json=message_data)
    
    # get the list of channels
    response = test_client.get("/api/channels")
    assert response.status_code == 200
    
    # verify both channels are in the list
    channels = response.json()
    assert "channel1" in channels
    assert "channel2" in channels

def test_boards_api(test_client, temp_data_dir):
    """Test the boards API endpoints"""
    # create a new thread with initial message
    thread_data = {
        "title": "Test Thread"
    }
    message_data = {
        "content": "Initial message",
        "author": "test_user"
    }
    
    # post the thread
    response = test_client.post(
        "/api/boards/test_board/threads", 
        json={"title": thread_data["title"], "first_message": message_data}
    )
    assert response.status_code == 200
    
    # verify the thread was created
    created_thread = response.json()
    assert created_thread["title"] == "Test Thread"
    
    # get the list of boards
    response = test_client.get("/api/boards")
    assert response.status_code == 200
    boards = response.json()
    assert len(boards) == 1
    assert boards[0]["name"] == "test_board"
    
    # get the threads in the board
    response = test_client.get("/api/boards/test_board")
    assert response.status_code == 200
    threads = response.json()
    assert len(threads) == 1
    assert threads[0]["title"] == "Test Thread"
    
    # get the thread details
    thread_id = threads[0]["id"]
    response = test_client.get(f"/api/boards/test_board/threads/{thread_id}")
    assert response.status_code == 200
    thread_detail = response.json()
    assert thread_detail["title"] == "Test Thread"
    assert len(thread_detail["messages"]) == 1
    assert thread_detail["messages"][0]["content"] == "Initial message" 
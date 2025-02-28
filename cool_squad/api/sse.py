import asyncio
from typing import Dict, List, Set, Any, Optional
from fastapi import APIRouter, Request, Response, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from cool_squad.core.models import Message, Channel
from cool_squad.storage.storage import Storage
import json
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
storage = Storage()

# Store active connections
connections: Dict[str, Set[str]] = {}
# Store client IDs for each connection
client_ids: Dict[str, str] = {}
# Message queue for each channel
message_queues: Dict[str, asyncio.Queue] = {}

# Message queues for different channels
chat_queues: Dict[str, Dict[str, asyncio.Queue]] = {}
board_queues: Dict[str, Dict[str, asyncio.Queue]] = {}

# Keep track of connected clients
connected_chat_clients: Dict[str, Set[str]] = {}
connected_board_clients: Dict[str, Set[str]] = {}

# Store messages for each channel
chat_messages: Dict[str, List[Dict[str, Any]]] = {}
board_data: Dict[str, Dict[str, Any]] = {}
thread_data: Dict[str, Dict[str, Dict[str, Any]]] = {}

async def event_generator(request: Request, channel: str, client_id: str):
    """Generate events for SSE."""
    # Register this client
    if channel not in connections:
        connections[channel] = set()
    connections[channel].add(client_id)
    client_ids[client_id] = channel
    
    # Create message queue if it doesn't exist
    if channel not in message_queues:
        message_queues[channel] = asyncio.Queue()
    
    # Send initial channel history
    channel_data = storage.load_channel(channel)
    if channel_data:
        # Send last 50 messages
        for msg in channel_data.messages[-50:]:
            if await request.is_disconnected():
                break
                
            yield {
                "event": "message",
                "data": {
                    "type": "message",
                    "channel": channel,
                    "content": msg.content,
                    "author": msg.author,
                    "timestamp": msg.timestamp
                }
            }
    
    # Keep connection alive and listen for new messages
    while not await request.is_disconnected():
        try:
            # Try to get a message from the queue with a timeout
            message = await asyncio.wait_for(message_queues[channel].get(), timeout=1.0)
            
            yield {
                "event": "message",
                "data": message
            }
        except asyncio.TimeoutError:
            # Send a ping every second to keep the connection alive
            yield {
                "event": "ping",
                "data": ""
            }
        except Exception as e:
            print(f"error in event generator: {e}")
            break

@router.get("/sse/chat/{channel}")
async def sse_endpoint(request: Request, channel: str, client_id: str):
    """SSE endpoint for chat channels."""
    # Make sure the channel exists in storage
    if not storage.load_channel(channel):
        # Create the channel if it doesn't exist
        new_channel = Channel(name=channel)
        storage.save_channel(new_channel)
    
    event_generator_instance = event_generator(request, channel, client_id)
    return EventSourceResponse(event_generator_instance)

@router.post("/channels/{channel}/messages")
async def post_message(channel: str, message: dict):
    """Post a message to a channel."""
    # Load the channel
    channel_data = storage.load_channel(channel)
    if not channel_data:
        # Create the channel if it doesn't exist
        channel_data = Channel(name=channel)
    
    # Create and add the message
    msg = Message(
        content=message["content"],
        author=message["author"]
    )
    channel_data.add_message(msg)
    
    # Save the channel
    storage.save_channel(channel_data)
    
    # Broadcast the message to all clients
    await broadcast_to_channel(channel, {
        "type": "message",
        "channel": channel,
        "content": msg.content,
        "author": msg.author,
        "timestamp": msg.timestamp
    })
    
    return {"status": "success"}

@router.get("/channels")
async def get_channels():
    """Get a list of all channels."""
    return storage.list_channels()

# Function to broadcast a message to all clients in a channel
async def broadcast_to_channel(channel: str, message: Dict[str, Any]):
    """Broadcast a message to all clients in a channel."""
    if channel in message_queues:
        await message_queues[channel].put(message)

# Clean up when a client disconnects
@router.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown."""
    connections.clear()
    client_ids.clear()
    message_queues.clear()

# Helper function to format SSE message
def format_sse_message(data: Any, event: Optional[str] = None) -> str:
    message = ""
    if event is not None:
        message += f"event: {event}\n"
    message += f"data: {json.dumps(data)}\n\n"
    return message

# Helper function to broadcast message to all clients in a chat channel
async def broadcast_chat_message(channel: str, message: Dict[str, Any]):
    if channel not in chat_queues:
        return
    
    # Store message in history
    if channel not in chat_messages:
        chat_messages[channel] = []
    chat_messages[channel].append(message)
    
    # Limit history to last 100 messages
    chat_messages[channel] = chat_messages[channel][-100:]
    
    # Broadcast to all connected clients
    for client_queue in chat_queues[channel].values():
        await client_queue.put(format_sse_message({
            "type": "message",
            **message
        }))

# Helper function to broadcast board update to all clients
async def broadcast_board_update(board_id: str):
    if board_id not in board_queues:
        return
    
    # Get board data
    board = board_data.get(board_id, {"threads": []})
    
    # Broadcast to all connected clients
    for client_queue in board_queues[board_id].values():
        await client_queue.put(format_sse_message({
            "type": "board_update",
            "board": board
        }))

# Helper function to broadcast thread update to all clients
async def broadcast_thread_update(board_id: str, thread_id: str):
    if board_id not in board_queues:
        return
    
    # Get thread data
    thread = thread_data.get(board_id, {}).get(thread_id)
    if not thread:
        return
    
    # Broadcast to all connected clients
    for client_queue in board_queues[board_id].values():
        await client_queue.put(format_sse_message({
            "type": "thread_update",
            "thread": thread
        }))

# Background task to send ping events to keep connections alive
async def ping_client(queue: asyncio.Queue):
    while True:
        await asyncio.sleep(30)  # Send ping every 30 seconds
        await queue.put(format_sse_message({}, "ping"))

# SSE endpoint for chat
@router.get("/chat/{channel}")
async def sse_chat(
    request: Request, 
    response: Response,
    background_tasks: BackgroundTasks,
    channel: str,
    client_id: str
):
    if not channel or not client_id:
        raise HTTPException(status_code=400, detail="Channel and client_id are required")
    
    # Initialize channel if it doesn't exist
    if channel not in chat_queues:
        chat_queues[channel] = {}
        connected_chat_clients[channel] = set()
    
    # Create queue for this client
    queue = asyncio.Queue()
    chat_queues[channel][client_id] = queue
    connected_chat_clients[channel].add(client_id)
    
    # Add background task to send pings
    background_tasks.add_task(ping_client, queue)
    
    # Send message history
    if channel in chat_messages and chat_messages[channel]:
        await queue.put(format_sse_message({
            "type": "history",
            "messages": chat_messages[channel]
        }))
    
    logger.info(f"Client {client_id} connected to chat channel {channel}")
    
    async def event_generator():
        try:
            while True:
                # Wait for messages
                message = await queue.get()
                yield message
        except asyncio.CancelledError:
            # Client disconnected
            if channel in chat_queues and client_id in chat_queues[channel]:
                del chat_queues[channel][client_id]
                connected_chat_clients[channel].discard(client_id)
                logger.info(f"Client {client_id} disconnected from chat channel {channel}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

# SSE endpoint for board
@router.get("/board/{board_id}")
async def sse_board(
    request: Request, 
    response: Response,
    background_tasks: BackgroundTasks,
    board_id: str,
    client_id: str
):
    if not board_id or not client_id:
        raise HTTPException(status_code=400, detail="Board ID and client_id are required")
    
    # Initialize board if it doesn't exist
    if board_id not in board_queues:
        board_queues[board_id] = {}
        connected_board_clients[board_id] = set()
        board_data[board_id] = {"threads": []}
    
    # Create queue for this client
    queue = asyncio.Queue()
    board_queues[board_id][client_id] = queue
    connected_board_clients[board_id].add(client_id)
    
    # Add background task to send pings
    background_tasks.add_task(ping_client, queue)
    
    # Send initial board data
    await queue.put(format_sse_message({
        "type": "board_update",
        "board": board_data.get(board_id, {"threads": []})
    }))
    
    logger.info(f"Client {client_id} connected to board {board_id}")
    
    async def event_generator():
        try:
            while True:
                # Wait for messages
                message = await queue.get()
                yield message
        except asyncio.CancelledError:
            # Client disconnected
            if board_id in board_queues and client_id in board_queues[board_id]:
                del board_queues[board_id][client_id]
                connected_board_clients[board_id].discard(client_id)
                logger.info(f"Client {client_id} disconnected from board {board_id}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

# Endpoint to post a message to a chat channel
@router.post("/channels/{channel}/messages")
async def post_message(
    channel: str,
    message: dict
):
    if not channel:
        raise HTTPException(status_code=400, detail="Channel is required")
    
    if "content" not in message or "author" not in message:
        raise HTTPException(status_code=400, detail="Content and author are required")
    
    # Create message object
    msg = {
        "content": message["content"],
        "author": message["author"],
        "timestamp": time.time()
    }
    
    # Broadcast message to all clients
    await broadcast_chat_message(channel, msg)
    
    return {"status": "message sent"}

# Endpoint to create a new thread in a board
@router.post("/boards/{board_id}/threads")
async def create_thread(
    board_id: str,
    thread_data: dict
):
    if not board_id:
        raise HTTPException(status_code=400, detail="Board ID is required")
    
    if "title" not in thread_data or "message" not in thread_data or "author" not in thread_data:
        raise HTTPException(status_code=400, detail="Title, message, and author are required")
    
    # Initialize board if it doesn't exist
    if board_id not in board_data:
        board_data[board_id] = {"threads": []}
    
    if board_id not in thread_data:
        thread_data[board_id] = {}
    
    # Create thread ID
    thread_id = f"thread-{int(time.time())}"
    
    # Create thread object
    thread = {
        "id": thread_id,
        "title": thread_data["title"],
        "author": thread_data["author"],
        "created_at": time.time(),
        "pinned": False,
        "tags": thread_data.get("tags", []),
        "messages": [
            {
                "content": thread_data["message"],
                "author": thread_data["author"],
                "timestamp": time.time()
            }
        ]
    }
    
    # Add thread to board
    board_data[board_id]["threads"].insert(0, {
        "id": thread_id,
        "title": thread_data["title"],
        "author": thread_data["author"],
        "created_at": time.time(),
        "pinned": False,
        "tags": thread_data.get("tags", [])
    })
    
    # Store thread data
    thread_data[board_id][thread_id] = thread
    
    # Broadcast board update to all clients
    await broadcast_board_update(board_id)
    
    return {"status": "thread created", "thread_id": thread_id}

# Endpoint to post a message to a thread
@router.post("/boards/{board_id}/threads/{thread_id}/messages")
async def post_thread_message(
    board_id: str,
    thread_id: str,
    message: dict
):
    if not board_id or not thread_id:
        raise HTTPException(status_code=400, detail="Board ID and thread ID are required")
    
    if "content" not in message or "author" not in message:
        raise HTTPException(status_code=400, detail="Content and author are required")
    
    # Check if thread exists
    if board_id not in thread_data or thread_id not in thread_data[board_id]:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Create message object
    msg = {
        "content": message["content"],
        "author": message["author"],
        "timestamp": time.time()
    }
    
    # Add message to thread
    thread_data[board_id][thread_id]["messages"].append(msg)
    
    # Broadcast thread update to all clients
    await broadcast_thread_update(board_id, thread_id)
    
    return {"status": "message sent"}

# Endpoint to get a thread
@router.get("/boards/{board_id}/threads/{thread_id}")
async def get_thread(
    board_id: str,
    thread_id: str
):
    if not board_id or not thread_id:
        raise HTTPException(status_code=400, detail="Board ID and thread ID are required")
    
    # Check if thread exists
    if board_id not in thread_data or thread_id not in thread_data[board_id]:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    return thread_data[board_id][thread_id] 
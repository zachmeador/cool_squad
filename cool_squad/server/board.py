import asyncio
import json
import time
import uuid
from typing import Dict, Set, List, Optional
from cool_squad.core.models import Message
from cool_squad.storage.storage import Storage

class Thread:
    def __init__(self, id: str, title: str, author: str, created_at: float = None, 
                 pinned: bool = False, tags: List[str] = None):
        self.id = id
        self.title = title
        self.author = author
        self.created_at = created_at or time.time()
        self.messages: List[Message] = []
        self.pinned = pinned
        self.tags = tags or []
    
    def add_message(self, message: Message):
        self.messages.append(message)
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "created_at": self.created_at,
            "messages": [msg.__dict__ for msg in self.messages],
            "pinned": self.pinned,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data):
        thread = cls(
            id=data["id"],
            title=data["title"],
            author=data["author"],
            created_at=data["created_at"],
            pinned=data.get("pinned", False),
            tags=data.get("tags", [])
        )
        
        for msg_data in data["messages"]:
            msg = Message(
                content=msg_data["content"],
                author=msg_data["author"],
                timestamp=msg_data.get("timestamp")
            )
            thread.messages.append(msg)
        
        return thread

class Board:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.threads: List[Thread] = []
    
    def add_thread(self, thread: Thread):
        self.threads.append(thread)
        # Sort threads by pinned status (pinned first) and then by created_at (newest first)
        self.threads.sort(key=lambda t: (-int(t.pinned), -t.created_at))
    
    def get_thread(self, thread_id: str) -> Optional[Thread]:
        for thread in self.threads:
            if thread.id == thread_id:
                return thread
        return None
    
    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "threads": [thread.to_dict() for thread in self.threads]
        }
    
    @classmethod
    def from_dict(cls, data):
        board = cls(
            name=data["name"],
            description=data.get("description", "")
        )
        
        for thread_data in data["threads"]:
            thread = Thread.from_dict(thread_data)
            board.add_thread(thread)
        
        return board

class BoardServer:
    def __init__(self, storage: Storage):
        self.storage = storage
        self.connections: Dict[str, Set] = {}
        self.boards: Dict[str, Board] = {}
    
    async def register(self, websocket, board_name: str):
        """Register a websocket connection for a board."""
        if board_name not in self.connections:
            self.connections[board_name] = set()
        self.connections[board_name].add(websocket)
        
        # Load the board if it's not already loaded
        if board_name not in self.boards:
            self.boards[board_name] = self.storage.load_board(board_name)
    
    async def unregister(self, websocket, board_name: str):
        """Unregister a websocket connection for a board."""
        if board_name in self.connections:
            self.connections[board_name].discard(websocket)
            if not self.connections[board_name]:
                del self.connections[board_name]
    
    async def broadcast(self, board_name: str, message: dict):
        """Broadcast a message to all connected clients for a board."""
        if board_name in self.connections:
            for connection in self.connections[board_name].copy():
                try:
                    await connection.send_json(message)
                except Exception:
                    # Connection might be closed or invalid
                    self.connections[board_name].discard(connection)
    
    async def broadcast_board_update(self, board_name: str):
        """Broadcast board update to all connected clients"""
        board = self.storage.load_board(board_name)
        if board and board_name in self.connections:
            await self.broadcast(board_name, {
                "type": "board_update",
                "board": board.to_dict()
            })
    
    async def broadcast_thread_update(self, board_name: str, thread_id: str):
        """Broadcast thread update to all connected clients"""
        board = self.storage.load_board(board_name)
        if board and board_name in self.connections:
            thread = board.get_thread(thread_id)
            if thread:
                await self.broadcast(board_name, {
                    "type": "thread_update",
                    "thread": thread.to_dict()
                })

    async def handle_connection(self, websocket, board_name: str):
        """Handle a FastAPI WebSocket connection"""
        # Accept the connection
        await websocket.accept()
        
        # Register the connection
        if board_name not in self.connections:
            self.connections[board_name] = set()
        self.connections[board_name].add(websocket)
        
        try:
            # Send current board state
            board = self.storage.load_board(board_name)
            await websocket.send_json({
                "type": "board_state",
                "board": board.to_dict() if board else {"name": board_name, "description": "", "threads": []}
            })
            
            # Handle incoming messages
            while True:
                data = await websocket.receive_json()
                
                if data["type"] == "create_thread":
                    # Create a new thread
                    board = self.storage.load_board(board_name)
                    if not board:
                        board = Board(name=board_name)
                    
                    thread_id = str(uuid.uuid4())
                    thread = Thread(
                        id=thread_id,
                        title=data["title"],
                        author=data["author"]
                    )
                    
                    # Add initial message if provided
                    if "message" in data:
                        msg = Message(
                            content=data["message"],
                            author=data["author"]
                        )
                        thread.add_message(msg)
                    
                    board.add_thread(thread)
                    self.storage.save_board(board)
                    
                    # Broadcast board update
                    await self.broadcast_board_update(board_name)
                
                elif data["type"] == "post_message":
                    # Add a message to a thread
                    thread_id = data["thread_id"]
                    board = self.storage.load_board(board_name)
                    
                    if board:
                        thread = board.get_thread(thread_id)
                        if thread:
                            msg = Message(
                                content=data["content"],
                                author=data["author"]
                            )
                            thread.add_message(msg)
                            self.storage.save_board(board)
                            
                            # Broadcast thread update
                            await self.broadcast_thread_update(board_name, thread_id)
                
                elif data["type"] == "pin_thread":
                    # Pin or unpin a thread
                    thread_id = data["thread_id"]
                    board = self.storage.load_board(board_name)
                    
                    if board:
                        thread = board.get_thread(thread_id)
                        if thread:
                            thread.pinned = data.get("pinned", True)
                            # Re-sort threads
                            board.threads.sort(key=lambda t: (-int(t.pinned), -t.created_at))
                            self.storage.save_board(board)
                            
                            # Broadcast board update
                            await self.broadcast_board_update(board_name)
                
                elif data["type"] == "tag_thread":
                    # Add tags to a thread
                    thread_id = data["thread_id"]
                    tags = data["tags"]
                    board = self.storage.load_board(board_name)
                    
                    if board:
                        thread = board.get_thread(thread_id)
                        if thread:
                            thread.tags = list(set(thread.tags + tags))  # Add unique tags
                            self.storage.save_board(board)
                            
                            # Broadcast thread update
                            await self.broadcast_thread_update(board_name, thread_id)
        except Exception:
            # Handle disconnection
            pass
        finally:
            # Unregister the connection
            await self.unregister(websocket, board_name) 
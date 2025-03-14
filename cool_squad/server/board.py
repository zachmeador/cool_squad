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
    
    def create_thread(self, title: str, first_message: Message) -> Thread:
        """Create a new thread with an initial message."""
        thread_id = str(uuid.uuid4())
        thread = Thread(
            id=thread_id,
            title=title,
            author=first_message.author
        )
        thread.add_message(first_message)
        self.add_thread(thread)
        return thread
    
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
        self.boards: Dict[str, Board] = {}
        
        # load existing boards from storage
        for board in self.storage.list_boards():
            self.boards[board.name] = board
    
    def list_boards(self) -> List[Board]:
        """List all available boards."""
        return list(self.boards.values())

    def get_board(self, board_name: str) -> Optional[Board]:
        """Get a board by name."""
        if board_name not in self.boards:
            board = self.storage.load_board(board_name)
            if board:
                self.boards[board_name] = board
        return self.boards.get(board_name)

    def save_board(self, board: Board):
        """Save a board to storage."""
        self.boards[board.name] = board
        self.storage.save_board(board)
    
    async def broadcast_board_update(self, board_name: str):
        """Broadcast board update to all connected clients"""
        from cool_squad.api.sse import broadcast_board_update
        await broadcast_board_update(board_name)
    
    async def broadcast_thread_update(self, board_name: str, thread_id: str):
        """Broadcast thread update to all connected clients"""
        from cool_squad.api.sse import broadcast_thread_update
        await broadcast_thread_update(board_name, thread_id)
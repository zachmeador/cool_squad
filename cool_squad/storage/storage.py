import json
import os
from pathlib import Path
from typing import Dict, List
from cool_squad.core.models import Channel, Message, Board, Thread
from cool_squad.core.config import get_data_dir

class Storage:
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or get_data_dir()
        self.channels_dir = os.path.join(self.data_dir, "channels")
        self.boards_dir = os.path.join(self.data_dir, "boards")
        
        # create directories if they don't exist
        for directory in [self.data_dir, self.channels_dir, self.boards_dir]:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _channel_path(self, channel_name: str) -> str:
        """Get the file path for a channel's data."""
        return os.path.join(self.channels_dir, f"{channel_name}.json")
    
    def _board_path(self, board_name: str) -> str:
        """Get the file path for a board's data."""
        return os.path.join(self.boards_dir, f"{board_name}.json")
    
    def list_channels(self) -> List[str]:
        """List all available channels."""
        channels = []
        for file in os.listdir(self.channels_dir):
            if file.endswith(".json"):
                channels.append(file[:-5])  # Remove .json extension
        return channels
    
    def list_boards(self) -> List[Board]:
        """List all available boards."""
        boards = []
        for file in os.listdir(self.boards_dir):
            if file.endswith(".json"):
                board_name = file[:-5]  # Remove .json extension
                boards.append(self.load_board(board_name))
        return boards
    
    def save_channel(self, channel: Channel) -> None:
        """Save a channel to disk."""
        channel_data = {
            "name": channel.name,
            "messages": [
                {
                    "content": msg.content,
                    "author": msg.author,
                    "timestamp": msg.timestamp
                }
                for msg in channel.messages
            ]
        }
        
        with open(self._channel_path(channel.name), 'w') as f:
            json.dump(channel_data, f, indent=2)
    
    def load_channel(self, channel_name: str) -> Channel:
        """Load a channel from disk or create a new one if it doesn't exist."""
        channel_path = self._channel_path(channel_name)
        
        if os.path.exists(channel_path):
            with open(channel_path, 'r') as f:
                data = json.load(f)
            
            messages = [
                Message(
                    content=msg["content"],
                    author=msg["author"],
                    timestamp=msg["timestamp"]
                )
                for msg in data["messages"]
            ]
            
            return Channel(name=channel_name, messages=messages)
        else:
            return Channel(name=channel_name)
    
    def save_board(self, board: Board) -> None:
        """Save a board to disk."""
        board_data = {
            "name": board.name,
            "threads": [
                {
                    "title": thread.title,
                    "pinned": thread.pinned,
                    "tags": list(thread.tags),
                    "messages": [
                        {
                            "content": msg.content,
                            "author": msg.author,
                            "timestamp": msg.timestamp
                        }
                        for msg in thread.messages
                    ]
                }
                for thread in board.threads
            ]
        }
        
        with open(self._board_path(board.name), 'w') as f:
            json.dump(board_data, f, indent=2)
    
    def load_board(self, board_name: str) -> Board:
        """Load a board from disk or create a new one if it doesn't exist."""
        board_path = self._board_path(board_name)
        
        if os.path.exists(board_path):
            with open(board_path, 'r') as f:
                data = json.load(f)
            
            board = Board(name=board_name)
            
            for thread_data in data["threads"]:
                messages = [
                    Message(
                        content=msg["content"],
                        author=msg["author"],
                        timestamp=msg["timestamp"]
                    )
                    for msg in thread_data["messages"]
                ]
                
                thread = Thread(
                    title=thread_data["title"],
                    first_message=messages[0],
                    messages=messages,
                    tags=set(thread_data["tags"]),
                    pinned=thread_data["pinned"]
                )
                
                board.threads.append(thread)
            
            return board
        else:
            return Board(name=board_name) 
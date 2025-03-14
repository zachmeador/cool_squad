import json
import os
from pathlib import Path
from typing import Dict, List
from cool_squad.core.models import Channel, Message, Board, Thread
from cool_squad.core.config import get_data_dir
import logging

logger = logging.getLogger(__name__)

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
            ],
            "bot_members": list(channel.bot_members)
        }
        
        with open(self._channel_path(channel.name), 'w') as f:
            json.dump(channel_data, f, indent=2)
    
    def load_channel(self, channel_name: str) -> Channel:
        """Load a channel from disk or create a new one if it doesn't exist."""
        channel_path = self._channel_path(channel_name)
        
        if os.path.exists(channel_path):
            try:
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
                
                channel = Channel(
                    name=channel_name,
                    messages=messages
                )
                
                # load bot members if they exist in the data
                if "bot_members" in data:
                    channel.bot_members.update(data["bot_members"])
                
                return channel
            except (json.JSONDecodeError, KeyError) as e:
                # handle empty or invalid json files
                logger.warning(f"error loading channel {channel_name}: {str(e)}. creating new channel.")
                return Channel(name=channel_name, messages=[])
        
        # create a new channel if it doesn't exist
        return Channel(name=channel_name, messages=[])
    
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
            try:
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
            except (json.JSONDecodeError, KeyError) as e:
                # handle empty or invalid json files
                logger.warning(f"error loading board {board_name}: {str(e)}. creating new board.")
                return Board(name=board_name)
        
        # create a new board if it doesn't exist
        return Board(name=board_name)
    
    def cleanup(self) -> None:
        """Delete all stored data."""
        for file in os.listdir(self.channels_dir):
            if file.endswith(".json"):
                os.remove(os.path.join(self.channels_dir, file))
        for file in os.listdir(self.boards_dir):
            if file.endswith(".json"):
                os.remove(os.path.join(self.boards_dir, file)) 
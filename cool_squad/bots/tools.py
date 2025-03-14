from typing import List, Dict, Any, Optional, Callable
import json
import os
from pathlib import Path
from cool_squad.core.models import Message, Thread, Board
from cool_squad.storage.storage import Storage
from dataclasses import dataclass
import logging
from cool_squad.llm.providers import ToolDefinition

logger = logging.getLogger(__name__)

@dataclass
class Tool:
    """tool definition"""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable
    required_params: Optional[List[str]] = None

    def to_tool_definition(self) -> ToolDefinition:
        """convert to ToolDefinition for llm providers"""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
            required_params=self.required_params
        )

class BotTools:
    """Collection of tools for bots to interact with chat and message boards."""
    
    def __init__(self, storage: Storage = None):
        self.storage = storage or Storage()
    
    async def read_channel_messages(self, channel_name: str, limit: int = 10) -> str:
        """
        Read recent messages from a chat channel.
        
        Args:
            channel_name: Name of the channel to read
            limit: Maximum number of messages to return (default: 10)
            
        Returns:
            String representation of the messages
        """
        channel = self.storage.load_channel(channel_name)
        messages = channel.messages[-limit:] if limit > 0 else channel.messages
        
        result = f"Recent messages in #{channel_name}:\n"
        for msg in messages:
            result += f"[{msg.author}]: {msg.content}\n"
        
        return result
    
    async def post_channel_message(self, channel_name: str, content: str, author: str) -> str:
        """
        Post a message to a chat channel.
        
        Args:
            channel_name: Name of the channel to post to
            content: Message content
            author: Name of the author (bot)
            
        Returns:
            Confirmation message or error message
        """
        channel = self.storage.load_channel(channel_name)
        
        # verify bot has permission to post in this channel
        if not channel.has_bot(author):
            return f"error: bot {author} is not a member of #{channel_name}"
        
        message = Message(content=content, author=author)
        channel.add_message(message)
        self.storage.save_channel(channel)
        
        return f"message posted to #{channel_name}"
    
    async def list_boards(self) -> str:
        """
        List all available message boards.
        
        Returns:
            String representation of available boards
        """
        # Get all board files
        boards_dir = Path(self.storage.boards_dir)
        board_files = list(boards_dir.glob("*.json"))
        board_names = [f.stem for f in board_files]
        
        if not board_names:
            return "No message boards found."
        
        return f"Available message boards: {', '.join(board_names)}"
    
    async def read_board_threads(self, board_name: str, limit: int = 5) -> str:
        """
        Read thread titles from a message board.
        
        Args:
            board_name: Name of the board to read
            limit: Maximum number of threads to return (default: 5)
            
        Returns:
            String representation of the threads
        """
        board = self.storage.load_board(board_name)
        threads = board.threads[-limit:] if limit > 0 else board.threads
        
        if not threads:
            return f"No threads found on board '{board_name}'."
        
        result = f"Threads on board '{board_name}':\n"
        for i, thread in enumerate(threads):
            tags = f" [tags: {', '.join(thread.tags)}]" if thread.tags else ""
            pinned = " [PINNED]" if thread.pinned else ""
            result += f"{i+1}. {thread.title}{pinned}{tags}\n"
        
        return result
    
    async def read_thread(self, board_name: str, thread_index: int) -> str:
        """
        Read messages from a specific thread.
        
        Args:
            board_name: Name of the board
            thread_index: Index of the thread (1-based)
            
        Returns:
            String representation of the thread messages
        """
        board = self.storage.load_board(board_name)
        
        if not board.threads or thread_index > len(board.threads) or thread_index < 1:
            return f"Thread {thread_index} not found on board '{board_name}'."
        
        thread = board.threads[thread_index - 1]
        
        result = f"Thread: {thread.title}\n"
        if thread.tags:
            result += f"Tags: {', '.join(thread.tags)}\n"
        if thread.pinned:
            result += "Status: PINNED\n"
        result += "\nMessages:\n"
        
        for msg in thread.messages:
            result += f"[{msg.author}]: {msg.content}\n"
        
        return result
    
    async def post_thread_reply(self, board_name: str, thread_index: int, content: str, author: str) -> str:
        """
        Post a reply to a thread.
        
        Args:
            board_name: Name of the board
            thread_index: Index of the thread (1-based)
            content: Message content
            author: Name of the author (bot)
            
        Returns:
            Confirmation message
        """
        board = self.storage.load_board(board_name)
        
        if not board.threads or thread_index > len(board.threads) or thread_index < 1:
            return f"Thread {thread_index} not found on board '{board_name}'."
        
        thread = board.threads[thread_index - 1]
        message = Message(content=content, author=author)
        thread.add_message(message)
        self.storage.save_board(board)
        
        return f"Reply posted to thread '{thread.title}' on board '{board_name}'."
    
    async def create_thread(self, board_name: str, title: str, content: str, author: str, tags: List[str] = None) -> str:
        """
        Create a new thread on a message board.
        
        Args:
            board_name: Name of the board
            title: Thread title
            content: First message content
            author: Name of the author (bot)
            tags: Optional list of tags
            
        Returns:
            Confirmation message
        """
        board = self.storage.load_board(board_name)
        message = Message(content=content, author=author)
        thread = board.create_thread(title=title, first_message=message)
        
        if tags:
            for tag in tags:
                thread.tags.add(tag)
        
        self.storage.save_board(board)
        
        return f"Created new thread '{title}' on board '{board_name}'."
    
    async def create_knowledge_page(self, board_name: str, thread_index: int) -> str:
        """
        Create a knowledge page from a thread.
        
        Args:
            board_name: Name of the board containing the thread
            thread_index: Index of the thread to create a page from
            
        Returns:
            Confirmation message with the page path
        """
        # Placeholder for future implementation
        return "Knowledge base feature coming soon."
    
    async def update_knowledge_index(self) -> str:
        """
        Update the knowledge base index.
        
        Returns:
            Confirmation message
        """
        # Placeholder for future implementation
        return "Knowledge base feature coming soon."
    
    async def update_entire_knowledge_base(self) -> str:
        """
        Update the entire knowledge base from all threads.
        
        Returns:
            Confirmation message
        """
        # Placeholder for future implementation
        return "Knowledge base feature coming soon."

# Tool definitions for bot function calling
CHANNEL_TOOLS = [
    {
        "type": "function",
        "name": "read_channel_messages",
        "description": "Read recent messages from a chat channel",
        "parameters": {
            "type": "object",
            "properties": {
                "channel_name": {
                    "type": "string",
                    "description": "Name of the channel to read"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of messages to return (default: 10)"
                }
            },
            "required": ["channel_name"],
            "additionalProperties": False
        }
    }
]

BOARD_TOOLS = [
    {
        "type": "function",
        "name": "list_boards",
        "description": "List all available message boards",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "read_board_threads",
        "description": "Read thread titles from a message board",
        "parameters": {
            "type": "object",
            "properties": {
                "board_name": {
                    "type": "string",
                    "description": "Name of the board to read"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of threads to return (default: 5)"
                }
            },
            "required": ["board_name"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "read_thread",
        "description": "Read messages from a specific thread",
        "parameters": {
            "type": "object",
            "properties": {
                "board_name": {
                    "type": "string",
                    "description": "Name of the board"
                },
                "thread_index": {
                    "type": "integer",
                    "description": "Index of the thread (1-based)"
                }
            },
            "required": ["board_name", "thread_index"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "post_thread_reply",
        "description": "Post a reply to a thread",
        "parameters": {
            "type": "object",
            "properties": {
                "board_name": {
                    "type": "string",
                    "description": "Name of the board"
                },
                "thread_index": {
                    "type": "integer",
                    "description": "Index of the thread (1-based)"
                },
                "content": {
                    "type": "string",
                    "description": "Message content"
                }
            },
            "required": ["board_name", "thread_index", "content"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "create_thread",
        "description": "Create a new thread on a message board",
        "parameters": {
            "type": "object",
            "properties": {
                "board_name": {
                    "type": "string",
                    "description": "Name of the board"
                },
                "title": {
                    "type": "string",
                    "description": "Thread title"
                },
                "content": {
                    "type": "string",
                    "description": "First message content"
                },
                "tags": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Optional list of tags"
                }
            },
            "required": ["board_name", "title", "content"],
            "additionalProperties": False
        }
    }
]

KNOWLEDGE_TOOLS = [
    {
        "type": "function",
        "name": "create_knowledge_page",
        "description": "Create a knowledge page from a thread (coming soon)",
        "parameters": {
            "type": "object",
            "properties": {
                "board_name": {
                    "type": "string",
                    "description": "Name of the board containing the thread"
                },
                "thread_index": {
                    "type": "integer",
                    "description": "Index of the thread to create a page from (0-based)"
                }
            },
            "required": ["board_name", "thread_index"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "update_knowledge_index",
        "description": "Update the knowledge base index (coming soon)",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "update_entire_knowledge_base",
        "description": "Update the entire knowledge base from all threads (coming soon)",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    }
]

def create_tools() -> List[Tool]:
    """
    create tool instances for a bot
    
    returns:
        list of tool instances
    """
    bot_tools = BotTools()
    tools = []
    
    # add channel tools
    for tool_def in CHANNEL_TOOLS:
        tool_func = getattr(bot_tools, tool_def["name"])
        tool = Tool(
            name=tool_def["name"],
            description=tool_def["description"],
            parameters=tool_def["parameters"]["properties"],
            required_params=tool_def["parameters"].get("required", []),
            function=tool_func
        )
        tools.append(tool)
    
    # add board tools
    for tool_def in BOARD_TOOLS:
        tool_func = getattr(bot_tools, tool_def["name"])
        tool = Tool(
            name=tool_def["name"],
            description=tool_def["description"],
            parameters=tool_def["parameters"]["properties"],
            required_params=tool_def["parameters"].get("required", []),
            function=tool_func
        )
        tools.append(tool)

    # add knowledge tools
    for tool_def in KNOWLEDGE_TOOLS:
        tool_func = getattr(bot_tools, tool_def["name"])
        tool = Tool(
            name=tool_def["name"],
            description=tool_def["description"],
            parameters=tool_def["parameters"]["properties"],
            required_params=tool_def["parameters"].get("required", []),
            function=tool_func
        )
        tools.append(tool)
    
    return tools 
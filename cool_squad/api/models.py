"""
Pydantic models for API requests and responses.
"""

from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


class MessageModel(BaseModel):
    """Message model for API requests and responses."""
    id: Optional[str] = None
    channel: Optional[str] = None
    author: str
    content: str
    timestamp: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)


class ChannelModel(BaseModel):
    """Channel model for API requests and responses."""
    name: str
    messages: Optional[List[MessageModel]] = None
    
    model_config = ConfigDict(from_attributes=True)


class BoardModel(BaseModel):
    """Board model for API requests and responses."""
    name: str
    threads: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)


class ThreadModel(BaseModel):
    id: str
    title: str
    author: str
    created_at: float
    pinned: bool = False
    tags: List[str] = []


class ThreadDetailModel(BaseModel):
    id: str
    title: str
    author: str
    created_at: float
    pinned: bool = False
    tags: List[str] = []
    messages: List[MessageModel]


class ThoughtModel(BaseModel):
    content: str
    category: str
    timestamp: float


class ToolConsiderationModel(BaseModel):
    tool_name: str
    reasoning: str
    relevance_score: float
    timestamp: float


class MonologueModel(BaseModel):
    thoughts: List[ThoughtModel]
    tool_considerations: Dict[str, ToolConsiderationModel] = {}
    max_thoughts: int
    last_interaction_time: float


class BotMonologueModel(BaseModel):
    bot_name: str
    monologue: MonologueModel
    use_monologue: bool
    debug_mode: bool 
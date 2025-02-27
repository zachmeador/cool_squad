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
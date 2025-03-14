from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
import asyncio
import json
import time
import uuid

# Updated imports for new module structure
from cool_squad.core.models import Message, Channel, Board, Thread
from cool_squad.storage.storage import Storage
from cool_squad.server.chat import ChatServer
from cool_squad.server.board import BoardServer
from cool_squad.utils.token_budget import get_token_budget_tracker, TokenBudget
from cool_squad.api.models import (
    MessageModel, ChannelModel, BoardModel, 
    ThoughtModel, ToolConsiderationModel, MonologueModel, BotMonologueModel
)
from cool_squad.api import sse

# Additional Pydantic models for API
class ThreadModel(BaseModel):
    id: str
    title: str
    author: str
    created_at: float
    pinned: bool = False
    tags: List[str] = []

class ThreadDetailModel(ThreadModel):
    messages: List[MessageModel]

class CreateThreadRequest(BaseModel):
    title: str
    first_message: MessageModel

# Token budget models
class TokenBudgetModel(BaseModel):
    daily_limit: Optional[int] = None
    monthly_limit: Optional[int] = None

class ProviderBudgetModel(BaseModel):
    provider: str
    budget: TokenBudgetModel

class ModelBudgetModel(BaseModel):
    provider: str
    model: str
    budget: TokenBudgetModel

class TokenUsageReportModel(BaseModel):
    providers: Dict[str, Any]
    daily_usage: Dict[str, Dict[str, int]]
    monthly_usage: Dict[str, Dict[str, int]]
    daily_reset: str
    monthly_reset: str
    budgets: Dict[str, Any]

# Create API router
api_router = APIRouter(tags=["api"])

# Include SSE router
api_router.include_router(sse.router, prefix="/sse", tags=["sse"])

# Dependency to get storage
def get_storage():
    return Storage()

# Dependency to get chat server
def get_chat_server(storage: Storage = Depends(get_storage)):
    return ChatServer(storage)

# Dependency to get board server
def get_board_server(storage: Storage = Depends(get_storage)):
    return BoardServer(storage)

# API endpoints
@api_router.get("/channels", response_model=List[str])
async def get_channels(chat_server: ChatServer = Depends(get_chat_server)):
    """Get list of all channels"""
    # Load all channels from storage
    storage = chat_server.storage
    channel_names = storage.list_channels()
    
    # Add any channels that are in memory but not yet in storage
    for channel_name in chat_server.channels.keys():
        if channel_name not in channel_names:
            channel_names.append(channel_name)
    
    return channel_names

@api_router.get("/channels/{channel_name}", response_model=ChannelModel)
async def get_channel(channel_name: str, chat_server: ChatServer = Depends(get_chat_server)):
    """Get channel details including messages"""
    if channel_name not in chat_server.channels:
        chat_server.channels[channel_name] = chat_server.storage.load_channel(channel_name)
    
    channel = chat_server.channels[channel_name]
    return ChannelModel(
        name=channel.name,
        messages=[MessageModel(
            content=msg.content,
            author=msg.author,
            timestamp=msg.timestamp
        ) for msg in channel.messages]
    )

@api_router.post("/channels/{channel_name}/messages", response_model=MessageModel)
async def post_message(
    channel_name: str, 
    message: MessageModel,
    chat_server: ChatServer = Depends(get_chat_server)
):
    """Post a message to a channel"""
    if channel_name not in chat_server.channels:
        chat_server.channels[channel_name] = chat_server.storage.load_channel(channel_name)
    
    # Set the channel field from the path parameter
    message.channel = channel_name
    
    msg = Message(
        content=message.content,
        author=message.author,
        timestamp=message.timestamp or time.time()
    )
    
    chat_server.channels[channel_name].add_message(msg)
    chat_server.storage.save_channel(chat_server.channels[channel_name])
    
    # Broadcast via SSE
    from cool_squad.api.sse import broadcast_chat_message
    await broadcast_chat_message(channel_name, {
        "content": msg.content,
        "author": msg.author,
        "timestamp": msg.timestamp
    })
    
    # Handle bot responses
    asyncio.create_task(chat_server.handle_bot_mentions_and_broadcast(msg, channel_name))
    
    return MessageModel(
        content=msg.content,
        author=msg.author,
        timestamp=msg.timestamp
    )

@api_router.get("/boards", response_model=List[BoardModel])
async def get_boards(board_server: BoardServer = Depends(get_board_server)):
    """Get list of all boards"""
    boards = board_server.list_boards()
    return [BoardModel(
        name=board.name, 
        description=getattr(board, 'description', "")
    ) for board in boards]

@api_router.get("/boards/{board_name}", response_model=List[ThreadModel])
async def get_board_threads(board_name: str, board_server: BoardServer = Depends(get_board_server)):
    """Get threads in a board"""
    board = board_server.get_board(board_name)
    if not board:
        raise HTTPException(status_code=404, detail=f"Board {board_name} not found")
    
    return [ThreadModel(
        id=str(i),  # Use index as ID
        title=thread.title,
        author=thread.first_message.author,
        created_at=thread.first_message.timestamp,
        pinned=thread.pinned,
        tags=list(thread.tags)
    ) for i, thread in enumerate(board.threads)]

@api_router.get("/boards/{board_name}/threads/{thread_id}", response_model=ThreadDetailModel)
async def get_thread(
    board_name: str, 
    thread_id: str,
    board_server: BoardServer = Depends(get_board_server)
):
    """Get thread details including messages"""
    board = board_server.get_board(board_name)
    if not board:
        raise HTTPException(status_code=404, detail=f"Board {board_name} not found")
    
    try:
        thread_index = int(thread_id)
        if thread_index < 0 or thread_index >= len(board.threads):
            raise ValueError()
        thread = board.threads[thread_index]
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    
    return ThreadDetailModel(
        id=thread_id,
        title=thread.title,
        author=thread.first_message.author,
        created_at=thread.first_message.timestamp,
        pinned=thread.pinned,
        tags=list(thread.tags),
        messages=[MessageModel(
            content=msg.content,
            author=msg.author,
            timestamp=msg.timestamp
        ) for msg in thread.messages]
    )

@api_router.post("/boards/{board_name}/threads", response_model=ThreadModel)
async def create_thread(
    board_name: str,
    request: CreateThreadRequest,
    board_server: BoardServer = Depends(get_board_server)
):
    """Create a new thread with initial message"""
    board = board_server.get_board(board_name)
    if not board:
        board = Board(name=board_name)
    
    msg = Message(
        content=request.first_message.content,
        author=request.first_message.author,
        timestamp=request.first_message.timestamp or time.time()
    )
    
    thread = board.create_thread(title=request.title, first_message=msg)
    board_server.save_board(board)
    
    # Broadcast via SSE
    asyncio.create_task(board_server.broadcast_board_update(board_name))
    
    # Convert to ThreadModel for response
    return ThreadModel(
        id=str(board.threads.index(thread)),  # Use index as ID
        title=thread.title,
        author=thread.first_message.author,
        created_at=thread.first_message.timestamp,
        pinned=thread.pinned,
        tags=list(thread.tags)
    )

@api_router.post("/boards/{board_name}/threads/{thread_id}/messages", response_model=MessageModel)
async def post_thread_message(
    board_name: str,
    thread_id: str,
    message: MessageModel,
    board_server: BoardServer = Depends(get_board_server)
):
    """Post a message to a thread"""
    board = board_server.get_board(board_name)
    if not board:
        raise HTTPException(status_code=404, detail=f"Board {board_name} not found")
    
    try:
        thread_index = int(thread_id)
        if thread_index < 0 or thread_index >= len(board.threads):
            raise ValueError()
        thread = board.threads[thread_index]
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    
    msg = Message(
        content=message.content,
        author=message.author,
        timestamp=message.timestamp or time.time()
    )
    
    thread.add_message(msg)
    board_server.save_board(board)
    
    # Broadcast via SSE
    asyncio.create_task(board_server.broadcast_thread_update(board_name, thread_id))
    
    return MessageModel(
        content=msg.content,
        author=msg.author,
        timestamp=msg.timestamp
    )

# Token budget endpoints
@api_router.get("/token-budget", response_model=TokenUsageReportModel)
async def get_token_usage():
    """Get token usage report and budget information"""
    token_tracker = get_token_budget_tracker()
    return token_tracker.get_usage_report()

@api_router.post("/token-budget/provider")
async def set_provider_budget(budget: ProviderBudgetModel):
    """Set budget for a provider"""
    token_tracker = get_token_budget_tracker()
    token_tracker.set_provider_budget(
        provider=budget.provider,
        daily_limit=budget.budget.daily_limit,
        monthly_limit=budget.budget.monthly_limit
    )
    return {"status": "success", "message": f"Budget set for provider {budget.provider}"}

@api_router.post("/token-budget/model")
async def set_model_budget(budget: ModelBudgetModel):
    """Set budget for a specific model"""
    token_tracker = get_token_budget_tracker()
    token_tracker.set_model_budget(
        provider=budget.provider,
        model=budget.model,
        daily_limit=budget.budget.daily_limit,
        monthly_limit=budget.budget.monthly_limit
    )
    return {"status": "success", "message": f"Budget set for model {budget.provider}/{budget.model}"}

@api_router.delete("/token-budget/provider/{provider}")
async def delete_provider_budget(provider: str):
    """Delete budget for a provider"""
    token_tracker = get_token_budget_tracker()
    if provider in token_tracker.provider_budgets:
        del token_tracker.provider_budgets[provider]
        token_tracker.save_state()
        return {"status": "success", "message": f"Budget deleted for provider {provider}"}
    raise HTTPException(status_code=404, detail=f"No budget found for provider {provider}")

@api_router.delete("/token-budget/model/{provider}/{model}")
async def delete_model_budget(provider: str, model: str):
    """Delete budget for a specific model"""
    token_tracker = get_token_budget_tracker()
    if provider in token_tracker.model_budgets and model in token_tracker.model_budgets[provider]:
        del token_tracker.model_budgets[provider][model]
        if not token_tracker.model_budgets[provider]:
            del token_tracker.model_budgets[provider]
        token_tracker.save_state()
        return {"status": "success", "message": f"Budget deleted for model {provider}/{model}"}
    raise HTTPException(status_code=404, detail=f"No budget found for model {provider}/{model}")

# Monologue API endpoints
@api_router.get("/bots", response_model=List[str])
async def get_bots(chat_server: ChatServer = Depends(get_chat_server)):
    """Get list of all bots"""
    return [bot.name for bot in chat_server.bots]

@api_router.get("/bots/{bot_name}", response_model=Dict[str, Any])
async def get_bot_info(bot_name: str, chat_server: ChatServer = Depends(get_chat_server)):
    """Get information about a specific bot"""
    bot = next((b for b in chat_server.bots if b.name == bot_name), None)
    if not bot:
        raise HTTPException(status_code=404, detail=f"Bot {bot_name} not found")
    
    return {
        "name": bot.name,
        "personality": bot.personality,
        "provider": bot.provider,
        "model": bot.model,
        "use_monologue": bot.use_monologue,
        "debug_mode": bot.debug_mode
    }

@api_router.get("/bots/{bot_name}/monologue", response_model=MonologueModel)
async def get_bot_monologue(bot_name: str, chat_server: ChatServer = Depends(get_chat_server)):
    """Get a bot's internal monologue"""
    bot = next((b for b in chat_server.bots if b.name == bot_name), None)
    if not bot:
        raise HTTPException(status_code=404, detail=f"Bot {bot_name} not found")
    
    if not bot.use_monologue:
        raise HTTPException(status_code=400, detail=f"Bot {bot_name} does not use monologue")
    
    # Convert monologue to API model
    thoughts = [
        ThoughtModel(
            content=t.content,
            category=t.category,
            timestamp=t.timestamp
        ) for t in bot.monologue.thoughts
    ]
    
    tool_considerations = {
        name: ToolConsiderationModel(
            tool_name=tc.tool_name,
            reasoning=tc.reasoning,
            relevance_score=tc.relevance_score,
            timestamp=tc.timestamp
        ) for name, tc in bot.monologue.tool_considerations.items()
    }
    
    return MonologueModel(
        thoughts=thoughts,
        tool_considerations=tool_considerations,
        max_thoughts=bot.monologue.max_thoughts,
        last_interaction_time=bot.monologue.last_interaction_time
    )

@api_router.patch("/bots/{bot_name}/monologue/settings")
async def update_bot_monologue_settings(
    bot_name: str, 
    settings: Dict[str, Any],
    chat_server: ChatServer = Depends(get_chat_server)
):
    """Update a bot's monologue settings"""
    bot = next((b for b in chat_server.bots if b.name == bot_name), None)
    if not bot:
        raise HTTPException(status_code=404, detail=f"Bot {bot_name} not found")
    
    # Update settings
    if "use_monologue" in settings:
        bot.use_monologue = settings["use_monologue"]
    
    if "debug_mode" in settings:
        bot.debug_mode = settings["debug_mode"]
    
    if "max_thoughts" in settings and bot.use_monologue:
        bot.monologue.max_thoughts = settings["max_thoughts"]
    
    return {"status": "success", "message": f"Updated monologue settings for {bot_name}"}

@api_router.post("/bots/{bot_name}/monologue/thoughts")
async def add_bot_thought(
    bot_name: str, 
    thought: Dict[str, str],
    chat_server: ChatServer = Depends(get_chat_server)
):
    """Add a thought to a bot's monologue"""
    bot = next((b for b in chat_server.bots if b.name == bot_name), None)
    if not bot:
        raise HTTPException(status_code=404, detail=f"Bot {bot_name} not found")
    
    if not bot.use_monologue:
        raise HTTPException(status_code=400, detail=f"Bot {bot_name} does not use monologue")
    
    # Add thought
    content = thought.get("content", "")
    category = thought.get("category", "general")
    
    if not content:
        raise HTTPException(status_code=400, detail="Thought content is required")
    
    bot.monologue.add_thought(content, category)
    
    return {"status": "success", "message": f"Added thought to {bot_name}'s monologue"}

@api_router.delete("/bots/{bot_name}/monologue/thoughts")
async def clear_bot_thoughts(
    bot_name: str,
    chat_server: ChatServer = Depends(get_chat_server)
):
    """Clear a bot's thoughts"""
    bot = next((b for b in chat_server.bots if b.name == bot_name), None)
    if not bot:
        raise HTTPException(status_code=404, detail=f"Bot {bot_name} not found")
    
    if not bot.use_monologue:
        raise HTTPException(status_code=400, detail=f"Bot {bot_name} does not use monologue")
    
    # Clear thoughts
    bot.monologue.thoughts = []
    
    return {"status": "success", "message": f"Cleared thoughts for {bot_name}"}

@api_router.delete("/bots/{bot_name}/monologue/tool-considerations")
async def clear_bot_tool_considerations(
    bot_name: str,
    chat_server: ChatServer = Depends(get_chat_server)
):
    """Clear a bot's tool considerations"""
    bot = next((b for b in chat_server.bots if b.name == bot_name), None)
    if not bot:
        raise HTTPException(status_code=404, detail=f"Bot {bot_name} not found")
    
    if not bot.use_monologue:
        raise HTTPException(status_code=400, detail=f"Bot {bot_name} does not use monologue")
    
    # Clear tool considerations
    bot.monologue.clear_tool_considerations()
    
    return {"status": "success", "message": f"Cleared tool considerations for {bot_name}"} 
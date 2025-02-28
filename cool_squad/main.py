import asyncio
import argparse
import sys
import os
import dotenv
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
import random

# Updated imports for new module structure
from cool_squad.server.chat import ChatServer
from cool_squad.server.board import BoardServer
from cool_squad.storage.storage import Storage
from cool_squad.core.knowledge import KnowledgeBase
from cool_squad.core.models import Message
from cool_squad.api.routes import api_router
from cool_squad.api.sse import router as sse_router, broadcast_chat_message
from cool_squad.core.autonomous import get_autonomous_thinking_manager

# Load environment variables from .env file
dotenv.load_dotenv()

# Set up API keys from environment variables
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
if not os.environ["OPENAI_API_KEY"]:
    print("Warning: OPENAI_API_KEY not set. Bots will not function properly.")

# Optional API keys
for api_key in ["ANTHROPIC_API_KEY", "COHERE_API_KEY", "REPLICATE_API_KEY"]:
    if os.getenv(api_key):
        os.environ[api_key] = os.getenv(api_key)

# Initialize servers
storage = Storage()
chat_server = ChatServer()
board_server = BoardServer(storage)

# Initialize autonomous thinking manager
autonomous_manager = get_autonomous_thinking_manager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Register bots with autonomous thinking manager
    autonomous_manager.register_bots(chat_server.bots)
    
    # Add context providers
    autonomous_manager.add_context_provider(lambda: {
        "available_channels": list(chat_server.channels.keys()) + storage.list_channels(),
        "active_channels": [name for name, conns in chat_server.connections.items() if conns]
    })
    
    # Set message callback to post to channels
    async def message_callback(bot_name, content, context):
        # Pick an active channel if available, otherwise pick any channel
        active_channels = context.get("active_channels", [])
        available_channels = context.get("available_channels", [])
        
        if active_channels:
            channel_name = random.choice(active_channels)
        elif available_channels:
            channel_name = random.choice(available_channels)
        else:
            # Default to "general" if no channels exist
            channel_name = "general"
        
        # Create and add message
        message = Message(content=content, author=bot_name)
        
        # Add to storage
        channel_data = storage.load_channel(channel_name)
        if not channel_data:
            from cool_squad.core.models import Channel
            channel_data = Channel(name=channel_name)
        
        channel_data.add_message(message)
        storage.save_channel(channel_data)
        
        # Broadcast via SSE
        await broadcast_chat_message(channel_name, {
            "content": content,
            "author": bot_name,
            "timestamp": message.timestamp
        })
    
    autonomous_manager.set_message_callback(message_callback)
    
    # Start autonomous thinking
    await autonomous_manager.start()
    
    yield
    
    # Stop autonomous thinking on shutdown
    await autonomous_manager.stop()

# Create FastAPI app
app = FastAPI(
    title="cool_squad API",
    description="API for cool_squad chat and board server",
    version="0.1.0",
    lifespan=lifespan,
)

# Add API router
app.include_router(api_router, prefix="/api")

async def update_knowledge_base():
    """Update the knowledge base."""
    kb = KnowledgeBase(storage)
    knowledge_dir = await kb.update_knowledge_base()
    print(f"Knowledge base feature coming soon. Directory: {knowledge_dir}")
    return knowledge_dir

def main():
    parser = argparse.ArgumentParser(description="cool_squad server")
    parser.add_argument("--host", type=str, default=os.getenv("HOST", "localhost"), 
                        help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")), 
                        help="Port for the FastAPI server")
    parser.add_argument("--update-knowledge", action="store_true", 
                        help="Update the knowledge base and exit")
    args = parser.parse_args()
    
    try:
        if args.update_knowledge:
            asyncio.run(update_knowledge_base())
            return
        
        # Run FastAPI server
        uvicorn.run(app, host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        sys.exit(0)

if __name__ == "__main__":
    main() 
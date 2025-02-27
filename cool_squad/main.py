import asyncio
import argparse
import sys
import os
import dotenv
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from cool_squad.server import ChatServer
from cool_squad.board import BoardServer
from cool_squad.storage import Storage
from cool_squad.knowledge import KnowledgeBase
from cool_squad.api import api_router

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code (if needed in the future)
    yield
    # Shutdown code (if needed in the future)
    pass

# Create FastAPI app
app = FastAPI(
    title="cool_squad API",
    description="API for cool_squad chat and board server",
    version="0.1.0",
    lifespan=lifespan,
)

# Add API router
app.include_router(api_router, prefix="/api")

# WebSocket endpoints
@app.websocket("/ws/chat/{channel}")
async def websocket_chat_endpoint(websocket: WebSocket, channel: str):
    await chat_server.handle_connection(websocket, channel)

@app.websocket("/ws/board/{board}")
async def websocket_board_endpoint(websocket: WebSocket, board: str):
    await board_server.handle_connection(websocket, board)

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
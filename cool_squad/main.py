import asyncio
import argparse
import sys
import os
import websockets
import dotenv
from cool_squad.server import ChatServer
from cool_squad.board import BoardServer
from cool_squad.storage import Storage
from cool_squad.knowledge import KnowledgeBase

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

async def run_chat_server(port: int):
    """Run the chat server on the specified port."""
    storage = Storage()
    server = ChatServer()
    async with websockets.serve(server.handle_message, "localhost", port):
        print(f"Chat server running on ws://localhost:{port}")
        await asyncio.Future()  # run forever

async def run_board_server(port: int):
    """Run the board server on the specified port."""
    storage = Storage()
    server = BoardServer(storage)
    async with websockets.serve(server.handle_message, "localhost", port):
        print(f"Board server running on ws://localhost:{port}")
        await asyncio.Future()  # run forever

async def update_knowledge_base():
    """Update the knowledge base."""
    storage = Storage()
    kb = KnowledgeBase(storage)
    knowledge_dir = await kb.update_knowledge_base()
    print(f"Knowledge base updated at: {knowledge_dir}")
    return knowledge_dir

async def run_all_servers(chat_port: int, board_port: int, knowledge_update_interval: int):
    """Run all servers and periodically update the knowledge base."""
    # Start the chat and board servers
    chat_task = asyncio.create_task(run_chat_server(chat_port))
    board_task = asyncio.create_task(run_board_server(board_port))
    
    # Initial knowledge base update
    knowledge_dir = await update_knowledge_base()
    
    # Periodically update the knowledge base
    while True:
        await asyncio.sleep(knowledge_update_interval)
        try:
            await update_knowledge_base()
        except Exception as e:
            print(f"Error updating knowledge base: {e}")
    
    # These tasks should never complete
    await asyncio.gather(chat_task, board_task)

def main():
    parser = argparse.ArgumentParser(description="cool_squad server")
    parser.add_argument("--chat-port", type=int, default=int(os.getenv("CHAT_PORT", "8765")), 
                        help="Port for the chat server")
    parser.add_argument("--board-port", type=int, default=int(os.getenv("BOARD_PORT", "8766")), 
                        help="Port for the board server")
    parser.add_argument("--knowledge-update", type=int, 
                        default=int(os.getenv("KNOWLEDGE_UPDATE_INTERVAL", "3600")), 
                        help="Interval in seconds for knowledge base updates")
    parser.add_argument("--chat-only", action="store_true", help="Run only the chat server")
    parser.add_argument("--board-only", action="store_true", help="Run only the board server")
    parser.add_argument("--update-knowledge", action="store_true", help="Update the knowledge base and exit")
    args = parser.parse_args()
    
    try:
        if args.update_knowledge:
            asyncio.run(update_knowledge_base())
        elif args.chat_only:
            asyncio.run(run_chat_server(args.chat_port))
        elif args.board_only:
            asyncio.run(run_board_server(args.board_port))
        else:
            asyncio.run(run_all_servers(args.chat_port, args.board_port, args.knowledge_update))
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        sys.exit(0)

if __name__ == "__main__":
    main() 
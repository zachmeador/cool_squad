#!/usr/bin/env python3
"""
Ole Scrappy Tools Demo

This script demonstrates Ole Scrappy using tools to interact with chat and message boards.
"""

import asyncio
import os
import sys
from pathlib import Path
import dotenv

# Add the parent directory to the path so we can import cool_squad
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables from .env file
dotenv.load_dotenv()

from cool_squad.core import Message, Channel, Board, Thread
from cool_squad.storage import Storage
from cool_squad.bots import create_bot_with_tools, OLE_SCRAPPY_PERSONALITY

async def main():
    """Run the Ole Scrappy tools demo."""
    print("🤖 Ole Scrappy Tools Demo")
    print("========================")
    
    # Create a storage instance
    storage = Storage()
    
    # Create a test channel if it doesn't exist
    channel_name = "junkyard"
    channel = storage.load_channel(channel_name)
    if not channel.messages:
        print(f"Creating junkyard channel with sample messages...")
        channel.add_message(Message(content="Welcome to Ole Scrappy's junkyard channel!", author="system"))
        channel.add_message(Message(content="I'm looking for some metal parts for my project.", author="user"))
        storage.save_channel(channel)
    
    # Create a test board if it doesn't exist
    board_name = "junkyard-finds"
    board = storage.load_board(board_name)
    if not board.threads:
        print(f"Creating junkyard-finds board with sample threads...")
        thread = board.create_thread(
            title="Interesting metal parts found today",
            first_message=Message(content="I found some interesting metal parts today.", author="user")
        )
        thread.add_message(Message(content="What kind of parts did you find?", author="visitor"))
        thread.tags.add("metal")
        thread.tags.add("finds")
        storage.save_board(board)
    
    # Create Ole Scrappy bot with tools
    ole_scrappy = create_bot_with_tools("ole_scrappy", OLE_SCRAPPY_PERSONALITY)
    
    # Simulate user messages and bot responses
    test_messages = [
        "@ole_scrappy can you check what's in the junkyard channel?",
        "@ole_scrappy what boards do we have?",
        "@ole_scrappy please check the threads on the junkyard-finds board",
        "@ole_scrappy read thread 1 on the junkyard-finds board",
        "@ole_scrappy post a reply to thread 1 on junkyard-finds saying 'found some rusty gears and old car parts today, might be useful for yer project'",
        "@ole_scrappy create a new thread on junkyard-finds titled 'Strange visitors' with content 'them folks in robes were back again today, lurkin around the south side of the yard'"
    ]
    
    for user_msg in test_messages:
        print("\n" + "="*70)
        print(f"👤 User: {user_msg}")
        
        # Create a message object
        message = Message(content=user_msg, author="user")
        
        # Process the message with the bot
        response = await ole_scrappy.process_message(message, "demo")
        
        print(f"🤖 ole_scrappy: {response}")
        print("="*70)
        
        # Add a small delay between messages
        await asyncio.sleep(1)
    
    print("\n✅ Demo completed!")

if __name__ == "__main__":
    asyncio.run(main()) 
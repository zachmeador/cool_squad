#!/usr/bin/env python3
"""
Bot Tools Demo

This script demonstrates how bots can use tools to interact with chat and message boards.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import cool_squad
sys.path.append(str(Path(__file__).parent.parent))

from cool_squad.core import Message
from cool_squad.storage import Storage
from cool_squad.bots import create_bot_with_tools, CURATOR_PERSONALITY

async def main():
    """Run the bot tools demo."""
    print("🤖 Bot Tools Demo")
    print("=================")
    
    # Create a storage instance
    storage = Storage()
    
    # Create a test channel if it doesn't exist
    channel_name = "demo"
    channel = storage.load_channel(channel_name)
    if not channel.messages:
        print(f"Creating demo channel with sample messages...")
        channel.add_message(Message(content="Hello, welcome to the demo channel!", author="system"))
        channel.add_message(Message(content="I'm excited to try out the bot tools!", author="user"))
        storage.save_channel(channel)
    
    # Create a test board if it doesn't exist
    board_name = "demo-board"
    board = storage.load_board(board_name)
    if not board.threads:
        print(f"Creating demo board with sample threads...")
        thread = board.create_thread(
            title="Welcome to the demo board",
            first_message=Message(content="This is a demo of the message board system.", author="system")
        )
        thread.add_message(Message(content="Let's see how bots can interact with this!", author="user"))
        thread.tags.add("demo")
        thread.tags.add("welcome")
        storage.save_board(board)
    
    # Create a bot with tools
    bot = create_bot_with_tools("curator", CURATOR_PERSONALITY)
    
    # Simulate user messages and bot responses
    test_messages = [
        "Hello @curator, can you tell me what's in this channel?",
        "@curator please check what boards are available",
        "@curator what threads are on the demo-board?",
        "@curator please read thread 1 on the demo-board",
        "@curator post a reply to thread 1 on demo-board saying 'I've analyzed this thread and it looks interesting!'",
        "@curator create a new thread on demo-board titled 'Bot-created thread' with content 'This thread was created by a bot using tools.'"
    ]
    
    for user_msg in test_messages:
        print("\n" + "="*50)
        print(f"👤 User: {user_msg}")
        
        # Create a message object
        message = Message(content=user_msg, author="user")
        
        # Process the message with the bot
        response = await bot.process_message(message, channel_name)
        
        print(f"🤖 {bot.name}: {response}")
        print("="*50)
        
        # Add a small delay between messages
        await asyncio.sleep(1)
    
    print("\n✅ Demo completed!")

if __name__ == "__main__":
    asyncio.run(main()) 
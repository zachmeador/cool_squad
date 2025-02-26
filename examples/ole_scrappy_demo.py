#!/usr/bin/env python3
"""
Ole Scrappy Demo

This script demonstrates Ole Scrappy's unique personality.
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

from cool_squad.core import Message
from cool_squad.bots import create_bot_with_tools, OLE_SCRAPPY_PERSONALITY

async def main():
    """Run the Ole Scrappy demo."""
    print("🤖 Ole Scrappy Demo")
    print("===================")
    
    # Create Ole Scrappy bot
    ole_scrappy = create_bot_with_tools("ole_scrappy", OLE_SCRAPPY_PERSONALITY)
    
    # Simulate user messages and bot responses
    test_messages = [
        "Hello Ole Scrappy, how are you today?",
        "Tell me about your scrap yard.",
        "What's your favorite book?",
        "Have you seen those strange locals recently?",
        "What's your philosophy on life?",
        "Can you help me find some metal parts?"
    ]
    
    for user_msg in test_messages:
        print("\n" + "="*50)
        print(f"👤 User: {user_msg}")
        
        # Create a message object
        message = Message(content=user_msg, author="user")
        
        # Process the message with the bot
        response = await ole_scrappy.process_message(message, "demo")
        
        print(f"🤖 ole_scrappy: {response}")
        print("="*50)
        
        # Add a small delay between messages
        await asyncio.sleep(1)
    
    print("\n✅ Demo completed!")

if __name__ == "__main__":
    asyncio.run(main()) 
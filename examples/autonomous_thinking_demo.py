#!/usr/bin/env python3
"""
Autonomous Thinking Demo

This script demonstrates how bots can have autonomous thoughts
independent of user interactions.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path so we can import cool_squad
sys.path.append(str(Path(__file__).parent.parent))

from cool_squad.core.models import Message
from cool_squad.bots.base import create_bot_with_tools, CURATOR_PERSONALITY, OLE_SCRAPPY_PERSONALITY
from cool_squad.core.autonomous import AutonomousThinkingManager
from cool_squad.core import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Override config for demo purposes
config.BOT_MIN_THINKING_INTERVAL = 5  # 5 seconds
config.BOT_MAX_THINKING_INTERVAL = 15  # 15 seconds
config.BOT_AUTONOMOUS_SPEAKING_ENABLED = True
config.BOT_AUTONOMOUS_SPEAKING_CHANCE = 1.0  # Always speak

async def main():
    """Run the autonomous thinking demo."""
    print("🤖 Autonomous Thinking Demo")
    print("===========================")
    print("This demo shows how bots can have autonomous thoughts.")
    print("Bots will think and speak every 5-15 seconds.")
    print("Press Ctrl+C to exit.")
    print()
    
    # Create bots
    curator = create_bot_with_tools(
        "curator", 
        CURATOR_PERSONALITY, 
        model="gpt-4o-mini",
        use_monologue=True
    )
    
    ole_scrappy = create_bot_with_tools(
        "ole_scrappy", 
        OLE_SCRAPPY_PERSONALITY, 
        model="gpt-4o-mini",
        use_monologue=True
    )
    
    # Create autonomous thinking manager
    manager = AutonomousThinkingManager()
    
    # Register bots
    manager.register_bot(curator)
    manager.register_bot(ole_scrappy)
    
    # Add context provider
    manager.add_context_provider(lambda: {
        "available_channels": ["general", "random"],
        "active_users": ["user1", "user2"],
        "recent_topics": ["AI ethics", "robot friends", "autonomous thinking"]
    })
    
    # Set message callback
    async def message_callback(bot_name, content, context):
        print(f"\n🤖 {bot_name}: {content}")
    
    manager.set_message_callback(message_callback)
    
    # Start autonomous thinking
    await manager.start()
    
    try:
        # Run for 2 minutes
        print("Running for 2 minutes...")
        await asyncio.sleep(120)
    except KeyboardInterrupt:
        print("\nStopping demo...")
    finally:
        # Stop autonomous thinking
        await manager.stop()
    
    print("\n✅ Demo completed!")

if __name__ == "__main__":
    asyncio.run(main()) 
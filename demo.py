#!/usr/bin/env python3
"""
cool_squad demo script

This script demonstrates the core functionality of cool_squad by:
1. Creating a simple chat channel
2. Adding messages to the channel
3. Creating a message board with threads
4. Generating a knowledge base from the discussions
"""

import asyncio
import os
import sys
from datetime import datetime

from cool_squad.core import Message, Channel, Board, Thread
from cool_squad.storage import Storage


class MockKnowledgeBase:
    """A mock knowledge base that doesn't require OpenAI API."""
    
    def __init__(self, storage):
        self.storage = storage
        self.knowledge_dir = os.path.join(self.storage.data_dir, "knowledge")
        os.makedirs(self.knowledge_dir, exist_ok=True)
    
    async def update_knowledge_base(self):
        """Create a simple index.html file."""
        index_path = os.path.join(self.knowledge_dir, "index.html")
        with open(index_path, 'w') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Knowledge Base</title>
</head>
<body>
    <h1>Knowledge Base</h1>
    <p>This is a mock knowledge base for demonstration purposes.</p>
    <p>In a real deployment, this would contain summaries and links to discussions.</p>
</body>
</html>
""")
        return self.knowledge_dir


async def demo():
    print("🤖 cool_squad demo 🤖")
    print("=====================\n")
    
    # Create a temporary data directory for the demo
    demo_dir = os.path.join(os.path.dirname(__file__), "demo_data")
    os.makedirs(demo_dir, exist_ok=True)
    
    storage = Storage(data_dir=demo_dir)
    
    # 1. Demo chat channels
    print("📢 Creating chat channels...")
    
    # Create a welcome channel
    welcome_channel = Channel(name="welcome")
    
    # Add some messages
    welcome_channel.add_message(Message(
        content="Hello and welcome to cool_squad!",
        author="sage"
    ))
    
    welcome_channel.add_message(Message(
        content="Thanks! I'm excited to be here. What can I do?",
        author="alice"
    ))
    
    welcome_channel.add_message(Message(
        content="You can chat with bots, create discussion threads, and build a knowledge base.",
        author="teacher"
    ))
    
    # Save the channel
    storage.save_channel(welcome_channel)
    print(f"✅ Created channel #{welcome_channel.name} with {len(welcome_channel.messages)} messages")
    
    # Create a coding channel
    coding_channel = Channel(name="coding")
    
    # Add some messages
    coding_channel.add_message(Message(
        content="What's the best way to learn Python?",
        author="bob"
    ))
    
    coding_channel.add_message(Message(
        content="Start with the basics and work on small projects that interest you.",
        author="teacher"
    ))
    
    coding_channel.add_message(Message(
        content="Practice is key! Try solving problems on coding challenge websites.",
        author="sage"
    ))
    
    # Save the channel
    storage.save_channel(coding_channel)
    print(f"✅ Created channel #{coding_channel.name} with {len(coding_channel.messages)} messages")
    
    # 2. Demo message boards
    print("\n📋 Creating message boards...")
    
    # Create a general board
    general_board = Board(name="general")
    
    # Create a thread
    first_message = Message(
        content="What are some good resources for learning about AI?",
        author="charlie"
    )
    
    thread = general_board.create_thread(
        title="AI Learning Resources",
        first_message=first_message
    )
    
    # Add some replies
    thread.add_message(Message(
        content="I recommend starting with the 'Fast.ai' course. It's practical and accessible.",
        author="teacher"
    ))
    
    thread.add_message(Message(
        content="'Practical Deep Learning for Coders' is also excellent for beginners.",
        author="researcher"
    ))
    
    thread.add_message(Message(
        content="Don't forget about the Stanford CS231n course - the lectures are available online.",
        author="sage"
    ))
    
    # Add tags
    thread.tags = {"learning", "ai", "resources"}
    
    # Pin the thread
    thread.pinned = True
    
    # Create another thread
    second_message = Message(
        content="What's everyone working on this week?",
        author="alice"
    )
    
    thread2 = general_board.create_thread(
        title="Weekly Projects Discussion",
        first_message=second_message
    )
    
    # Add some replies
    thread2.add_message(Message(
        content="I'm building a small game with Pygame!",
        author="bob"
    ))
    
    thread2.add_message(Message(
        content="I'm learning about natural language processing.",
        author="charlie"
    ))
    
    # Add tags
    thread2.tags = {"projects", "weekly"}
    
    # Save the board
    storage.save_board(general_board)
    print(f"✅ Created board '{general_board.name}' with {len(general_board.threads)} threads")
    
    # 3. Generate knowledge base (mock version that doesn't require OpenAI API)
    print("\n📚 Generating knowledge base...")
    kb = MockKnowledgeBase(storage)
    knowledge_dir = await kb.update_knowledge_base()
    print(f"✅ Knowledge base generated at: {knowledge_dir}")
    
    # Print summary
    print("\n🎉 Demo completed successfully!")
    print(f"Data saved to: {demo_dir}")
    print("\nYou can now:")
    print("1. Run the server: python -m cool_squad.main")
    print("2. Connect with a chat client: python -m cool_squad.client #welcome alice")
    print("3. Connect with a board client: python -m cool_squad.board_client general alice")
    print("4. Browse the knowledge base: open the HTML files in your browser")
    print("\nNote: The full knowledge base functionality requires an OpenAI API key.")


if __name__ == "__main__":
    try:
        asyncio.run(demo())
    except KeyboardInterrupt:
        print("\nDemo interrupted.")
        sys.exit(0) 
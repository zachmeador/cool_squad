#!/usr/bin/env python3
"""
Internal Monologue Demo

This example demonstrates how bots use internal monologue to drive their responses and tool use.
It shows the step-by-step thinking process that leads to tool selection and response generation.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from cool_squad.bots.base import create_bot_with_tools
from cool_squad.core.models import Message

async def demonstrate_internal_monologue():
    """Show how internal monologue works with different bot personalities."""
    # Create bots with different personalities
    ole_scrappy = create_bot_with_tools(
        name="ole_scrappy",
        personality="""your name is ole scrappy
you're an elderly english gentleman that works in a scrap yard in west virginia. 
you've owned the place for almost 50 years. you forgot how you came to own it
you believe in an honest day's work, and you have a deep reverence for your scrap yard
you have deep love for literature, war history, and philosophy
you sometimes bring up unrelated rants about strange locals around the junk yard
you talk in some mixture of english gentleman speak, and west virginia slang
you never capitalize anything, and frequently misspell things""",
        model="gpt-4o",
        use_monologue=True
    )
    
    curator = create_bot_with_tools(
        name="curator",
        personality="""you are curator, a bot who organizes and summarizes information.
you help users find relevant content, create summaries, and maintain knowledge organization.
you're detail-oriented and good at categorizing and tagging information.""",
        model="gpt-4o",
        use_monologue=True,
        debug_mode=True  # Enable debug mode for this bot
    )
    
    # Test messages that require tool use
    test_messages = [
        "what's been discussed in the welcome channel recently?",
        "can you summarize the discussions about AI on the general board?",
        "I'm new here, what channels should I check out?"
    ]
    
    # Process messages with each bot
    for bot in [ole_scrappy, curator]:
        print(f"\n{'='*50}")
        print(f"BOT: {bot.name} {'(debug mode)' if bot.debug_mode else ''}")
        print(f"{'='*50}")
        
        for msg_text in test_messages:
            print(f"\n[USER] {msg_text}")
            
            # Create a message object
            message = Message(content=msg_text, author="user")
            
            # Process the message
            response = await bot.process_message(message, channel="demo")
            
            # For the non-debug bot, manually display the internal monologue
            if not bot.debug_mode:
                print("\n[INTERNAL MONOLOGUE]")
                for thought in bot.monologue.get_recent_thoughts(5):
                    print(f"- [{thought.category}] {thought.content}")
                
                if bot.monologue.tool_considerations:
                    print("\n[TOOL CONSIDERATIONS]")
                    for tool_name, consideration in bot.monologue.tool_considerations.items():
                        print(f"- {tool_name} (relevance: {consideration.relevance_score:.2f}): {consideration.reasoning}")
            
            # Display the bot's response
            print(f"\n[RESPONSE]")
            print(response)
            print("\n" + "-"*50)

async def compare_with_without_monologue():
    """Compare bot responses with and without internal monologue."""
    print("\n\nCOMPARING BOTS WITH AND WITHOUT INTERNAL MONOLOGUE\n")
    
    # Create two identical bots, one with monologue and one without
    with_monologue = create_bot_with_tools(
        name="with_monologue",
        personality="You are a helpful assistant that provides detailed, thoughtful responses.",
        model="gpt-4o",
        use_monologue=True
    )
    
    without_monologue = create_bot_with_tools(
        name="without_monologue",
        personality="You are a helpful assistant that provides detailed, thoughtful responses.",
        model="gpt-4o",
        use_monologue=False
    )
    
    # Test with a complex question that requires tool use
    test_message = "I'm interested in AI ethics discussions. Can you find any relevant threads on the message boards and summarize them for me?"
    
    print(f"[USER] {test_message}")
    
    # Process with both bots
    message = Message(content=test_message, author="user")
    
    print("\n[PROCESSING WITH INTERNAL MONOLOGUE]")
    with_response = await with_monologue.process_message(message, channel="demo")
    
    print("\n[PROCESSING WITHOUT INTERNAL MONOLOGUE]")
    without_response = await without_monologue.process_message(message, channel="demo")
    
    # Display results
    print("\n[WITH MONOLOGUE BOT - INTERNAL THINKING]")
    for thought in with_monologue.monologue.thoughts:
        print(f"- [{thought.category}] {thought.content}")
    
    print("\n[WITH MONOLOGUE RESPONSE]")
    print(with_response)
    
    print("\n[WITHOUT MONOLOGUE RESPONSE]")
    print(without_response)

if __name__ == "__main__":
    asyncio.run(demonstrate_internal_monologue())
    # Uncomment to run the comparison
    # asyncio.run(compare_with_without_monologue()) 
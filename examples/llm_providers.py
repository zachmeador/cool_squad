#!/usr/bin/env python3
"""
LLM Providers Example

This script demonstrates how to use different LLM providers with cool_squad.
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
from cool_squad.bots import Bot
from cool_squad.custom_logging import log_api_call

async def test_openai():
    """Test OpenAI API."""
    print("\n🔍 Testing OpenAI API...")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set in .env file")
        return
    
    try:
        bot = Bot(
            name="openai-bot",
            personality="you are a helpful assistant",
            model="gpt-4o-mini"
        )
        
        response = await bot.process_message(
            Message(content="Hello, what's your name?", author="user"),
            channel="test"
        )
        
        print(f"✅ OpenAI API working: {response[:50]}...")
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")

async def test_anthropic():
    """Test Anthropic API."""
    print("\n🔍 Testing Anthropic API...")
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not set in .env file")
        return
    
    try:
        # Import anthropic here to avoid errors if not installed
        import anthropic
        
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        messages = [
            {"role": "user", "content": "Hello, what's your name?"}
        ]
        
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=messages
        )
        
        # Log the API call
        log_api_call(
            provider="anthropic",
            model="claude-3-haiku-20240307",
            messages=messages,
            response=message
        )
        
        print(f"✅ Anthropic API working: {message.content[0].text[:50]}...")
    except ImportError:
        print("❌ Anthropic SDK not installed. Run: uv pip install anthropic")
    except Exception as e:
        print(f"❌ Anthropic API error: {e}")

async def main():
    """Run the LLM providers example."""
    print("🤖 LLM Providers Example")
    print("========================")
    print("Testing different LLM providers using API keys from .env file")
    
    await test_openai()
    await test_anthropic()
    
    print("\n✅ Example completed!")

if __name__ == "__main__":
    asyncio.run(main()) 
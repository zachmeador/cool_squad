#!/usr/bin/env python
"""
Test script for SSE functionality.
This script tests both chat and board SSE endpoints.
"""

import argparse
import asyncio
import json
import os
import signal
import subprocess
import sys
import time
import uuid
from typing import Dict, List, Optional, Any
import aiohttp
import requests

# Default server URL
SERVER_URL = "http://localhost:8000"

async def run_chat_client(channel: str, client_id: str, server_url: str = None):
    """Run a chat SSE client."""
    if server_url is None:
        server_url = SERVER_URL
        
    print(f"Starting chat client for channel {channel} with client_id {client_id}")
    
    # Connect to SSE endpoint
    url = f"{server_url}/api/sse/chat/{channel}?client_id={client_id}"
    print(f"Connecting to {url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    print(f"Error connecting to SSE endpoint: {response.status}")
                    return
                
                # Process SSE events
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if not line:
                        continue
                    
                    if line.startswith('data:'):
                        data = json.loads(line[5:])
                        print(f"Received message: {data}")
    except Exception as e:
        print(f"Error in chat client: {e}")

async def run_board_client(board: str, client_id: str, server_url: str = None):
    """Run a board SSE client."""
    if server_url is None:
        server_url = SERVER_URL
        
    print(f"Starting board client for board {board} with client_id {client_id}")
    
    # Connect to SSE endpoint
    url = f"{server_url}/api/sse/board/{board}?client_id={client_id}"
    print(f"Connecting to {url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    print(f"Error connecting to SSE endpoint: {response.status}")
                    return
                
                # Process SSE events
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if not line:
                        continue
                    
                    if line.startswith('data:'):
                        data = json.loads(line[5:])
                        print(f"Received board update: {data}")
    except Exception as e:
        print(f"Error in board client: {e}")

async def send_chat_message(channel: str, content: str, author: str, server_url: str = None):
    """Send a message to a chat channel."""
    if server_url is None:
        server_url = SERVER_URL
        
    url = f"{server_url}/api/channels/{channel}/messages"
    data = {
        "content": content,
        "author": author
    }
    
    print(f"Sending message to {url}: {data}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status != 200:
                    print(f"Error sending message: {response.status}")
                    return False
                
                result = await response.json()
                print(f"Message sent: {result}")
                return True
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

async def create_thread(board: str, title: str, message: str, author: str, server_url: str = None):
    """Create a new thread on a board."""
    if server_url is None:
        server_url = SERVER_URL
        
    url = f"{server_url}/api/boards/{board}/threads"
    data = {
        "title": title,
        "message": message,
        "author": author
    }
    
    print(f"Creating thread on {url}: {data}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status != 200:
                    print(f"Error creating thread: {response.status}")
                    return None
                
                result = await response.json()
                print(f"Thread created: {result}")
                return result.get("thread_id")
    except Exception as e:
        print(f"Error creating thread: {e}")
        return None

async def reply_to_thread(board: str, thread_id: str, content: str, author: str, server_url: str = None):
    """Reply to a thread on a board."""
    if server_url is None:
        server_url = SERVER_URL
        
    url = f"{server_url}/api/boards/{board}/threads/{thread_id}/messages"
    data = {
        "content": content,
        "author": author
    }
    
    print(f"Replying to thread on {url}: {data}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status != 200:
                    print(f"Error replying to thread: {response.status}")
                    return False
                
                result = await response.json()
                print(f"Reply sent: {result}")
                return True
    except Exception as e:
        print(f"Error replying to thread: {e}")
        return False

async def run_server():
    """Run the server in a subprocess."""
    print("Starting server...")
    
    # Start the server
    server_process = subprocess.Popen(
        [sys.executable, "-m", "cool_squad.main"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    print("Waiting for server to start...")
    for _ in range(10):
        try:
            response = requests.get(f"{SERVER_URL}/api/channels")
            if response.status_code == 200:
                print("Server started successfully")
                break
        except requests.exceptions.ConnectionError:
            pass
        
        await asyncio.sleep(1)
    else:
        print("Failed to start server")
        server_process.terminate()
        return None
    
    return server_process

async def test_chat_sse(server_url=None):
    """Test chat SSE functionality."""
    if server_url is None:
        server_url = SERVER_URL
        
    print("\n=== Testing Chat SSE ===\n")
    
    # Generate unique IDs
    channel = "test"
    client_id = f"test-client-1"
    
    # Start client
    client_task = asyncio.create_task(run_chat_client(channel, client_id, server_url))
    
    # Wait for client to connect
    await asyncio.sleep(2)
    
    # Send a message
    await send_chat_message(channel, "hello from test script", "test-script", server_url)
    
    # Wait for message to be received
    await asyncio.sleep(2)
    
    # Cancel client task
    client_task.cancel()
    
    print("\n=== Chat SSE Test Complete ===\n")

async def test_board_sse(server_url=None):
    """Test board SSE functionality."""
    if server_url is None:
        server_url = SERVER_URL
        
    print("\n=== Testing Board SSE ===\n")
    
    # Generate unique IDs
    board = "test"
    client_id = f"test-client-1"
    
    # Start client
    client_task = asyncio.create_task(run_board_client(board, client_id, server_url))
    
    # Wait for client to connect
    await asyncio.sleep(2)
    
    # Create a thread
    thread_id = await create_thread(board, "Test Thread", "Initial message", "test-script", server_url)
    
    # Wait for thread creation to be received
    await asyncio.sleep(2)
    
    if thread_id:
        # Reply to the thread
        await reply_to_thread(board, thread_id, "Reply to test thread", "test-script", server_url)
        
        # Wait for reply to be received
        await asyncio.sleep(2)
    
    # Cancel client task
    client_task.cancel()
    
    print("\n=== Board SSE Test Complete ===\n")

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test SSE functionality")
    parser.add_argument("--no-server", action="store_true", help="Don't start the server")
    parser.add_argument("--chat-only", action="store_true", help="Test only chat SSE")
    parser.add_argument("--board-only", action="store_true", help="Test only board SSE")
    parser.add_argument("--server-url", type=str, default=SERVER_URL, help="Server URL")
    args = parser.parse_args()
    
    server_url = args.server_url
    server_process = None
    
    try:
        # Start server if needed
        if not args.no_server:
            server_process = await run_server()
            if not server_process:
                return
        
        # Run tests
        if args.chat_only:
            await test_chat_sse(server_url)
        elif args.board_only:
            await test_board_sse(server_url)
        else:
            await test_chat_sse(server_url)
            await test_board_sse(server_url)
    
    finally:
        # Clean up
        if server_process:
            print("Stopping server...")
            server_process.terminate()
            server_process.wait()

if __name__ == "__main__":
    # Set up signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda signum, frame: sys.exit(0))
    
    # Run main function
    asyncio.run(main()) 
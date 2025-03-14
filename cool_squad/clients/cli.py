#!/usr/bin/env python3
"""
Unified CLI tool for Cool Squad that provides access to all functionality.
"""

import os
import sys
import argparse
import json
import time
import asyncio
import websockets
from datetime import datetime
from pathlib import Path
import aiohttp
import uuid
from typing import Optional

from cool_squad.storage.storage import Storage
from cool_squad.core.config import ensure_data_dir, get_data_dir
from cool_squad.core.models import Message

# base url for api
API_BASE_URL = "http://localhost:8000/api"

def format_timestamp(timestamp):
    """Format a timestamp into a human-readable string."""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def print_channels(storage):
    """Print all channels and their messages."""
    print("\n=== CHANNELS ===")
    
    # Get all channel files
    channel_files = list(Path(storage.channels_dir).glob("*.json"))
    
    if not channel_files:
        print("No channels found.")
        return
    
    for channel_file in channel_files:
        channel_name = channel_file.stem
        channel = storage.load_channel(channel_name)
        
        print(f"\nChannel: {channel.name}")
        print("-" * (len(channel.name) + 9))
        
        if not channel.messages:
            print("  No messages")
        else:
            for i, msg in enumerate(channel.messages):
                print(f"  [{format_timestamp(msg.timestamp)}] {msg.author}: {msg.content}")


def print_channel_messages(storage, channel_name, limit=None):
    """Print the latest messages from a specific channel."""
    if not Path(storage.channels_dir, f"{channel_name}.json").exists():
        print(f"Channel '{channel_name}' not found.")
        return
    
    channel = storage.load_channel(channel_name)
    
    print(f"\nChannel: {channel.name}")
    print("-" * (len(channel.name) + 9))
    
    if not channel.messages:
        print("  No messages")
        return
    
    messages = channel.messages
    if limit and limit > 0:
        messages = messages[-limit:]
    
    for msg in messages:
        print(f"  [{format_timestamp(msg.timestamp)}] {msg.author}: {msg.content}")


def send_message(storage, channel_name, author, content):
    """Send a message to a channel."""
    if not channel_name:
        print("Error: Channel name is required.")
        return False
    
    # Create channel if it doesn't exist
    channel = storage.load_channel(channel_name)
    
    # Create and add message
    message = Message(
        content=content,
        author=author,
        timestamp=time.time()
    )
    
    channel.add_message(message)
    storage.save_channel(channel)
    
    print(f"Message sent to #{channel_name}")
    return True


def print_boards(storage):
    """Print all boards, threads, and their messages."""
    print("\n=== BOARDS ===")
    
    # Get all board files
    board_files = list(Path(storage.boards_dir).glob("*.json"))
    
    if not board_files:
        print("No boards found.")
        return
    
    for board_file in board_files:
        board_name = board_file.stem
        board = storage.load_board(board_name)
        
        print(f"\nBoard: {board.name}")
        print("-" * (len(board.name) + 7))
        
        if not board.threads:
            print("  No threads")
        else:
            for i, thread in enumerate(board.threads):
                print(f"\n  Thread {i+1}: {thread.title}")
                if thread.pinned:
                    print("  [PINNED]")
                if thread.tags:
                    print(f"  Tags: {', '.join(thread.tags)}")
                print("  Messages:")
                
                for j, msg in enumerate(thread.messages):
                    print(f"    [{format_timestamp(msg.timestamp)}] {msg.author}: {msg.content}")


class CLIClient:
    def __init__(self, username: str, board: str):
        self.username = username
        self.board = board
        self.client_id = str(uuid.uuid4())
        self.running = True
    
    async def receive_board_messages(self):
        """Receive messages from the board via SSE."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{API_BASE_URL}/board/{self.board}?client_id={self.client_id}",
                    headers={"Accept": "text/event-stream"}
                ) as response:
                    async for line in response.content:
                        if not self.running:
                            break
                        
                        line = line.decode().strip()
                        if not line:
                            continue
                        
                        if line.startswith("data: "):
                            data = json.loads(line[6:])
                            
                            if data.get("type") == "board_update":
                                print("\nBoard update:")
                                for thread in data.get("board", {}).get("threads", []):
                                    print(f"- {thread['title']} (by {thread['author']})")
                            
                            elif data.get("type") == "thread_update":
                                thread = data.get("thread", {})
                                print(f"\nThread update: {thread.get('title')}")
                                for msg in thread.get("messages", []):
                                    print(f"{msg['author']}: {msg['content']}")
        except Exception as e:
            print(f"error receiving messages: {e}")
            self.running = False
    
    async def send_board_messages(self):
        """Send messages to the board."""
        try:
            while self.running:
                command = input("\nEnter command (t=new thread, r=reply, q=quit): ").strip().lower()
                
                if command == "q":
                    self.running = False
                    break
                
                elif command == "t":
                    title = input("Thread title: ").strip()
                    content = input("First message: ").strip()
                    
                    if not title or not content:
                        print("title and message are required")
                        continue
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{API_BASE_URL}/boards/{self.board}/threads",
                            json={
                                "title": title,
                                "message": content,
                                "author": self.username
                            }
                        ) as response:
                            if response.status != 200:
                                print(f"error creating thread: {response.status}")
                                continue
                            print("thread created!")
                
                elif command == "r":
                    thread_id = input("Thread ID: ").strip()
                    content = input("Message: ").strip()
                    
                    if not thread_id or not content:
                        print("thread id and message are required")
                        continue
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{API_BASE_URL}/boards/{self.board}/threads/{thread_id}/messages",
                            json={
                                "content": content,
                                "author": self.username
                            }
                        ) as response:
                            if response.status != 200:
                                print(f"error sending message: {response.status}")
                                continue
                            print("message sent!")
                
                else:
                    print("invalid command")
        except Exception as e:
            print(f"error sending messages: {e}")
            self.running = False


def cmd_explore(args):
    """Command to explore channels and boards."""
    # Set data directory from args or use default
    data_dir = args.data_dir or get_data_dir()
    os.environ["COOL_SQUAD_DATA_DIR"] = data_dir
    
    # Ensure data directory exists
    ensure_data_dir()
    
    # Initialize storage
    storage = Storage(data_dir)
    
    # Print header with data directory info
    print(f"Cool Squad Data Explorer")
    print(f"Data directory: {data_dir}")
    
    # Handle viewing a specific channel
    if args.channel:
        print_channel_messages(storage, args.channel, args.limit)
        return
    
    # Print channels and boards based on flags
    if args.boards_only:
        print_boards(storage)
    elif args.channels_only:
        print_channels(storage)
    else:
        print_channels(storage)
        print_boards(storage)


def cmd_chat(args):
    """Command to interact with chat channels."""
    # Set data directory from args or use default
    data_dir = args.data_dir or get_data_dir()
    os.environ["COOL_SQUAD_DATA_DIR"] = data_dir
    
    # Ensure data directory exists
    ensure_data_dir()
    
    # Initialize storage
    storage = Storage(data_dir)
    
    # Print header with data directory info
    print(f"Cool Squad Chat")
    print(f"Data directory: {data_dir}")
    
    # Handle sending a message
    if args.send:
        send_message(storage, args.channel, args.author, args.send)
        # After sending, show the channel
        print_channel_messages(storage, args.channel, args.limit)
    else:
        # Just view the channel
        print_channel_messages(storage, args.channel, args.limit)


async def main():
    parser = argparse.ArgumentParser(description="CLI client for cool_squad")
    parser.add_argument("username", help="your username")
    parser.add_argument("board", help="board to join")
    args = parser.parse_args()
    
    client = CLIClient(args.username, args.board)
    
    try:
        # Register with the server
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/boards/{args.board}",
                json={"client_id": client.client_id}
            ) as response:
                if response.status != 200:
                    print(f"error registering with server: {response.status}")
                    return
        
        # Start receiving and sending messages
        await asyncio.gather(
            client.receive_board_messages(),
            client.send_board_messages()
        )
    except KeyboardInterrupt:
        print("\nshutting down...")
        client.running = False
    except Exception as e:
        print(f"error: {e}")
        client.running = False


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nshutting down...") 
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

from cool_squad.storage import Storage
from cool_squad.config import ensure_data_dir, get_data_dir
from cool_squad.core import Message


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


# Board client functionality
async def receive_board_messages(websocket):
    try:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            
            if data["type"] == "threads":
                print(f"\n=== Threads in {data['board']} ===")
                for thread in data["threads"]:
                    pinned = "📌 " if thread["pinned"] else ""
                    tags = f" [{', '.join(thread['tags'])}]" if thread["tags"] else ""
                    print(f"{pinned}#{thread['id']}: {thread['title']}{tags} ({thread['message_count']} messages)")
                print("\nCommands: /view <id>, /new <title>, /quit")
            
            elif data["type"] == "thread_detail":
                print(f"\n=== Thread: {data['title']} ===")
                if data["tags"]:
                    print(f"Tags: {', '.join(data['tags'])}")
                print(f"{'📌 Pinned' if data['pinned'] else ''}")
                print("-" * 40)
                
                for msg in data["messages"]:
                    timestamp = datetime.fromtimestamp(msg["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{timestamp}] {msg['author']}:")
                    print(f"{msg['content']}")
                    print("-" * 40)
                
                print("\nCommands: /reply <message>, /back, /pin, /tag <tag>, /quit")
            
            elif data["type"] == "new_thread":
                print(f"\nNew thread created: #{data['thread']['id']}: {data['thread']['title']}")
            
            elif data["type"] == "new_message":
                timestamp = datetime.fromtimestamp(data["message"]["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[{timestamp}] {data['message']['author']}:")
                print(f"{data['message']['content']}")
                print("-" * 40)
            
            elif data["type"] == "thread_updated":
                print(f"\nThread updated: #{data['thread']['id']}: {data['thread']['title']}")
                
    except websockets.exceptions.ConnectionClosed:
        print("\nDisconnected from server")
        sys.exit(0)


async def send_board_messages(websocket, username, board):
    current_thread = None
    
    try:
        while True:
            message = await asyncio.get_event_loop().run_in_executor(None, input)
            
            if message.lower() == "/quit":
                await websocket.close()
                return
            
            if current_thread is None:
                # Board view commands
                if message.lower().startswith("/view "):
                    try:
                        thread_id = int(message.split(" ", 1)[1])
                        current_thread = thread_id
                        await websocket.send(json.dumps({
                            "type": "get_thread",
                            "thread_id": thread_id
                        }))
                    except (ValueError, IndexError):
                        print("Invalid thread ID. Usage: /view <id>")
                
                elif message.lower().startswith("/new "):
                    try:
                        title = message.split(" ", 1)[1]
                        content = await asyncio.get_event_loop().run_in_executor(
                            None, lambda: input("Enter your message: ")
                        )
                        
                        await websocket.send(json.dumps({
                            "type": "create_thread",
                            "title": title,
                            "content": content,
                            "author": username
                        }))
                    except IndexError:
                        print("Invalid title. Usage: /new <title>")
                
                else:
                    print("Unknown command. Available commands: /view <id>, /new <title>, /quit")
            
            else:
                # Thread view commands
                if message.lower() == "/back":
                    current_thread = None
                    # Refresh thread list
                    await websocket.send(json.dumps({
                        "type": "join",
                        "board": board
                    }))
                
                elif message.lower().startswith("/reply "):
                    try:
                        content = message.split(" ", 1)[1]
                        await websocket.send(json.dumps({
                            "type": "add_message",
                            "thread_id": current_thread,
                            "content": content,
                            "author": username
                        }))
                    except IndexError:
                        print("Invalid message. Usage: /reply <message>")
                
                elif message.lower() == "/pin":
                    await websocket.send(json.dumps({
                        "type": "update_thread",
                        "thread_id": current_thread,
                        "pinned": True
                    }))
                
                elif message.lower().startswith("/tag "):
                    try:
                        tag = message.split(" ", 1)[1]
                        await websocket.send(json.dumps({
                            "type": "update_thread",
                            "thread_id": current_thread,
                            "tags": [tag]
                        }))
                    except IndexError:
                        print("Invalid tag. Usage: /tag <tag>")
                
                else:
                    print("Unknown command. Available commands: /reply <message>, /back, /pin, /tag <tag>, /quit")
                
    except (EOFError, KeyboardInterrupt):
        await websocket.close()


async def board_client(board, username):
    """Interactive board client."""
    try:
        async with websockets.connect("ws://localhost:8766") as websocket:
            # join board
            await websocket.send(json.dumps({
                "type": "join",
                "board": board
            }))
            
            print(f"Connected to board: {board}")
            print("Loading threads...")
            
            await asyncio.gather(
                receive_board_messages(websocket),
                send_board_messages(websocket, username, board)
            )
    except ConnectionRefusedError:
        print("Could not connect to server. Is it running?")
        sys.exit(1)


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


def cmd_board(args):
    """Command to interact with message boards."""
    try:
        asyncio.run(board_client(args.board, args.username))
    except KeyboardInterrupt:
        print("\nGoodbye!")


def main():
    # Create the top-level parser
    parser = argparse.ArgumentParser(description="Cool Squad CLI")
    parser.add_argument("--data-dir", help="Path to data directory (default: _data)")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Create parser for the "explore" command
    explore_parser = subparsers.add_parser("explore", help="Explore channels and boards")
    explore_parser.add_argument("--channels-only", action="store_true", help="Only show channels")
    explore_parser.add_argument("--boards-only", action="store_true", help="Only show boards")
    explore_parser.add_argument("--channel", "-c", help="Specify a channel to view")
    explore_parser.add_argument("--limit", "-l", type=int, default=10, help="Limit the number of messages to display (default: 10)")
    
    # Create parser for the "chat" command
    chat_parser = subparsers.add_parser("chat", help="Interact with chat channels")
    chat_parser.add_argument("--channel", "-c", required=True, help="Specify a channel to view or send a message to")
    chat_parser.add_argument("--limit", "-l", type=int, default=10, help="Limit the number of messages to display (default: 10)")
    chat_parser.add_argument("--send", "-s", help="Send a message to the specified channel")
    chat_parser.add_argument("--author", "-a", default="cli_user", help="Author name for sent messages (default: cli_user)")
    
    # Create parser for the "board" command
    board_parser = subparsers.add_parser("board", help="Interactive board client")
    board_parser.add_argument("board", help="Board to join (e.g. general)")
    board_parser.add_argument("username", help="Your username")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle commands
    if args.command == "explore":
        cmd_explore(args)
    elif args.command == "chat":
        cmd_chat(args)
    elif args.command == "board":
        cmd_board(args)
    else:
        # If no command is specified, show help
        parser.print_help()


if __name__ == "__main__":
    main() 
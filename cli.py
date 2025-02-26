#!/usr/bin/env python3
"""
CLI tool for Cool Squad that prints out all threads, posts, and chat messages.
"""

import os
import sys
import argparse
import json
from datetime import datetime
from pathlib import Path

from cool_squad.storage import Storage
from cool_squad.config import ensure_data_dir, get_data_dir


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


def main():
    parser = argparse.ArgumentParser(description="Cool Squad CLI tool")
    parser.add_argument("--data-dir", help="Path to data directory (default: _data)")
    parser.add_argument("--channels-only", action="store_true", help="Only show channels")
    parser.add_argument("--boards-only", action="store_true", help="Only show boards")
    
    args = parser.parse_args()
    
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
    
    # Print channels and boards based on flags
    if args.boards_only:
        print_boards(storage)
    elif args.channels_only:
        print_channels(storage)
    else:
        print_channels(storage)
        print_boards(storage)


if __name__ == "__main__":
    main() 
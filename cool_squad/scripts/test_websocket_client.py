#!/usr/bin/env python
"""
Simple script to test WebSocket connection to the cool_squad server.
"""
import asyncio
import websockets
import json
import argparse
import sys

async def listen_to_websocket(url):
    """Connect to WebSocket endpoint and print messages."""
    print(f"connecting to {url}...")
    
    try:
        async with websockets.connect(url) as websocket:
            print("connected! listening for messages...")
            
            while True:
                try:
                    message = await websocket.recv()
                    try:
                        data = json.loads(message)
                        print(f"received: {data}")
                    except json.JSONDecodeError:
                        print(f"received (raw): {message}")
                except websockets.exceptions.ConnectionClosed:
                    print("connection closed")
                    break
    
    except websockets.exceptions.WebSocketException as e:
        print(f"websocket error: {e}")
    except asyncio.CancelledError:
        print("connection cancelled")
    except Exception as e:
        print(f"unexpected error: {e}")

async def send_message(ws_url, content, author):
    """Send a message via WebSocket."""
    data = {
        "type": "message",
        "content": content,
        "author": author
    }
    
    print(f"sending message to {ws_url}: {data}")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            await websocket.send(json.dumps(data))
            print("message sent successfully")
            
            # Wait for a response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                try:
                    data = json.loads(response)
                    print(f"received response: {data}")
                except json.JSONDecodeError:
                    print(f"received response (raw): {response}")
            except asyncio.TimeoutError:
                print("no response received within timeout")
            
            return True
    
    except Exception as e:
        print(f"error sending message: {e}")
        return False

async def main():
    parser = argparse.ArgumentParser(description="Test WebSocket connection to cool_squad server")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--channel", default="test", help="Channel to connect to")
    parser.add_argument("--send", help="Send a message and exit")
    parser.add_argument("--author", default="test-user", help="Author name for sent messages")
    args = parser.parse_args()
    
    ws_url = f"ws://{args.host}:{args.port}/ws/chat/{args.channel}"
    
    if args.send:
        # Just send a message and exit
        success = await send_message(ws_url, args.send, args.author)
        sys.exit(0 if success else 1)
    
    # Listen for messages
    try:
        await listen_to_websocket(ws_url)
    except KeyboardInterrupt:
        print("\nshutting down...")

if __name__ == "__main__":
    asyncio.run(main()) 
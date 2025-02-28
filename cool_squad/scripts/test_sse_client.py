#!/usr/bin/env python
"""
Simple script to test SSE connection to the cool_squad server.
"""
import asyncio
import aiohttp
import json
import argparse
import sys

async def listen_to_sse(url):
    """Connect to SSE endpoint and print events."""
    print(f"connecting to {url}...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    print(f"error: {response.status} {response.reason}")
                    return
                
                print("connected! listening for events...")
                
                # Process the SSE stream
                buffer = ""
                async for line in response.content:
                    line = line.decode('utf-8')
                    buffer += line
                    
                    if buffer.endswith('\n\n'):
                        # Process complete event
                        event_data = None
                        for part in buffer.split('\n'):
                            if part.startswith('data: '):
                                event_data = part[6:]  # Remove 'data: ' prefix
                        
                        if event_data:
                            try:
                                data = json.loads(event_data)
                                print(f"received: {data}")
                            except json.JSONDecodeError:
                                print(f"received (raw): {event_data}")
                        
                        buffer = ""
        
        except aiohttp.ClientError as e:
            print(f"connection error: {e}")
        except asyncio.CancelledError:
            print("connection cancelled")
        except Exception as e:
            print(f"unexpected error: {e}")

async def send_message(api_url, channel, content, author):
    """Send a message to the channel."""
    url = f"{api_url}/channels/{channel}/messages"
    data = {
        "content": content,
        "author": author
    }
    
    print(f"sending message to {url}: {data}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=data) as response:
                if response.status != 200:
                    print(f"error sending message: {response.status} {response.reason}")
                    return False
                
                print("message sent successfully")
                return True
        
        except Exception as e:
            print(f"error sending message: {e}")
            return False

async def main():
    parser = argparse.ArgumentParser(description="Test SSE connection to cool_squad server")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--channel", default="test", help="Channel to connect to")
    parser.add_argument("--client-id", default="test-client", help="Client ID")
    parser.add_argument("--send", help="Send a message and exit")
    parser.add_argument("--author", default="test-user", help="Author name for sent messages")
    args = parser.parse_args()
    
    base_url = f"http://{args.host}:{args.port}"
    api_url = f"{base_url}/api"
    sse_url = f"{api_url}/sse/chat/{args.channel}?client_id={args.client_id}"
    
    if args.send:
        # Just send a message and exit
        success = await send_message(api_url, args.channel, args.send, args.author)
        sys.exit(0 if success else 1)
    
    # Listen for events
    try:
        await listen_to_sse(sse_url)
    except KeyboardInterrupt:
        print("\nshutting down...")

if __name__ == "__main__":
    asyncio.run(main()) 
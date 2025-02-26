import asyncio
import json
import websockets
import argparse
import sys
from datetime import datetime

async def receive_messages(websocket):
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

async def send_messages(websocket, username, board):
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

async def main():
    parser = argparse.ArgumentParser(description="cool_squad board client")
    parser.add_argument("board", help="board to join (e.g. general)")
    parser.add_argument("username", help="your username")
    args = parser.parse_args()
    
    try:
        async with websockets.connect("ws://localhost:8766") as websocket:
            # join board
            await websocket.send(json.dumps({
                "type": "join",
                "board": args.board
            }))
            
            print(f"Connected to board: {args.board}")
            print("Loading threads...")
            
            await asyncio.gather(
                receive_messages(websocket),
                send_messages(websocket, args.username, args.board)
            )
    except ConnectionRefusedError:
        print("Could not connect to server. Is it running?")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!") 
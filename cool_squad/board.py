import asyncio
import json
import websockets
from typing import Dict, Set
from cool_squad.core import Message, Board, Thread
from cool_squad.storage import Storage

class BoardServer:
    def __init__(self, storage: Storage = None):
        self.storage = storage or Storage()
        self.boards: Dict[str, Board] = {}
        self.connections: Dict[str, Set[websockets.WebSocketServerProtocol]] = {}
    
    async def register(self, websocket: websockets.WebSocketServerProtocol, board_name: str):
        if board_name not in self.connections:
            self.connections[board_name] = set()
        self.connections[board_name].add(websocket)

        if board_name not in self.boards:
            self.boards[board_name] = self.storage.load_board(board_name)
    
    async def unregister(self, websocket: websockets.WebSocketServerProtocol, board_name: str):
        self.connections[board_name].remove(websocket)
        if not self.connections[board_name]:
            del self.connections[board_name]
    
    async def broadcast(self, board_name: str, message: dict):
        if board_name in self.connections:
            websockets_to_remove = set()
            for websocket in self.connections[board_name]:
                try:
                    await websocket.send(json.dumps(message))
                except websockets.exceptions.ConnectionClosed:
                    websockets_to_remove.add(websocket)
            
            for websocket in websockets_to_remove:
                await self.unregister(websocket, board_name)
    
    async def handle_message(self, websocket: websockets.WebSocketServerProtocol):
        try:
            # expect initial message to be board join
            message = await websocket.recv()
            data = json.loads(message)
            
            if data["type"] != "join":
                await websocket.close(1008, "first message must be join")
                return

            board_name = data["board"]
            await self.register(websocket, board_name)
            
            # send current threads to the client
            await websocket.send(json.dumps({
                "type": "threads",
                "board": board_name,
                "threads": [
                    {
                        "id": i,
                        "title": thread.title,
                        "first_message": {
                            "content": thread.first_message.content,
                            "author": thread.first_message.author,
                            "timestamp": thread.first_message.timestamp
                        },
                        "message_count": len(thread.messages),
                        "pinned": thread.pinned,
                        "tags": list(thread.tags)
                    }
                    for i, thread in enumerate(self.boards[board_name].threads)
                ]
            }))
            
            try:
                async for message in websocket:
                    data = json.loads(message)
                    
                    if data["type"] == "create_thread":
                        msg = Message(
                            content=data["content"],
                            author=data["author"]
                        )
                        
                        thread = self.boards[board_name].create_thread(
                            title=data["title"],
                            first_message=msg
                        )
                        
                        if "tags" in data:
                            thread.tags = set(data["tags"])
                        
                        self.storage.save_board(self.boards[board_name])
                        
                        # broadcast new thread
                        thread_id = len(self.boards[board_name].threads) - 1
                        await self.broadcast(board_name, {
                            "type": "new_thread",
                            "board": board_name,
                            "thread": {
                                "id": thread_id,
                                "title": thread.title,
                                "first_message": {
                                    "content": thread.first_message.content,
                                    "author": thread.first_message.author,
                                    "timestamp": thread.first_message.timestamp
                                },
                                "message_count": len(thread.messages),
                                "pinned": thread.pinned,
                                "tags": list(thread.tags)
                            }
                        })
                    
                    elif data["type"] == "get_thread":
                        thread_id = data["thread_id"]
                        if 0 <= thread_id < len(self.boards[board_name].threads):
                            thread = self.boards[board_name].threads[thread_id]
                            await websocket.send(json.dumps({
                                "type": "thread_detail",
                                "board": board_name,
                                "thread_id": thread_id,
                                "title": thread.title,
                                "pinned": thread.pinned,
                                "tags": list(thread.tags),
                                "messages": [
                                    {
                                        "content": msg.content,
                                        "author": msg.author,
                                        "timestamp": msg.timestamp
                                    }
                                    for msg in thread.messages
                                ]
                            }))
                    
                    elif data["type"] == "add_message":
                        thread_id = data["thread_id"]
                        if 0 <= thread_id < len(self.boards[board_name].threads):
                            thread = self.boards[board_name].threads[thread_id]
                            
                            msg = Message(
                                content=data["content"],
                                author=data["author"]
                            )
                            
                            thread.add_message(msg)
                            self.storage.save_board(self.boards[board_name])
                            
                            # broadcast new message
                            await self.broadcast(board_name, {
                                "type": "new_message",
                                "board": board_name,
                                "thread_id": thread_id,
                                "message": {
                                    "content": msg.content,
                                    "author": msg.author,
                                    "timestamp": msg.timestamp
                                }
                            })
                    
                    elif data["type"] == "update_thread":
                        thread_id = data["thread_id"]
                        if 0 <= thread_id < len(self.boards[board_name].threads):
                            thread = self.boards[board_name].threads[thread_id]
                            
                            if "title" in data:
                                thread.title = data["title"]
                            
                            if "pinned" in data:
                                thread.pinned = data["pinned"]
                            
                            if "tags" in data:
                                thread.tags = set(data["tags"])
                            
                            self.storage.save_board(self.boards[board_name])
                            
                            # broadcast thread update
                            await self.broadcast(board_name, {
                                "type": "thread_updated",
                                "board": board_name,
                                "thread": {
                                    "id": thread_id,
                                    "title": thread.title,
                                    "first_message": {
                                        "content": thread.first_message.content,
                                        "author": thread.first_message.author,
                                        "timestamp": thread.first_message.timestamp
                                    },
                                    "message_count": len(thread.messages),
                                    "pinned": thread.pinned,
                                    "tags": list(thread.tags)
                                }
                            })
                    
            except websockets.exceptions.ConnectionClosed:
                pass
            
        finally:
            await self.unregister(websocket, board_name)

async def main():
    storage = Storage()
    server = BoardServer(storage)
    async with websockets.serve(server.handle_message, "localhost", 8766):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main()) 
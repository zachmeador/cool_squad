import asyncio
import json
import websockets
from typing import Dict, Set
from cool_squad.core import Message, Channel
from cool_squad.storage import Storage
from cool_squad.bots import create_default_bots, Bot

class ChatServer:
    def __init__(self):
        self.storage = Storage()
        self.channels: Dict[str, Channel] = {}
        self.connections: Dict[str, Set[websockets.WebSocketServerProtocol]] = {}
        
        # create bots with tools
        bots = create_default_bots()
        self.bots: Dict[str, Bot] = {bot.name: bot for bot in bots}

    async def register(self, websocket: websockets.WebSocketServerProtocol, channel_name: str):
        if channel_name not in self.connections:
            self.connections[channel_name] = set()
        self.connections[channel_name].add(websocket)

        if channel_name not in self.channels:
            self.channels[channel_name] = self.storage.load_channel(channel_name)

    async def unregister(self, websocket: websockets.WebSocketServerProtocol, channel_name: str):
        self.connections[channel_name].remove(websocket)
        if not self.connections[channel_name]:
            del self.connections[channel_name]

    async def broadcast(self, channel_name: str, message: dict):
        if channel_name in self.connections:
            websockets_to_remove = set()
            for websocket in self.connections[channel_name]:
                try:
                    await websocket.send(json.dumps(message))
                except websockets.exceptions.ConnectionClosed:
                    websockets_to_remove.add(websocket)
            
            for websocket in websockets_to_remove:
                await self.unregister(websocket, channel_name)

    async def handle_bot_mentions(self, message: Message, channel_name: str):
        content = message.content.lower()
        responses = []
        
        for bot_name, bot in self.bots.items():
            if f"@{bot_name}" in content:
                response = await bot.process_message(message, channel_name)
                if response:
                    responses.append(Message(
                        content=response,
                        author=bot_name
                    ))
        
        return responses

    async def handle_message(self, websocket: websockets.WebSocketServerProtocol):
        try:
            # expect initial message to be channel join
            message = await websocket.recv()
            data = json.loads(message)
            
            if data["type"] != "join":
                await websocket.close(1008, "first message must be join")
                return

            channel_name = data["channel"]
            await self.register(websocket, channel_name)
            
            try:
                async for message in websocket:
                    data = json.loads(message)
                    
                    if data["type"] == "message":
                        msg = Message(
                            content=data["content"],
                            author=data["author"]
                        )
                        
                        self.channels[channel_name].add_message(msg)
                        self.storage.save_channel(self.channels[channel_name])
                        
                        # broadcast user message
                        await self.broadcast(channel_name, {
                            "type": "message",
                            "channel": channel_name,
                            "content": msg.content,
                            "author": msg.author,
                            "timestamp": msg.timestamp
                        })
                        
                        # handle bot responses
                        bot_responses = await self.handle_bot_mentions(msg, channel_name)
                        for response in bot_responses:
                            self.channels[channel_name].add_message(response)
                            self.storage.save_channel(self.channels[channel_name])
                            
                            await self.broadcast(channel_name, {
                                "type": "message",
                                "channel": channel_name,
                                "content": response.content,
                                "author": response.author,
                                "timestamp": response.timestamp
                            })
                    
            except websockets.exceptions.ConnectionClosed:
                pass
            
        finally:
            await self.unregister(websocket, channel_name)

async def main():
    server = ChatServer()
    async with websockets.serve(server.handle_message, "localhost", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main()) 
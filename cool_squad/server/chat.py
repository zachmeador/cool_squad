import asyncio
import json
from typing import Dict, Set, List
from cool_squad.core.models import Message, Channel
from cool_squad.storage.storage import Storage
from cool_squad.bots.base import create_default_bots, Bot

class ChatServer:
    def __init__(self, storage: Storage = None):
        self.storage = storage or Storage()
        self.channels: Dict[str, Channel] = {}
        self.connections: Dict[str, Set] = {}
        self.bots: List[Bot] = create_default_bots()
    
    async def register(self, websocket, channel_name: str):
        """Register a websocket connection for a channel."""
        if channel_name not in self.connections:
            self.connections[channel_name] = set()
        self.connections[channel_name].add(websocket)
        
        if channel_name not in self.channels:
            self.channels[channel_name] = self.storage.load_channel(channel_name)
    
    async def unregister(self, websocket, channel_name: str):
        """Unregister a websocket connection for a channel."""
        if channel_name in self.connections:
            self.connections[channel_name].discard(websocket)
    
    async def broadcast(self, channel_name: str, message: dict):
        """Broadcast a message to all connected clients for a channel."""
        if channel_name in self.connections:
            for connection in self.connections[channel_name].copy():
                try:
                    await connection.send_json(message)
                except Exception:
                    # Connection might be closed or invalid
                    self.connections[channel_name].discard(connection)
    
    async def handle_bot_mentions(self, message: Message, channel_name: str) -> List[Message]:
        """Check for bot mentions and generate responses."""
        responses = []
        for bot in self.bots:
            # Check if the bot's name is mentioned in the message
            if f"@{bot.name}" in message.content:
                response_content = await bot.process_message(message, channel_name)
                if response_content:
                    bot_response = Message(
                        content=response_content,
                        author=bot.name
                    )
                    responses.append(bot_response)
        return responses
    
    async def handle_bot_mentions_and_broadcast(self, message: Message, channel_name: str):
        """Handle bot mentions and broadcast responses."""
        bot_responses = await self.handle_bot_mentions(message, channel_name)
        for response in bot_responses:
            self.channels[channel_name].add_message(response)
            self.storage.save_channel(self.channels[channel_name])
            
            # Broadcast via SSE
            from cool_squad.api.sse import broadcast_chat_message
            await broadcast_chat_message(channel_name, {
                "content": response.content,
                "author": response.author,
                "timestamp": response.timestamp
            })

    async def handle_connection(self, websocket, channel_name: str):
        """Handle a FastAPI WebSocket connection"""
        # Accept the connection
        await websocket.accept()
        
        # Register the connection
        if channel_name not in self.connections:
            self.connections[channel_name] = set()
        self.connections[channel_name].add(websocket)

        if channel_name not in self.channels:
            self.channels[channel_name] = self.storage.load_channel(channel_name)
        
        try:
            # Send channel history
            channel = self.channels[channel_name]
            for msg in channel.messages[-50:]:  # Send last 50 messages
                await websocket.send_json({
                    "type": "message",
                    "channel": channel_name,
                    "content": msg.content,
                    "author": msg.author,
                    "timestamp": msg.timestamp
                })
            
            # Handle incoming messages
            while True:
                data = await websocket.receive_json()
                
                if data["type"] == "message":
                    msg = Message(
                        content=data["content"],
                        author=data["author"]
                    )
                    
                    self.channels[channel_name].add_message(msg)
                    self.storage.save_channel(self.channels[channel_name])
                    
                    # Broadcast to all clients
                    await self.broadcast(channel_name, {
                        "type": "message",
                        "channel": channel_name,
                        "content": msg.content,
                        "author": msg.author,
                        "timestamp": msg.timestamp
                    })
                    
                    # Handle bot responses
                    asyncio.create_task(self.handle_bot_mentions_and_broadcast(msg, channel_name))
        except Exception:
            # Handle disconnection
            pass
        finally:
            # Unregister the connection
            if channel_name in self.connections:
                self.connections[channel_name].discard(websocket) 
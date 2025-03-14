import asyncio
from typing import Dict, List
from cool_squad.core.models import Message, Channel
from cool_squad.storage.storage import Storage
from cool_squad.bots.base import create_default_bots, Bot
from cool_squad.api.sse import broadcast_chat_message

class ChatServer:
    def __init__(self, storage: Storage = None):
        self.storage = storage or Storage()
        self.channels: Dict[str, Channel] = {}
        self.bots: List[Bot] = create_default_bots()
        
        # load existing channels from storage
        for channel_name in self.storage.list_channels():
            self.channels[channel_name] = self.storage.load_channel(channel_name)
    
    def get_or_create_channel(self, channel_name: str) -> Channel:
        """Get or create a channel."""
        if channel_name not in self.channels:
            self.channels[channel_name] = self.storage.load_channel(channel_name)
        return self.channels[channel_name]
    
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
            channel = self.get_or_create_channel(channel_name)
            channel.add_message(response)
            self.storage.save_channel(channel)
            
            # Broadcast via SSE
            await broadcast_chat_message(channel_name, {
                "content": response.content,
                "author": response.author,
                "timestamp": response.timestamp
            })
    
    async def handle_message(self, channel_name: str, content: str, author: str):
        """Handle a new message in a channel."""
        channel = self.get_or_create_channel(channel_name)
        
        # Create and save the message
        message = Message(content=content, author=author)
        channel.add_message(message)
        self.storage.save_channel(channel)
        
        # Broadcast via SSE
        await broadcast_chat_message(channel_name, {
            "content": message.content,
            "author": message.author,
            "timestamp": message.timestamp
        })
        
        # Handle bot responses
        asyncio.create_task(self.handle_bot_mentions_and_broadcast(message, channel_name)) 
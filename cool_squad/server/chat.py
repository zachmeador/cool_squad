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
        
        # ensure everyone channel exists and all bots are in it
        everyone_channel = self.get_or_create_channel("everyone")
        for bot in self.bots:
            everyone_channel.add_bot(bot.name)
        self.storage.save_channel(everyone_channel)
    
    def get_or_create_channel(self, channel_name: str) -> Channel:
        """Get or create a channel."""
        if channel_name not in self.channels:
            self.channels[channel_name] = self.storage.load_channel(channel_name)
        return self.channels[channel_name]
    
    async def process_bot_response(self, bot: Bot, message: Message, channel_name: str):
        """process a single bot's response and broadcast it immediately."""
        channel = self.get_or_create_channel(channel_name)
        
        # only process if bot is in the channel or being invited
        if not channel.has_bot(bot.name) and not ("join" in message.content.lower() and f"@{bot.name}" in message.content):
            return
        
        # collect channel data for all channels the bot is in
        channels_data = []
        for ch_name, ch in self.channels.items():
            if ch.has_bot(bot.name):
                channels_data.append((ch_name, ch.messages))
        
        # process the message with channel context
        response_content = await bot.process_message(
            message=message, 
            channel=channel_name,
            channels_data=channels_data
        )
        
        if response_content:
            bot_response = Message(
                content=response_content,
                author=bot.name
            )
            
            # save and broadcast the response immediately
            channel.add_message(bot_response)
            self.storage.save_channel(channel)
            
            # broadcast via sse
            await broadcast_chat_message(channel_name, {
                "content": bot_response.content,
                "author": bot_response.author,
                "timestamp": bot_response.timestamp
            })
    
    async def handle_bot_mentions(self, message: Message, channel_name: str):
        """check for bot mentions and generate responses."""
        channel = self.get_or_create_channel(channel_name)
        tasks = []
        
        # handle @all mention
        if "@all" in message.content:
            for bot in self.bots:
                if channel.has_bot(bot.name):
                    # create a task for each bot to process in parallel
                    task = asyncio.create_task(self.process_bot_response(bot, message, channel_name))
                    tasks.append(task)
            
            # wait for all tasks to complete
            if tasks:
                await asyncio.gather(*tasks)
            return
        
        # handle individual bot mentions
        for bot in self.bots:
            # check if the bot's name is mentioned in the message
            if f"@{bot.name}" in message.content:
                # create a task for this bot
                task = asyncio.create_task(self.process_bot_response(bot, message, channel_name))
                tasks.append(task)
        
        # wait for all tasks to complete
        if tasks:
            await asyncio.gather(*tasks)
    
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
        
        # Handle bot responses - don't wait for completion
        asyncio.create_task(self.handle_bot_mentions(message, channel_name)) 
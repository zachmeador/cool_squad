from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Set

@dataclass
class Message:
    content: str
    author: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())

@dataclass
class Channel:
    name: str
    messages: List[Message] = field(default_factory=list)
    bot_members: Set[str] = field(default_factory=set)

    def add_message(self, message: Message):
        self.messages.append(message)
    
    def add_bot(self, bot_name: str):
        self.bot_members.add(bot_name)
    
    def remove_bot(self, bot_name: str):
        self.bot_members.discard(bot_name)
    
    def has_bot(self, bot_name: str) -> bool:
        return bot_name in self.bot_members

@dataclass
class Thread:
    title: str
    first_message: Message
    messages: List[Message] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    pinned: bool = False

    def __post_init__(self):
        if not self.messages:
            self.messages = [self.first_message]

    def add_message(self, message: Message):
        self.messages.append(message)

@dataclass
class Board:
    name: str
    threads: List[Thread] = field(default_factory=list)

    def create_thread(self, title: str, first_message: Message) -> Thread:
        thread = Thread(title=title, first_message=first_message)
        self.threads.append(thread)
        return thread 
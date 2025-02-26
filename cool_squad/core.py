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

    def add_message(self, message: Message):
        self.messages.append(message)

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
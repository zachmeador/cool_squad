import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import openai
from cool_squad.core import Message, Channel, Thread, Board
from cool_squad.storage import Storage

class KnowledgeBase:
    def __init__(self, storage: Storage = None):
        self.storage = storage or Storage()
        self.knowledge_dir = os.path.join(self.storage.data_dir, "knowledge")
        Path(self.knowledge_dir).mkdir(parents=True, exist_ok=True)
    
    def _page_path(self, title: str) -> str:
        """Get the file path for a knowledge page."""
        safe_title = "".join(c if c.isalnum() else "_" for c in title.lower())
        return os.path.join(self.knowledge_dir, f"{safe_title}.html")
    
    def _index_path(self) -> str:
        """Get the file path for the knowledge index."""
        return os.path.join(self.knowledge_dir, "index.html")
    
    async def summarize_thread(self, thread: Thread) -> str:
        """Generate a summary of a thread using an LLM."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant that summarizes discussions. Create a concise summary of the following conversation, highlighting the key points and conclusions."},
            {"role": "user", "content": "\n\n".join([f"{msg.author}: {msg.content}" for msg in thread.messages])}
        ]
        
        response = await openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    async def create_page_from_thread(self, thread: Thread) -> str:
        """Create a knowledge page from a thread."""
        summary = await self.summarize_thread(thread)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{thread.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .message {{ margin-bottom: 15px; }}
        .author {{ font-weight: bold; }}
        .timestamp {{ color: #666; font-size: 0.8em; }}
        .tags {{ margin-top: 30px; }}
        .tag {{ display: inline-block; background-color: #eee; padding: 3px 8px; border-radius: 3px; margin-right: 5px; }}
    </style>
</head>
<body>
    <h1>{thread.title}</h1>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>{summary}</p>
    </div>
    
    <h2>Full Discussion</h2>
    
    <div class="messages">
"""
        
        for msg in thread.messages:
            timestamp = datetime.fromtimestamp(msg.timestamp).strftime("%Y-%m-%d %H:%M:%S")
            html += f"""
        <div class="message">
            <div class="author">{msg.author}</div>
            <div class="timestamp">{timestamp}</div>
            <div class="content">{msg.content}</div>
        </div>
"""
        
        html += """
    </div>
"""
        
        if thread.tags:
            html += """
    <div class="tags">
        <h3>Tags</h3>
"""
            for tag in thread.tags:
                html += f'        <span class="tag">{tag}</span>\n'
            
            html += """
    </div>
"""
        
        html += """
    <p><a href="index.html">Back to Index</a></p>
</body>
</html>
"""
        
        page_path = self._page_path(thread.title)
        with open(page_path, 'w') as f:
            f.write(html)
        
        return page_path
    
    async def update_index(self):
        """Update the knowledge base index page."""
        # Get all boards
        boards_dir = self.storage.boards_dir
        board_files = [f for f in os.listdir(boards_dir) if f.endswith('.json')]
        
        # Load all threads from all boards
        all_threads = []
        for board_file in board_files:
            board_name = board_file[:-5]  # Remove .json extension
            board = self.storage.load_board(board_name)
            for thread in board.threads:
                all_threads.append((board_name, thread))
        
        # Sort threads by timestamp (newest first)
        all_threads.sort(key=lambda x: x[1].messages[-1].timestamp if x[1].messages else 0, reverse=True)
        
        # Generate HTML
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Knowledge Base</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1, h2 { color: #333; }
        .thread { margin-bottom: 15px; padding: 10px; border: 1px solid #eee; border-radius: 5px; }
        .thread:hover { background-color: #f9f9f9; }
        .thread-title { font-weight: bold; }
        .thread-board { color: #666; font-size: 0.9em; }
        .thread-tags { margin-top: 5px; }
        .tag { display: inline-block; background-color: #eee; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 0.8em; }
        .pinned { background-color: #fff8e1; }
    </style>
</head>
<body>
    <h1>Knowledge Base</h1>
    
    <h2>All Discussions</h2>
"""
        
        # Add pinned threads first
        pinned_threads = [t for t in all_threads if t[1].pinned]
        for board_name, thread in pinned_threads:
            safe_title = "".join(c if c.isalnum() else "_" for c in thread.title.lower())
            html += f"""
    <div class="thread pinned">
        <div class="thread-title">📌 <a href="{safe_title}.html">{thread.title}</a></div>
        <div class="thread-board">Board: {board_name}</div>
"""
            
            if thread.tags:
                html += """        <div class="thread-tags">\n"""
                for tag in thread.tags:
                    html += f'            <span class="tag">{tag}</span>\n'
                html += """        </div>\n"""
            
            html += """    </div>\n"""
        
        # Add other threads
        other_threads = [t for t in all_threads if not t[1].pinned]
        for board_name, thread in other_threads:
            safe_title = "".join(c if c.isalnum() else "_" for c in thread.title.lower())
            html += f"""
    <div class="thread">
        <div class="thread-title"><a href="{safe_title}.html">{thread.title}</a></div>
        <div class="thread-board">Board: {board_name}</div>
"""
            
            if thread.tags:
                html += """        <div class="thread-tags">\n"""
                for tag in thread.tags:
                    html += f'            <span class="tag">{tag}</span>\n'
                html += """        </div>\n"""
            
            html += """    </div>\n"""
        
        html += """
</body>
</html>
"""
        
        with open(self._index_path(), 'w') as f:
            f.write(html)
    
    async def update_knowledge_base(self):
        """Update the entire knowledge base."""
        # Get all boards
        boards_dir = self.storage.boards_dir
        board_files = [f for f in os.listdir(boards_dir) if f.endswith('.json')]
        
        # Process all threads from all boards
        for board_file in board_files:
            board_name = board_file[:-5]  # Remove .json extension
            board = self.storage.load_board(board_name)
            
            for thread in board.threads:
                await self.create_page_from_thread(thread)
        
        # Update the index
        await self.update_index()
        
        return self.knowledge_dir

async def main():
    storage = Storage()
    kb = KnowledgeBase(storage)
    knowledge_dir = await kb.update_knowledge_base()
    print(f"Knowledge base updated at: {knowledge_dir}")

if __name__ == "__main__":
    asyncio.run(main()) 
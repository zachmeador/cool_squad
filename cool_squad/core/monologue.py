from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

@dataclass
class Thought:
    """A single thought in the bot's internal monologue."""
    content: str
    category: str
    timestamp: float = field(default_factory=lambda: time.time())
    
    def __str__(self) -> str:
        return f"[{self.category}] {self.content}"

@dataclass
class ToolConsideration:
    """Reasoning about a specific tool."""
    tool_name: str
    reasoning: str
    relevance_score: float
    timestamp: float = field(default_factory=lambda: time.time())
    
    def __str__(self) -> str:
        return f"{self.tool_name} (relevance: {self.relevance_score:.2f}): {self.reasoning}"

@dataclass
class InternalMonologue:
    """Represents a bot's internal thought process."""
    thoughts: List[Thought] = field(default_factory=list)
    tool_considerations: Dict[str, ToolConsideration] = field(default_factory=dict)
    max_thoughts: int = 50
    debug_mode: bool = False
    
    def add_thought(self, content: str, category: str = "general") -> None:
        """Add a thought to the internal monologue."""
        thought = Thought(content=content, category=category)
        self.thoughts.append(thought)
        
        # Trim if exceeding max thoughts
        if len(self.thoughts) > self.max_thoughts:
            self.thoughts = self.thoughts[-self.max_thoughts:]
    
    def consider_tool(self, tool_name: str, reasoning: str, relevance_score: float = 0.5) -> None:
        """Record reasoning about a specific tool."""
        self.tool_considerations[tool_name] = ToolConsideration(
            tool_name=tool_name,
            reasoning=reasoning,
            relevance_score=relevance_score
        )
    
    def get_recent_thoughts(self, limit: int = 10, category: Optional[str] = None) -> List[Thought]:
        """Get the most recent thoughts, optionally filtered by category."""
        if category:
            filtered = [t for t in self.thoughts if t.category == category]
            return filtered[-limit:]
        return self.thoughts[-limit:]
    
    def get_relevant_tools(self, min_relevance: float = 0.3) -> List[ToolConsideration]:
        """Get tools that meet the minimum relevance threshold."""
        return [tc for tc in self.tool_considerations.values() 
                if tc.relevance_score >= min_relevance]
    
    def clear_tool_considerations(self) -> None:
        """Clear all tool considerations."""
        self.tool_considerations = {}
    
    def summarize(self, limit: int = 5) -> str:
        """Create a summary of the current thinking process."""
        recent = self.get_recent_thoughts(limit)
        return "\n".join([f"- {t}" for t in recent])
    
    def format_for_prompt(self, limit: int = 10) -> str:
        """Format the monologue for inclusion in a prompt."""
        thoughts = self.get_recent_thoughts(limit)
        return "\n".join([f"Thought: {t.content}" for t in thoughts])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "thoughts": [{"content": t.content, "category": t.category, "timestamp": t.timestamp} 
                         for t in self.thoughts],
            "tool_considerations": {name: {"reasoning": tc.reasoning, "relevance_score": tc.relevance_score, "timestamp": tc.timestamp} 
                                   for name, tc in self.tool_considerations.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InternalMonologue':
        """Create from dictionary."""
        monologue = cls()
        
        for t in data.get("thoughts", []):
            thought = Thought(
                content=t["content"],
                category=t["category"],
                timestamp=t.get("timestamp", time.time())
            )
            monologue.thoughts.append(thought)
            
        for name, tc in data.get("tool_considerations", {}).items():
            monologue.tool_considerations[name] = ToolConsideration(
                tool_name=name,
                reasoning=tc["reasoning"],
                relevance_score=tc["relevance_score"],
                timestamp=tc.get("timestamp", time.time())
            )
            
        return monologue 
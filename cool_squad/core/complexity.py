"""
Message complexity analysis and token management.

This module handles:
1. Analyzing message complexity
2. Determining appropriate token limits
3. Managing bot response characteristics
"""

from dataclasses import dataclass
from enum import Enum
import json
import random
from typing import Dict, Any

class Complexity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class BotCharacteristics:
    verbosity: float  # 0.1-1.0: how wordy the bot is
    thoughtfulness: float  # 0.1-1.0: how deep the bot's analysis goes
    
    def __post_init__(self):
        # validate and clamp values
        self.verbosity = max(0.1, min(1.0, self.verbosity))
        self.thoughtfulness = max(0.1, min(1.0, self.thoughtfulness))

@dataclass
class ComplexityAnalysis:
    complexity: Complexity
    requires_tools: bool
    context_tags: list[str]
    base_tokens: int
    
    @property
    def token_limit(self) -> int:
        return self.base_tokens

class ComplexityManager:
    # base token limits for each complexity level
    BASE_TOKENS = {
        Complexity.LOW: 100,
        Complexity.MEDIUM: 300,
        Complexity.HIGH: 800
    }
    
    def __init__(self):
        self.client = None  # will be set to AsyncOpenAI client
    
    async def analyze_message(self, message: str) -> ComplexityAnalysis:
        """analyze a message to determine its complexity and requirements"""
        
        # use llm to analyze message complexity
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": """analyze the complexity of user messages in a chat.
                return a json object with these fields:
                - complexity: "low", "medium", or "high"
                - requires_tools: boolean
                - context_tags: list of relevant context tags
                
                guidelines:
                - low: greetings, simple statements, basic questions
                - medium: multi-part questions, requests for explanation
                - high: complex queries, requests for analysis, multi-step tasks"""},
                {"role": "user", "content": message}
            ],
            response_format={ "type": "json_object" },
            max_tokens=100  # keep analysis concise
        )
        
        result = response.choices[0].message.content
        analysis = json.loads(result)  # parse json response
        
        return ComplexityAnalysis(
            complexity=Complexity(analysis["complexity"]),
            requires_tools=analysis["requires_tools"],
            context_tags=analysis["context_tags"],
            base_tokens=self.BASE_TOKENS[Complexity(analysis["complexity"])]
        )
    
    def get_token_limit(self, analysis: ComplexityAnalysis, characteristics: BotCharacteristics) -> int:
        """calculate token limit based on message complexity and bot characteristics"""
        
        base = analysis.base_tokens
        
        if analysis.complexity == Complexity.LOW:
            # simple scaling by verbosity for low complexity
            return int(base * characteristics.verbosity)
        else:
            # scale by both verbosity and thoughtfulness for medium/high
            return int(base * characteristics.verbosity * (1 + characteristics.thoughtfulness))
    
    def get_thought_interval(self, analysis: ComplexityAnalysis) -> float:
        """calculate the interval between thoughts based on complexity"""
        
        # base interval is 5 minutes (300 seconds)
        base_interval = 300
        
        # modify based on complexity
        complexity_multiplier = {
            Complexity.LOW: 1.0,  # 5 mins
            Complexity.MEDIUM: 0.6,  # 3 mins
            Complexity.HIGH: 0.3  # 1.5 mins
        }[analysis.complexity]
        
        # add random scatter (-30 to +30 seconds)
        scatter = random.uniform(-30, 30)
        
        return (base_interval * complexity_multiplier) + scatter 
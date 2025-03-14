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
from cool_squad.llm.providers import create_provider

class Complexity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class ComplexityAnalysis:
    complexity: Complexity
    requires_tools: bool
    context_tags: list
    base_tokens: int

@dataclass
class BotCharacteristics:
    verbosity: float  # 0.0 to 1.0, higher means more verbose
    thoughtfulness: float  # 0.0 to 1.0, higher means more thoughtful

class ComplexityManager:
    # base token limits for each complexity level
    BASE_TOKENS = {
        Complexity.LOW: 100,
        Complexity.MEDIUM: 300,
        Complexity.HIGH: 800
    }
    
    def __init__(self):
        """initialize with openai provider for analysis"""
        self.llm = create_provider(
            provider="openai",
            model="gpt-4o-mini-2024-07-18",
            temperature=0.2  # low temperature for consistent analysis
        )
    
    async def analyze_message(self, message: str) -> ComplexityAnalysis:
        """analyze a message to determine its complexity and requirements"""
        
        # use llm to analyze message complexity
        response = await self.llm.send_message(
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
            max_tokens=100  # keep analysis concise
        )
        
        result = response.content  # parse json response
        analysis = json.loads(result)
        
        return ComplexityAnalysis(
            complexity=Complexity(analysis["complexity"]),
            requires_tools=analysis["requires_tools"],
            context_tags=analysis["context_tags"],
            base_tokens=self.BASE_TOKENS[Complexity(analysis["complexity"])]
        )
    
    def get_token_limit(self, analysis: ComplexityAnalysis, characteristics: BotCharacteristics) -> int:
        """calculate token limit based on complexity and bot characteristics"""
        
        # start with base tokens for complexity level
        tokens = analysis.base_tokens
        
        # adjust for verbosity (up to 50% more tokens)
        tokens = int(tokens * (1 + characteristics.verbosity * 0.5))
        
        # adjust for thoughtfulness (up to 30% more tokens)
        tokens = int(tokens * (1 + characteristics.thoughtfulness * 0.3))
        
        # add buffer for tools if needed
        if analysis.requires_tools:
            tokens += 200  # extra tokens for tool calls and results
        
        return tokens
    
    def get_thought_interval(self, analysis: ComplexityAnalysis) -> float:
        """calculate time until next thought based on complexity"""
        
        # base intervals for each complexity level (in seconds)
        intervals = {
            Complexity.LOW: 300,  # 5 minutes
            Complexity.MEDIUM: 180,  # 3 minutes
            Complexity.HIGH: 60  # 1 minute
        }
        
        # get base interval
        interval = intervals[analysis.complexity]
        
        # add some randomness (±20%)
        variation = interval * 0.2
        interval += random.uniform(-variation, variation)
        
        return interval 
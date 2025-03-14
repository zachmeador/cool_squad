from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import os
import json
from cool_squad.core.models import Message
from cool_squad.bots.tools import Tool, create_tools
from cool_squad.utils.logging import log_api_call
from cool_squad.utils.token_budget import get_token_budget_tracker
from cool_squad.core.monologue import InternalMonologue
from cool_squad.core.complexity import ComplexityManager, BotCharacteristics, Complexity
from cool_squad.bots.personalities import (
    NORMIE_PERSONALITY,
    CURATOR_PERSONALITY,
    OLE_SCRAPPY_PERSONALITY,
    ROSICRUCIAN_RIDDLES_PERSONALITY,
    OBSESSIVE_CURATOR_PERSONALITY
)
import time
import logging
from cool_squad.llm.providers import LLMProvider, create_provider, LLMResponse, ToolDefinition

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize complexity manager
complexity_manager = ComplexityManager()

@dataclass
class Bot:
    name: str
    personality: str
    provider: str = "openai"  # provider: openai, anthropic, ollama, etc.
    model: str = "gpt-4o-mini-2024-07-18"
    temperature: float = 0.7
    tools: List[Tool] = field(default_factory=list)
    memory: List[Dict[str, str]] = field(default_factory=list)
    max_memory: int = 100
    respect_budget: bool = True
    monologue: InternalMonologue = field(default_factory=InternalMonologue)
    use_monologue: bool = True
    debug_mode: bool = False  # When True, shows internal monologue in responses
    characteristics: BotCharacteristics = field(default_factory=lambda: BotCharacteristics(
        verbosity=0.7,  # moderately verbose by default
        thoughtfulness=0.7  # moderately thoughtful by default
    ))
    last_thought_time: float = field(default_factory=lambda: time.time())
    next_thought_time: float = field(default_factory=lambda: time.time() + 300)  # start with 5 min interval

    def __post_init__(self):
        """initialize the llm provider"""
        self.llm = create_provider(
            provider=self.provider,
            model=self.model,
            temperature=self.temperature
        )

    def build_context_from_channels(self, channels_data, current_message=None, max_messages_per_channel=20, max_total_messages=50):
        """
        Build a context memory from recent messages in multiple channels.
        
        Args:
            channels_data: List of tuples (channel_name, channel_messages)
            current_message: The current message being processed (to exclude from context)
            max_messages_per_channel: Maximum number of messages to include from each channel
            max_total_messages: Maximum total messages to include in context
            
        Returns:
            List of message dicts formatted for LLM context
        """
        # start with the system message (personality)
        context = [{"role": "system", "content": self.personality}]
        
        # collect recent messages from all channels
        all_recent_messages = []
        
        for channel_name, messages in channels_data:
            # get last N messages from each channel
            recent = messages[-max_messages_per_channel:] if len(messages) > max_messages_per_channel else messages[:]
            for msg in recent:
                all_recent_messages.append((msg, channel_name))
        
        # sort all messages by timestamp
        all_recent_messages.sort(key=lambda x: x[0].timestamp)
        
        # take the most recent messages up to the maximum limit
        if len(all_recent_messages) > max_total_messages:
            all_recent_messages = all_recent_messages[-max_total_messages:]
        
        # add all messages to context
        for msg, ch_name in all_recent_messages:
            # don't include the current message being processed
            if current_message is None or msg is not current_message:
                context.append({
                    "role": "user" if msg.author != self.name else "assistant",
                    "content": f"[#{ch_name}] {msg.author}: {msg.content}"
                })
        
        return context

    async def process_message(self, message: Message, channel: str, channels_data=None) -> Optional[str]:
        # analyze message complexity first
        analysis = await complexity_manager.analyze_message(message.content)
        
        # update thought timing based on complexity
        current_time = time.time()
        if current_time >= self.next_thought_time:
            self.last_thought_time = current_time
            self.next_thought_time = current_time + complexity_manager.get_thought_interval(analysis)
        
        # Start internal monologue if:
        # 1. monologue is enabled AND
        # 2. either it's time for a thought OR complexity > LOW
        should_monologue = (
            self.use_monologue and 
            (current_time >= self.next_thought_time or analysis.complexity != Complexity.LOW)
        )
        
        if should_monologue:
            self.monologue.add_thought(
                f"Received message from {message.author} in #{channel}: '{message.content}'", 
                category="input"
            )
        
        # construct the conversation history
        if channels_data:
            # use the new context building method if channels data is provided
            messages = self.build_context_from_channels(channels_data, current_message=message)
        else:
            # fall back to the old method if no channels data is provided
            messages = [
                {"role": "system", "content": self.personality}
            ] + self.memory[-self.max_memory:]
        
        # add the current message
        messages.append({
            "role": "user",
            "content": f"[#{channel}] {message.author}: {message.content}"
        })

        try:
            # Check if we should respect budget limits
            if self.respect_budget:
                token_tracker = get_token_budget_tracker()
                # Check if we're already over budget
                if self.provider in token_tracker.provider_budgets:
                    budget = token_tracker.provider_budgets[self.provider]
                    if budget.daily_limit and token_tracker.daily_usage.get(self.provider, {}).get("_total", 0) >= budget.daily_limit:
                        return f"[Budget Limit] I'm unable to respond as the daily token budget for {self.provider} has been reached."
                    if budget.monthly_limit and token_tracker.monthly_usage.get(self.provider, {}).get("_total", 0) >= budget.monthly_limit:
                        return f"[Budget Limit] I'm unable to respond as the monthly token budget for {self.provider} has been reached."
                
                # Check model-specific budget if applicable
                if self.provider in token_tracker.model_budgets and self.model in token_tracker.model_budgets[self.provider]:
                    budget = token_tracker.model_budgets[self.provider][self.model]
                    if budget.daily_limit and token_tracker.daily_usage.get(self.provider, {}).get(self.model, 0) >= budget.daily_limit:
                        return f"[Budget Limit] I'm unable to respond as the daily token budget for {self.model} has been reached."
                    if budget.monthly_limit and token_tracker.monthly_usage.get(self.provider, {}).get(self.model, 0) >= budget.monthly_limit:
                        return f"[Budget Limit] I'm unable to respond as the monthly token budget for {self.model} has been reached."

            # Calculate token limit based on complexity and characteristics
            max_tokens = complexity_manager.get_token_limit(analysis, self.characteristics)
            
            # If using monologue and we have tools, first generate internal thinking
            if self.use_monologue and self.tools and analysis.requires_tools:
                await self._generate_internal_monologue(messages[-1]["content"])
                
                # Add monologue to the system message for context
                monologue_prompt = f"\n\nYour recent thoughts:\n{self.monologue.format_for_prompt()}"
                messages[0]["content"] += monologue_prompt

            # prepare tools if needed - only if complexity analysis indicates tools are required
            tool_definitions = None
            if self.tools and analysis.requires_tools:
                # Filter out the post_channel_message tool since we're handling responses directly
                filtered_tools = [tool for tool in self.tools if tool.name != "post_channel_message"]
                if filtered_tools:
                    tool_definitions = [tool.to_tool_definition() for tool in filtered_tools]

            # get initial response
            response = await self.llm.send_message(
                messages=messages,
                tools=tool_definitions,
                max_tokens=max_tokens
            )

            # handle tool calls if any
            if response.tool_calls:
                tool_outputs = []
                for tool_call in response.tool_calls:
                    tool = next(t for t in self.tools if t.name == tool_call.name)
                    result = await tool.function(**tool_call.arguments)
                    tool_outputs.append({
                        "name": tool_call.name,
                        "result": result
                    })
                    
                    # Record tool use in monologue
                    if self.use_monologue:
                        self.monologue.add_thought(
                            f"Using tool {tool_call.name} with args: {tool_call.arguments}", 
                            category="tool_use"
                        )
                        self.monologue.add_thought(
                            f"Tool {tool_call.name} returned: {result}", 
                            category="tool_result"
                        )

                # add tool results to conversation
                for output in tool_outputs:
                    messages.append({
                        "role": "tool",
                        "content": str(output["result"]),
                        "name": output["name"]
                    })

                # get final response with tool results
                final_response = await self.llm.send_message(
                    messages=messages,
                    tools=tool_definitions,
                    max_tokens=max_tokens
                )
                response = final_response

            # update memory
            self.memory.append({"role": "user", "content": messages[-1]["content"]})
            self.memory.append({"role": "assistant", "content": response.content})

            # If in debug mode, prepend the internal monologue
            if self.debug_mode and self.use_monologue:
                thoughts_summary = "\n".join([
                    f"[{t.category}] {t.content}" 
                    for t in self.monologue.get_recent_thoughts(5)
                ])
                
                tool_summary = ""
                if self.monologue.tool_considerations:
                    tool_summary = "\n\n[Tool Considerations]\n" + "\n".join([
                        f"{name} (relevance: {tc.relevance_score:.2f}): {tc.reasoning}" 
                        for name, tc in self.monologue.tool_considerations.items()
                    ])
                
                debug_info = f"[DEBUG: Internal Monologue]\n{thoughts_summary}{tool_summary}\n\n[RESPONSE]\n"
                return debug_info + response.content

            return response.content

        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logger.error(error_msg)
            return error_msg

    async def _generate_internal_monologue(self, user_message: str) -> None:
        """Generate internal monologue for the bot."""
        # Clear previous tool considerations
        self.monologue.clear_tool_considerations()
        
        # Create a prompt specifically for generating internal thoughts
        monologue_prompt = f"""You are {self.name}, with the following personality: {self.personality}

You are thinking through how to respond to this message: "{user_message}"

Think step by step about:
1. What is the user asking for?
2. What information do you need to respond effectively?
3. What tools might be helpful? Consider each available tool.

Available tools:
{self._format_available_tools()}

Format your response as an internal monologue that reflects your personality.
Focus on your reasoning process and how you would approach this request.
"""

        try:
            # get monologue response
            response = await self.llm.send_message(
                messages=[{"role": "user", "content": monologue_prompt}],
                max_tokens=500
            )
            
            # Add the generated thoughts to the monologue
            self.monologue.add_thought(response.content, category="reasoning")
            
            # Consider tools based on the monologue
            await self._consider_tools_from_monologue(response.content)
            
        except Exception as e:
            # If there's an error, add a simple thought instead
            self.monologue.add_thought(
                f"Error generating detailed thoughts: {str(e)}. Will proceed with direct response.", 
                category="error"
            )
    
    async def _consider_tools_from_monologue(self, monologue_text: str) -> None:
        """Extract tool considerations from the monologue text."""
        # Create a prompt to analyze which tools would be relevant
        tool_analysis_prompt = f"""Based on this internal monologue:

"{monologue_text}"

Which of the following tools would be most relevant to use? Rate each tool's relevance on a scale of 0.0 to 1.0, where 0.0 means completely irrelevant and 1.0 means essential.

Available tools:
{self._format_available_tools()}

Format your response as a JSON object with tool names as keys and objects containing "relevance" (float) and "reasoning" (string) as values.
Example:
{{
  "read_channel_messages": {{"relevance": 0.8, "reasoning": "Need to check recent messages in the channel"}},
  "post_channel_message": {{"relevance": 0.2, "reasoning": "Might need to post a response, but not certain yet"}}
}}
"""

        try:
            # get tool analysis response
            response = await self.llm.send_message(
                messages=[{"role": "user", "content": tool_analysis_prompt}],
                temperature=0.2  # lower temperature for more consistent json
            )
            
            # Parse the JSON response
            tool_analysis = json.loads(response.content)
            
            # Add tool considerations to the monologue
            for tool_name, analysis in tool_analysis.items():
                self.monologue.consider_tool(
                    tool_name=tool_name,
                    reasoning=analysis["reasoning"],
                    relevance_score=analysis["relevance"]
                )
                
        except Exception as e:
            # If there's an error, add a simple thought instead
            self.monologue.add_thought(
                f"Error analyzing tool relevance: {str(e)}. Will select tools directly.", 
                category="error"
            )
    
    def _format_available_tools(self) -> str:
        """Format available tools for inclusion in prompts."""
        tool_descriptions = []
        for tool in self.tools:
            params = json.dumps(tool.parameters, indent=2)
            tool_descriptions.append(f"- {tool.name}: {tool.description}\n  Parameters: {params}")
        
        return "\n\n".join(tool_descriptions)

# create bot tools instance
def create_bot_with_tools(name: str, personality: str, provider: str = "openai", model: str = "gpt-4o-mini", temperature: float = 0.7, use_monologue: bool = True, debug_mode: bool = False) -> Bot:
    """
    Create a bot with tools.
    
    Args:
        name: Bot name
        personality: Bot personality description
        provider: LLM provider (openai, anthropic, etc.)
        model: LLM model to use
        temperature: Temperature for generation
        use_monologue: Whether to use internal monologue
        debug_mode: Whether to show internal monologue in responses
        
    Returns:
        Bot instance with tools
    """
    return Bot(
        name=name,
        personality=personality,
        provider=provider,
        model=model,
        temperature=temperature,
        tools=create_tools(),
        use_monologue=use_monologue,
        debug_mode=debug_mode
    )

# example of creating bots with tools
def create_default_bots():
    """Create default bots with tools."""
    return [
        create_bot_with_tools("curator", CURATOR_PERSONALITY, provider="openai"),
        create_bot_with_tools("ole_scrappy", OLE_SCRAPPY_PERSONALITY, provider="openai", model="gpt-4o"),
        create_bot_with_tools("rosicrucian_riddles", ROSICRUCIAN_RIDDLES_PERSONALITY, provider="openai", model="gpt-4o"),
        create_bot_with_tools("normie", NORMIE_PERSONALITY, provider="openai", model="gpt-4o"),
        create_bot_with_tools("obsessive_curator", OBSESSIVE_CURATOR_PERSONALITY, provider="openai", model="gpt-4o"),
        create_bot_with_tools("claude_haiku", "", provider="anthropic", model="claude-3-haiku-20240307")
    ] 
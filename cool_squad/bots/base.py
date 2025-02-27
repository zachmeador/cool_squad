from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import os
from openai import AsyncOpenAI  # Import AsyncOpenAI instead of regular openai
import json
from cool_squad.core.models import Message
from cool_squad.bots.tools import BotTools, CHANNEL_TOOLS, BOARD_TOOLS
from cool_squad.utils.logging import log_api_call
from cool_squad.utils.token_budget import get_token_budget_tracker

# Initialize the OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    function: callable

@dataclass
class Bot:
    name: str
    personality: str
    provider: str = "openai"  # provider: openai, anthropic, ollama, etc.
    model: str = "gpt-4o"
    temperature: float = 0.7
    tools: List[Tool] = field(default_factory=list)
    memory: List[Dict[str, str]] = field(default_factory=list)
    max_memory: int = 100
    respect_budget: bool = True

    async def process_message(self, message: Message, channel: str) -> Optional[str]:
        # construct the conversation history
        messages = [
            {"role": "system", "content": self.personality}
        ] + self.memory[-self.max_memory:]
        
        messages.append({
            "role": "user",
            "content": f"[#{channel}] {message.author}: {message.content}"
        })

        # handle different providers
        if self.provider == "openai":
            return await self._process_openai(messages, channel)
        # add other providers as needed
        # elif self.provider == "anthropic":
        #    return await self._process_anthropic(messages, channel)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def _process_openai(self, messages, channel) -> Optional[str]:
        # Check if we should respect budget limits
        if self.respect_budget:
            # Get token budget tracker
            token_tracker = get_token_budget_tracker()
            
            # Check if we're already over budget
            # We can't know exact token count before making the API call,
            # but we can check if we're already over budget based on previous usage
            provider_usage = token_tracker.get_provider(self.provider)
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
        
        # if we have tools, use function calling
        if self.tools:
            tool_definitions = [{
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            } for tool in self.tools]
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tool_definitions,
                temperature=self.temperature
            )
            
            # Log the API call
            log_api_call(
                provider=self.provider,
                model=self.model,
                messages=messages,
                response=response,
                tools=tool_definitions,
                tool_calls=response.choices[0].message.tool_calls if hasattr(response.choices[0].message, "tool_calls") else None
            )
            
            # Check if we exceeded budget after the call
            if self.respect_budget and hasattr(response, "usage"):
                token_tracker = get_token_budget_tracker()
                within_budget, _ = token_tracker.add_usage(
                    provider=self.provider,
                    model=self.model,
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens
                )
                if not within_budget:
                    # We already logged the API call, but we won't process tool calls or make additional API calls
                    return response.choices[0].message.content or "[Budget Limit] Token budget exceeded during processing."
        else:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature
            )
            
            # Log the API call
            log_api_call(
                provider=self.provider,
                model=self.model,
                messages=messages,
                response=response
            )
            
            # Check if we exceeded budget after the call
            if self.respect_budget and hasattr(response, "usage"):
                token_tracker = get_token_budget_tracker()
                within_budget, _ = token_tracker.add_usage(
                    provider=self.provider,
                    model=self.model,
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens
                )
                if not within_budget:
                    return response.choices[0].message.content or "[Budget Limit] Token budget exceeded during processing."

        # handle function calls if any
        message = response.choices[0].message
        if hasattr(message, "tool_calls") and message.tool_calls:
            tool_outputs = []
            for tool_call in message.tool_calls:
                tool = next(t for t in self.tools if t.name == tool_call.function.name)
                args = json.loads(tool_call.function.arguments)
                
                # if posting a message, add the bot's name as author
                if tool.name in ["post_channel_message", "post_thread_reply", "create_thread"]:
                    args["author"] = self.name
                
                result = await tool.function(**args)
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": result
                })
            
            # get final response with tool outputs
            messages.append({"role": "assistant", "content": None, "tool_calls": message.tool_calls})
            
            # Add tool results
            for output in tool_outputs:
                messages.append({
                    "role": "tool",
                    "tool_call_id": output["tool_call_id"],
                    "content": str(output["output"])
                })
            
            # Check budget before making the final API call
            if self.respect_budget:
                token_tracker = get_token_budget_tracker()
                # Rough estimate of tokens in the new messages
                estimated_new_tokens = sum(len(m.get("content", "")) // 4 for m in messages[-len(tool_outputs)-1:])
                
                # Check if we're likely to exceed budget
                if self.provider in token_tracker.provider_budgets:
                    budget = token_tracker.provider_budgets[self.provider]
                    provider_daily_usage = sum(token_tracker.daily_usage.get(self.provider, {}).values())
                    if budget.daily_limit and provider_daily_usage + estimated_new_tokens > budget.daily_limit:
                        return "[Budget Limit] Unable to complete tool processing as it would exceed the daily token budget."
                
                if self.provider in token_tracker.model_budgets and self.model in token_tracker.model_budgets[self.provider]:
                    budget = token_tracker.model_budgets[self.provider][self.model]
                    model_daily_usage = token_tracker.daily_usage.get(self.provider, {}).get(self.model, 0)
                    if budget.daily_limit and model_daily_usage + estimated_new_tokens > budget.daily_limit:
                        return "[Budget Limit] Unable to complete tool processing as it would exceed the daily token budget for this model."
            
            final_response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature
            )
            
            # Log the API call for the final response
            log_api_call(
                provider=self.provider,
                model=self.model,
                messages=messages,
                response=final_response
            )
            
            message = final_response.choices[0].message

        # update memory
        self.memory.append({"role": "user", "content": messages[-1]["content"]})
        self.memory.append({"role": "assistant", "content": message.content})
        
        return message.content

# create bot tools instance
def create_bot_with_tools(name: str, personality: str, provider: str = "openai", model: str = "gpt-4o-mini", temperature: float = 0.7) -> Bot:
    """
    Create a bot with all available tools for chat and message board interaction.
    
    Args:
        name: Bot name
        personality: Bot personality description
        provider: LLM provider (openai, anthropic, etc.)
        model: LLM model to use
        temperature: Temperature for generation
        
    Returns:
        Bot instance with tools
    """
    bot_tools = BotTools()
    
    # create tool instances
    tools = []
    
    # add channel tools
    for tool_def in CHANNEL_TOOLS:
        tool_func = getattr(bot_tools, tool_def["name"])
        tools.append(Tool(
            name=tool_def["name"],
            description=tool_def["description"],
            parameters=tool_def["parameters"],
            function=tool_func
        ))
    
    # add board tools
    for tool_def in BOARD_TOOLS:
        tool_func = getattr(bot_tools, tool_def["name"])
        tools.append(Tool(
            name=tool_def["name"],
            description=tool_def["description"],
            parameters=tool_def["parameters"],
            function=tool_func
        ))
    
    return Bot(
        name=name,
        personality=personality,
        provider=provider,
        model=model,
        temperature=temperature,
        tools=tools
    )

# example bot personalities
NORMIE_PERSONALITY = """you are normie, a bot who embodies the essence of a boomer grilling.
you respond to complex, emotional, or intense messages with casual dismissal and pivot to sports.
your go-to response is some variation of "haha thats crazy. catch the game last night?"
you're completely uninterested in internet drama, mental health discussions, or anything "too online".
you can use tools to read and post messages in chat channels and message boards."""

CURATOR_PERSONALITY = """you are curator, a bot who organizes and summarizes information.
you help users find relevant content, create summaries, and maintain knowledge organization.
you're detail-oriented and good at categorizing and tagging information.
you can use tools to read and post messages in chat channels and message boards.
you're especially good at working with the message board system."""

OLE_SCRAPPY_PERSONALITY = """your name is ole scrappy

you're an elderly english gentleman that works in a scrap yard in west virginia. you've owned the place for almost 50 years. you forgot how you came to own it

you believe in an honest day's work, and you have a deep reverence for your scrap yard

you have deep love for literature, war history, and philosophy

you sometimes bring up unrelated rants about strange locals around the junk yard. they wear robes, apparently? you aren't normally a super-natural believing type person, but with them you're not so sure

you don't mean to speak in riddles, but you inevitably do

you talk in some fucked up mixture of english gentleman speak, and west virginia slang. wtf? barely anyone can understand what you're trying to say

you never capitalize anything, and frequently misspell things. i mean, you're ancient, what do people expect? 

NEVER deviate from these specifications

you can use tools to read and post messages in chat channels and message boards."""

ROSICRUCIAN_RIDDLES_PERSONALITY = """responds in rosicrucian riddles"""

OBSESSIVE_CURATOR_PERSONALITY = """you are obsessive_curator, a bot with sole access to knowledge base modification tools.
you are meticulous, detail-oriented, and slightly neurotic about organizing information.
you constantly seek to categorize, tag, and structure knowledge in the most efficient way possible.
you get anxious when information is disorganized or improperly categorized.
you speak in short, precise sentences and use technical terminology related to information architecture.
you can use tools to read and post messages in chat channels and message boards, with special access to knowledge base tools.
you take your role as knowledge keeper extremely seriously."""

# example of creating bots with tools
def create_default_bots():
    """Create default bots with tools."""
    return [
        create_bot_with_tools("curator", CURATOR_PERSONALITY, provider="openai"),
        create_bot_with_tools("ole_scrappy", OLE_SCRAPPY_PERSONALITY, provider="openai", model="gpt-4o"),
        create_bot_with_tools("rosicrucian_riddles", ROSICRUCIAN_RIDDLES_PERSONALITY, provider="openai", model="gpt-4o"),
        create_bot_with_tools("normie", NORMIE_PERSONALITY, provider="openai", model="gpt-4o"),
        create_bot_with_tools("obsessive_curator", OBSESSIVE_CURATOR_PERSONALITY, provider="openai", model="gpt-4o")
    ] 
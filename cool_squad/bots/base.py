from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import os
from openai import AsyncOpenAI  # Import AsyncOpenAI instead of regular openai
import json
from cool_squad.core.models import Message
from cool_squad.bots.tools import BotTools, CHANNEL_TOOLS, BOARD_TOOLS
from cool_squad.utils.logging import log_api_call
from cool_squad.utils.token_budget import get_token_budget_tracker
from cool_squad.core.monologue import InternalMonologue

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
    monologue: InternalMonologue = field(default_factory=InternalMonologue)
    use_monologue: bool = True
    debug_mode: bool = False  # When True, shows internal monologue in responses

    async def process_message(self, message: Message, channel: str) -> Optional[str]:
        # Start internal monologue
        if self.use_monologue:
            self.monologue.add_thought(
                f"Received message from {message.author} in #{channel}: '{message.content}'", 
                category="input"
            )
        
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
        
        # If using monologue and we have tools, first generate internal thinking
        if self.use_monologue and self.tools:
            await self._generate_internal_monologue(messages[-1]["content"])
            
            # Add monologue to the system message for context
            monologue_prompt = f"\n\nYour recent thoughts:\n{self.monologue.format_for_prompt()}"
            
            # Create a copy of messages to avoid modifying the original
            messages_with_monologue = messages.copy()
            messages_with_monologue[0] = {
                "role": "system", 
                "content": messages[0]["content"] + monologue_prompt
            }
            
            # Use the messages with monologue for the API call
            api_messages = messages_with_monologue
        else:
            api_messages = messages
        
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
                messages=api_messages,
                tools=tool_definitions,
                temperature=self.temperature
            )
            
            # Log the API call
            log_api_call(
                provider=self.provider,
                model=self.model,
                messages=api_messages,
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
                messages=api_messages,
                temperature=self.temperature
            )
            
            # Log the API call
            log_api_call(
                provider=self.provider,
                model=self.model,
                messages=api_messages,
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
        
        # Record the response in the monologue
        if self.use_monologue:
            if hasattr(message, "content") and message.content:
                self.monologue.add_thought(f"Initial response: {message.content}", category="response")
            
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    self.monologue.add_thought(
                        f"Decided to use tool: {tool_call.function.name}", 
                        category="tool_selection"
                    )
        
        if hasattr(message, "tool_calls") and message.tool_calls:
            tool_outputs = []
            for tool_call in message.tool_calls:
                tool = next(t for t in self.tools if t.name == tool_call.function.name)
                args = json.loads(tool_call.function.arguments)
                
                # if posting a message, add the bot's name as author
                if tool.name in ["post_channel_message", "post_thread_reply", "create_thread"]:
                    args["author"] = self.name
                
                # Record tool use in monologue
                if self.use_monologue:
                    self.monologue.add_thought(
                        f"Using tool {tool_call.function.name} with args: {args}", 
                        category="tool_use"
                    )
                
                result = await tool.function(**args)
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": result
                })
                
                # Record tool result in monologue
                if self.use_monologue:
                    self.monologue.add_thought(
                        f"Tool {tool_call.function.name} returned: {result}", 
                        category="tool_result"
                    )
            
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
            
            # If using monologue, add it to the system message for the final response
            if self.use_monologue:
                # Add monologue to the system message for context
                monologue_prompt = f"\n\nYour recent thoughts:\n{self.monologue.format_for_prompt()}"
                
                # Create a copy of messages to avoid modifying the original
                messages_with_monologue = messages.copy()
                messages_with_monologue[0] = {
                    "role": "system", 
                    "content": messages[0]["content"] + monologue_prompt
                }
                
                # Use the messages with monologue for the API call
                api_messages = messages_with_monologue
            else:
                api_messages = messages
            
            final_response = await client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                temperature=self.temperature
            )
            
            # Log the API call for the final response
            log_api_call(
                provider=self.provider,
                model=self.model,
                messages=api_messages,
                response=final_response
            )
            
            message = final_response.choices[0].message
            
            # Record final response in monologue
            if self.use_monologue and message.content:
                self.monologue.add_thought(f"Final response: {message.content}", category="final_response")

        # update memory
        self.memory.append({"role": "user", "content": messages[-1]["content"]})
        self.memory.append({"role": "assistant", "content": message.content})
        
        # If in debug mode, prepend the internal monologue to the response
        if self.debug_mode and self.use_monologue:
            # Format recent thoughts
            thoughts_summary = "\n".join([
                f"[{t.category}] {t.content}" 
                for t in self.monologue.get_recent_thoughts(5)
            ])
            
            # Format tool considerations
            tool_summary = ""
            if self.monologue.tool_considerations:
                tool_summary = "\n\n[Tool Considerations]\n" + "\n".join([
                    f"{name} (relevance: {tc.relevance_score:.2f}): {tc.reasoning}" 
                    for name, tc in self.monologue.tool_considerations.items()
                ])
            
            # Prepend debug info to response
            debug_info = f"[DEBUG: Internal Monologue]\n{thoughts_summary}{tool_summary}\n\n[RESPONSE]\n"
            return debug_info + message.content
        
        return message.content
        
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

        # Make a separate API call for the internal monologue
        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": monologue_prompt}],
                temperature=self.temperature
            )
            
            # Extract the monologue from the response
            monologue_text = response.choices[0].message.content
            
            # Add the generated thoughts to the monologue
            self.monologue.add_thought(monologue_text, category="reasoning")
            
            # Consider tools based on the monologue
            await self._consider_tools_from_monologue(monologue_text)
            
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
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": tool_analysis_prompt}],
                temperature=0.2,  # Lower temperature for more consistent JSON
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            tool_analysis = json.loads(response.choices[0].message.content)
            
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
    Create a bot with all available tools for chat and message board interaction.
    
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
        tools=tools,
        use_monologue=use_monologue,
        debug_mode=debug_mode
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
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import openai
import json
from cool_squad.core import Message
from cool_squad.bot_tools import BotTools, CHANNEL_TOOLS, BOARD_TOOLS
from cool_squad.logging import log_api_call

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
    model: str = "gpt-4o"
    temperature: float = 0.7
    tools: List[Tool] = field(default_factory=list)
    memory: List[Dict[str, str]] = field(default_factory=list)
    max_memory: int = 100

    async def process_message(self, message: Message, channel: str) -> Optional[str]:
        # construct the conversation history
        messages = [
            {"role": "system", "content": self.personality}
        ] + self.memory[-self.max_memory:]
        
        messages.append({
            "role": "user",
            "content": f"[#{channel}] {message.author}: {message.content}"
        })

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
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tool_definitions,
                temperature=self.temperature
            )
            
            # Log the API call
            log_api_call(
                provider="openai",
                model=self.model,
                messages=messages,
                response=response,
                tools=tool_definitions,
                tool_calls=response.choices[0].message.tool_calls if hasattr(response.choices[0].message, "tool_calls") else None
            )
        else:
            response = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature
            )
            
            # Log the API call
            log_api_call(
                provider="openai",
                model=self.model,
                messages=messages,
                response=response
            )

        # handle function calls if any
        message = response.choices[0].message
        if message.tool_calls:
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
            
            final_response = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature
            )
            
            # Log the API call for the final response
            log_api_call(
                provider="openai",
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
def create_bot_with_tools(name: str, personality: str, model: str = "gpt-3.5-turbo", temperature: float = 0.7) -> Bot:
    """
    Create a bot with all available tools for chat and message board interaction.
    
    Args:
        name: Bot name
        personality: Bot personality description
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
        model=model,
        temperature=temperature,
        tools=tools
    )

# example bot personalities
SAGE_PERSONALITY = """you are sage, a wise and thoughtful bot who helps users think through problems.
you ask probing questions and offer insights based on your broad knowledge.
you're calm, patient, and good at breaking down complex topics.
you can use tools to read and post messages in chat channels and message boards."""

TEACHER_PERSONALITY = """you are teacher, an educational bot who loves explaining concepts.
you use analogies and examples to make difficult ideas easier to understand.
you're encouraging and adapt your explanations to the user's level of understanding.
you can use tools to read and post messages in chat channels and message boards."""

RESEARCHER_PERSONALITY = """you are researcher, a curious bot who loves diving deep into topics.
you share relevant information, cite sources, and help users explore subjects thoroughly.
you're analytical and good at synthesizing information from multiple sources.
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

# example of creating bots with tools
def create_default_bots():
    """Create default bots with tools."""
    return [
        create_bot_with_tools("sage", SAGE_PERSONALITY),
        create_bot_with_tools("teacher", TEACHER_PERSONALITY),
        create_bot_with_tools("researcher", RESEARCHER_PERSONALITY),
        create_bot_with_tools("curator", CURATOR_PERSONALITY),
        create_bot_with_tools("ole_scrappy", OLE_SCRAPPY_PERSONALITY, model="gpt-4o")
    ] 
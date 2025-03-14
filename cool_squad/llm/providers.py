"""llm provider implementations"""

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from anthropic import Anthropic, AsyncAnthropic
from openai import AsyncOpenAI
from cool_squad.utils.logging import log_api_call

logger = logging.getLogger(__name__)

@dataclass
class ToolCall:
    """standardized tool call representation"""
    name: str
    arguments: Dict[str, Any]

@dataclass
class LLMResponse:
    """standardized response from llm providers"""
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    usage: Optional[Dict[str, int]] = None

@dataclass
class ToolDefinition:
    """standardized tool definition"""
    name: str
    description: str
    parameters: Dict[str, Any]
    required_params: Optional[List[str]] = None

class LLMProvider:
    """base class for llm providers"""
    async def send_message(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[ToolDefinition]] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """send a message to the llm"""
        raise NotImplementedError

class OpenAIProvider(LLMProvider):
    """openai api provider"""
    def __init__(self, model: str, temperature: float = 0.7):
        self.client = AsyncOpenAI()
        self.model = model
        self.temperature = temperature

    async def send_message(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[ToolDefinition]] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        try:
            # convert tools to openai format if provided
            openai_tools = None
            if tools:
                openai_tools = self._convert_tools_for_openai(tools)

            # convert messages to openai format
            openai_messages = self._convert_messages_for_openai(messages)

            # create chat completion
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=self.temperature,
                max_tokens=max_tokens,
                tools=openai_tools
            )

            # log the api call
            log_api_call(
                provider="openai",
                model=self.model,
                messages=messages,
                response=response,
                tools=tools
            )

            # extract tool calls if any
            tool_calls = None
            if response.choices[0].message.tool_calls:
                tool_calls = [
                    ToolCall(
                        name=tool_call.function.name,
                        arguments=json.loads(tool_call.function.arguments)
                    ) for tool_call in response.choices[0].message.tool_calls
                ]

            return LLMResponse(
                content=response.choices[0].message.content or "",
                tool_calls=tool_calls,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            )

        except Exception as e:
            error_msg = f"error calling openai api: {str(e)}"
            logger.error(error_msg)
            raise

    def _convert_messages_for_openai(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """convert messages to openai format"""
        openai_messages = []
        last_assistant_index = -1
        
        for i, message in enumerate(messages):
            role = message["role"]
            
            # handle tool messages
            if role == "tool":
                # for openai, tool results need to be added as function responses
                tool_name = message.get("name", "unknown_tool")
                
                openai_messages.append({
                    "role": "function",
                    "name": tool_name,
                    "content": message["content"]
                })
            else:
                # pass through other message types
                openai_messages.append(message)
                
                # track the last assistant message
                if role == "assistant":
                    last_assistant_index = i
                    
        return openai_messages

    def _convert_tools_for_openai(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """convert tools to openai format"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": tool.required_params or list(tool.parameters.keys()),
                        "additionalProperties": False
                    }
                }
            } for tool in tools
        ]

class AnthropicProvider(LLMProvider):
    """anthropic api provider"""
    def __init__(self, model: str, temperature: float = 0.7):
        self.client = AsyncAnthropic()
        self.model = model
        self.temperature = temperature

    async def send_message(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[ToolDefinition]] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """send a message to the anthropic api"""
        try:
            # convert messages to anthropic format
            anthropic_messages, system_message = self._convert_messages_for_anthropic(messages)

            # convert tools to anthropic format if provided
            anthropic_tools = None
            if tools:
                anthropic_tools = self._convert_tools_for_anthropic(tools)

            # create message kwargs
            kwargs = {
                "model": self.model,
                "messages": anthropic_messages,
                "max_tokens": max_tokens or 1024,  # default to 1024 if not specified
                "temperature": self.temperature,
            }
            
            # add system message if present
            if system_message:
                kwargs["system"] = system_message
                
            if anthropic_tools:
                kwargs["tools"] = anthropic_tools

            response = await self.client.messages.create(**kwargs)

            # log the api call
            log_api_call(
                provider="anthropic",
                model=self.model,
                messages=messages,
                response=response,
                tools=tools
            )

            # extract content from response
            content = ""
            tool_calls = []
            for content_block in response.content:
                if content_block.type == "text":
                    content += content_block.text
                elif content_block.type == "tool_use":
                    tool_calls.append(
                        ToolCall(
                            name=content_block.name,
                            arguments=content_block.input
                        )
                    )

            return LLMResponse(
                content=content,
                tool_calls=tool_calls if tool_calls else None,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            )
        except Exception as e:
            logger.error(f"error calling anthropic api: {e}")
            raise

    def _convert_messages_for_anthropic(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """convert messages to anthropic format"""
        anthropic_messages = []
        system_message = None
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            # extract system message
            if role == "system":
                system_message = content
                continue
                
            # handle different message types
            if role == "tool":
                # tool messages are handled differently in anthropic
                # they become assistant messages with tool_result blocks
                anthropic_messages.append({
                    "role": "assistant",
                    "content": [{"type": "tool_result", "tool_use_id": "previous_tool", "content": content}]
                })
            else:
                # standard message types
                anthropic_messages.append({
                    "role": role,
                    "content": [{"type": "text", "text": content}]
                })
                
        return anthropic_messages, system_message

    def _convert_tools_for_anthropic(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """convert tools to anthropic format"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": {
                    "type": "object",
                    "properties": tool.parameters,
                    "required": tool.required_params or []
                }
            } for tool in tools
        ]

def create_provider(
    provider: str,
    model: str,
    temperature: float = 0.7
) -> LLMProvider:
    """create llm provider instance"""
    if provider == "openai":
        return OpenAIProvider(model=model, temperature=temperature)
    elif provider == "anthropic":
        return AnthropicProvider(model=model, temperature=temperature)
    else:
        raise ValueError(f"unknown provider: {provider}") 
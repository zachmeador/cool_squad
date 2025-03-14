"""test openai api integration"""

import logging
import os
import pytest
from dotenv import load_dotenv

from cool_squad.llm.providers import OpenAIProvider
from cool_squad.bots.tools import create_tools

# set up logging
logging.basicConfig(level=logging.DEBUG)

# load environment variables
load_dotenv()

@pytest.fixture
def openai_provider():
    """create an openai provider"""
    return OpenAIProvider(
        model="gpt-4o-mini",
        temperature=0.7
    )

@pytest.mark.asyncio
async def test_openai_basic_response(openai_provider):
    """test basic message response"""
    response = await openai_provider.send_message(
        messages=[
            {"role": "user", "content": "what is 2+2?"}
        ]
    )
    assert "4" in response.content

@pytest.mark.asyncio
async def test_openai_tool_use(openai_provider):
    """test tool usage"""
    tools = create_tools()
    tool_definitions = [tool.to_tool_definition() for tool in tools]
    response = await openai_provider.send_message(
        messages=[
            {"role": "user", "content": "calculate 15 * 3 + 2"}
        ],
        tools=tool_definitions
    )
    assert "47" in response.content

@pytest.mark.asyncio
async def test_openai_tool_error_handling(openai_provider):
    """test error handling with invalid tool call"""
    tools = create_tools()
    tool_definitions = [tool.to_tool_definition() for tool in tools]
    response = await openai_provider.send_message(
        messages=[
            {"role": "user", "content": "use a tool that doesn't exist"}
        ],
        tools=tool_definitions
    )
    assert response.tool_calls is None or len(response.tool_calls) == 0  # verify no tools were called
    assert response.content  # verify we got some response 
"""
Tests for the internal monologue functionality.
"""

import pytest
import time
from cool_squad.core.monologue import InternalMonologue, Thought, ToolConsideration


def test_thought_creation():
    """Test that thoughts can be created correctly."""
    thought = Thought(content="I should check recent messages", category="reasoning")
    
    assert thought.content == "I should check recent messages"
    assert thought.category == "reasoning"
    assert thought.timestamp is not None
    assert str(thought).startswith("[reasoning]")


def test_tool_consideration_creation():
    """Test that tool considerations can be created correctly."""
    consideration = ToolConsideration(
        tool_name="read_channel_messages",
        reasoning="Need to check recent messages",
        relevance_score=0.8
    )
    
    assert consideration.tool_name == "read_channel_messages"
    assert consideration.reasoning == "Need to check recent messages"
    assert consideration.relevance_score == 0.8
    assert consideration.timestamp is not None
    assert "relevance: 0.80" in str(consideration)


def test_monologue_add_thought():
    """Test adding thoughts to the monologue."""
    monologue = InternalMonologue()
    
    monologue.add_thought("First thought", "general")
    monologue.add_thought("Second thought", "reasoning")
    
    assert len(monologue.thoughts) == 2
    assert monologue.thoughts[0].content == "First thought"
    assert monologue.thoughts[1].category == "reasoning"


def test_monologue_max_thoughts():
    """Test that monologue respects max_thoughts limit."""
    monologue = InternalMonologue(max_thoughts=3)
    
    for i in range(5):
        monologue.add_thought(f"Thought {i}", "general")
    
    assert len(monologue.thoughts) == 3
    assert monologue.thoughts[0].content == "Thought 2"
    assert monologue.thoughts[2].content == "Thought 4"


def test_consider_tool():
    """Test adding tool considerations."""
    monologue = InternalMonologue()
    
    monologue.consider_tool(
        tool_name="read_channel_messages",
        reasoning="Need to check recent messages",
        relevance_score=0.8
    )
    
    monologue.consider_tool(
        tool_name="post_channel_message",
        reasoning="Might need to post a response",
        relevance_score=0.3
    )
    
    assert len(monologue.tool_considerations) == 2
    assert "read_channel_messages" in monologue.tool_considerations
    assert monologue.tool_considerations["read_channel_messages"].relevance_score == 0.8


def test_get_recent_thoughts():
    """Test retrieving recent thoughts."""
    monologue = InternalMonologue()
    
    for i in range(10):
        monologue.add_thought(f"Thought {i}", "general" if i % 2 == 0 else "reasoning")
    
    # Get last 3 thoughts
    recent = monologue.get_recent_thoughts(3)
    assert len(recent) == 3
    assert recent[0].content == "Thought 7"
    assert recent[2].content == "Thought 9"
    
    # Get thoughts by category
    reasoning_thoughts = monologue.get_recent_thoughts(5, category="reasoning")
    assert len(reasoning_thoughts) <= 5
    assert all(t.category == "reasoning" for t in reasoning_thoughts)


def test_get_relevant_tools():
    """Test retrieving relevant tools based on threshold."""
    monologue = InternalMonologue()
    
    monologue.consider_tool("tool1", "Reasoning 1", 0.9)
    monologue.consider_tool("tool2", "Reasoning 2", 0.5)
    monologue.consider_tool("tool3", "Reasoning 3", 0.2)
    
    # Get tools with relevance >= 0.5
    relevant = monologue.get_relevant_tools(0.5)
    assert len(relevant) == 2
    assert any(tc.tool_name == "tool1" for tc in relevant)
    assert any(tc.tool_name == "tool2" for tc in relevant)
    assert not any(tc.tool_name == "tool3" for tc in relevant)


def test_clear_tool_considerations():
    """Test clearing tool considerations."""
    monologue = InternalMonologue()
    
    monologue.consider_tool("tool1", "Reasoning 1", 0.9)
    monologue.consider_tool("tool2", "Reasoning 2", 0.5)
    
    assert len(monologue.tool_considerations) == 2
    
    monologue.clear_tool_considerations()
    assert len(monologue.tool_considerations) == 0


def test_summarize():
    """Test summarizing the monologue."""
    monologue = InternalMonologue()
    
    monologue.add_thought("First thought", "general")
    monologue.add_thought("Second thought", "reasoning")
    
    summary = monologue.summarize()
    assert "First thought" in summary
    assert "Second thought" in summary
    assert "[general]" in summary
    assert "[reasoning]" in summary


def test_format_for_prompt():
    """Test formatting the monologue for inclusion in a prompt."""
    monologue = InternalMonologue()
    
    monologue.add_thought("First thought", "general")
    monologue.add_thought("Second thought", "reasoning")
    
    formatted = monologue.format_for_prompt()
    assert "Thought: First thought" in formatted
    assert "Thought: Second thought" in formatted


def test_to_dict_and_from_dict():
    """Test serializing and deserializing the monologue."""
    monologue = InternalMonologue()
    
    monologue.add_thought("Test thought", "general")
    monologue.consider_tool("test_tool", "Test reasoning", 0.7)
    
    # Convert to dict
    data = monologue.to_dict()
    
    # Create new monologue from dict
    new_monologue = InternalMonologue.from_dict(data)
    
    assert len(new_monologue.thoughts) == 1
    assert new_monologue.thoughts[0].content == "Test thought"
    assert new_monologue.thoughts[0].category == "general"
    
    assert len(new_monologue.tool_considerations) == 1
    assert "test_tool" in new_monologue.tool_considerations
    assert new_monologue.tool_considerations["test_tool"].reasoning == "Test reasoning"
    assert new_monologue.tool_considerations["test_tool"].relevance_score == 0.7 
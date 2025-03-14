"""
Tests for the integration of internal monologue with bots.
"""

import pytest
from unittest.mock import MagicMock, patch
from cool_squad.bots.base import Bot
from cool_squad.core.models import Message


def test_bot_monologue_initialization():
    """Test that a bot initializes with an internal monologue."""
    bot = Bot("test_bot", "Test personality", use_monologue=True)
    assert bot.use_monologue is True
    assert len(bot.monologue.thoughts) == 0


def test_bot_adds_thought():
    """Test that a bot can add thoughts to its monologue."""
    bot = Bot("test_bot", "Test personality", use_monologue=True)
    bot.monologue.add_thought("test thought", "general")
    assert len(bot.monologue.thoughts) == 1
    assert bot.monologue.thoughts[0].content == "test thought"


def test_bot_without_monologue():
    """Test that a bot with monologue disabled doesn't use it."""
    bot = Bot("test_bot", "Test personality", use_monologue=False)
    bot.monologue.add_thought("test thought", "general")
    assert bot.use_monologue is False
    assert len(bot.monologue.thoughts) == 1  # still adds thought but won't use it


def test_debug_mode():
    """Test that debug mode includes monologue in responses."""
    bot = Bot(
        name="debug_bot",
        personality="Test personality",
        use_monologue=True,
        debug_mode=True
    )
    
    # Add some thoughts
    bot.monologue.add_thought("first thought", "general")
    bot.monologue.add_thought("second thought", "reasoning")
    
    # Get formatted thoughts
    thoughts_summary = "\n".join([
        f"[{t.category}] {t.content}" 
        for t in bot.monologue.get_recent_thoughts(5)
    ])
    
    # Check thought formatting
    assert "[general] first thought" in thoughts_summary
    assert "[reasoning] second thought" in thoughts_summary 
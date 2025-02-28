"""
Autonomous thinking module for bots.

This module provides functionality for bots to have autonomous thoughts
independent of user interactions. It runs as a background task and
periodically triggers thinking for bots that haven't had recent interactions.
"""

import asyncio
import random
import time
import logging
from typing import List, Dict, Any, Optional, Callable
import json

from cool_squad.core import config
from cool_squad.core.models import Message
from cool_squad.bots.base import Bot

# Set up logging
logger = logging.getLogger(__name__)

class AutonomousThinkingManager:
    """
    Manager for autonomous bot thinking.
    
    This class manages the autonomous thinking process for bots,
    running as a background task that periodically triggers
    thinking for bots that haven't had recent interactions.
    """
    
    def __init__(self):
        self.bots: List[Bot] = []
        self.running: bool = False
        self.task: Optional[asyncio.Task] = None
        self.message_callback: Optional[Callable] = None
        self.context_providers: List[Callable] = []
        
    def register_bot(self, bot: Bot) -> None:
        """Register a bot with the autonomous thinking manager."""
        if bot not in self.bots:
            self.bots.append(bot)
            logger.info(f"Registered bot '{bot.name}' for autonomous thinking")
    
    def register_bots(self, bots: List[Bot]) -> None:
        """Register multiple bots with the autonomous thinking manager."""
        for bot in bots:
            self.register_bot(bot)
    
    def unregister_bot(self, bot: Bot) -> None:
        """Unregister a bot from the autonomous thinking manager."""
        if bot in self.bots:
            self.bots.remove(bot)
            logger.info(f"Unregistered bot '{bot.name}' from autonomous thinking")
    
    def set_message_callback(self, callback: Callable) -> None:
        """
        Set a callback function for when a bot decides to speak.
        
        The callback should accept (bot_name, message_content, context) parameters.
        """
        self.message_callback = callback
    
    def add_context_provider(self, provider: Callable) -> None:
        """
        Add a context provider function.
        
        Context providers should return a dict with context information
        that will be passed to the autonomous thinking prompt.
        """
        self.context_providers.append(provider)
    
    def get_combined_context(self) -> Dict[str, Any]:
        """Get combined context from all context providers."""
        context = {}
        for provider in self.context_providers:
            try:
                provider_context = provider()
                if provider_context:
                    context.update(provider_context)
            except Exception as e:
                logger.error(f"Error getting context from provider: {e}")
        return context
    
    async def start(self) -> None:
        """Start the autonomous thinking background task."""
        if self.running:
            logger.warning("Autonomous thinking is already running")
            return
            
        if not config.AUTONOMOUS_THINKING_ENABLED:
            logger.info("Autonomous thinking is disabled in config")
            return
            
        self.running = True
        self.task = asyncio.create_task(self._thinking_loop())
        logger.info("Started autonomous thinking background task")
    
    async def stop(self) -> None:
        """Stop the autonomous thinking background task."""
        if not self.running:
            return
            
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        logger.info("Stopped autonomous thinking background task")
    
    async def _thinking_loop(self) -> None:
        """Main loop for autonomous thinking."""
        while self.running:
            # Get random interval between min and max
            interval = random.uniform(
                config.BOT_MIN_THINKING_INTERVAL,
                config.BOT_MAX_THINKING_INTERVAL
            )
            
            # Wait for the interval
            await asyncio.sleep(interval)
            
            # Get context from providers
            context = self.get_combined_context()
            
            # Trigger thinking for each bot
            for bot in self.bots:
                if bot.use_monologue:
                    asyncio.create_task(self._trigger_bot_thought(bot, context))
    
    async def _trigger_bot_thought(self, bot: Bot, context: Dict[str, Any]) -> None:
        """Generate an autonomous thought for a bot."""
        # Skip if the bot has had recent interaction
        if hasattr(bot.monologue, 'has_recent_interaction') and bot.monologue.has_recent_interaction():
            return
        
        # Create a thinking prompt based on context
        thinking_prompt = self._create_thinking_prompt(bot, context)
        
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI()
            
            # Make API call for autonomous thought
            response = await client.chat.completions.create(
                model=bot.model,
                messages=[{"role": "user", "content": thinking_prompt}],
                temperature=0.8  # Higher temperature for more creative thoughts
            )
            
            # Add the thought to the bot's monologue
            thought_text = response.choices[0].message.content
            bot.monologue.add_thought(thought_text, category="autonomous")
            logger.debug(f"Bot '{bot.name}' had autonomous thought: {thought_text}")
            
            # Optionally trigger speaking
            if config.BOT_AUTONOMOUS_SPEAKING_ENABLED and random.random() < config.BOT_AUTONOMOUS_SPEAKING_CHANCE:
                if self.message_callback:
                    await self.message_callback(bot.name, thought_text, context)
        except Exception as e:
            logger.error(f"Error generating autonomous thought for {bot.name}: {e}")
    
    def _create_thinking_prompt(self, bot: Bot, context: Dict[str, Any]) -> str:
        """Create a thinking prompt for the bot based on context."""
        # Base prompt
        prompt = f"""You are {bot.name} with personality: {bot.personality}

You're currently idle and having an autonomous thought.
"""

        # Add context if available
        if context:
            prompt += "\nContext information:\n"
            for key, value in context.items():
                prompt += f"- {key}: {value}\n"
        
        # Add instructions
        prompt += """
Generate a brief, personality-appropriate thought that reflects your character.
This could be:
- Reflecting on recent conversations or events
- Wondering about topics related to your interests
- Considering checking message boards or other channels
- Any other thought that fits your personality

Keep it brief (1-3 sentences) and authentic to your character.
"""
        
        return prompt


# Singleton instance
_manager = None

def get_autonomous_thinking_manager() -> AutonomousThinkingManager:
    """Get the singleton instance of the autonomous thinking manager."""
    global _manager
    if _manager is None:
        _manager = AutonomousThinkingManager()
    return _manager 
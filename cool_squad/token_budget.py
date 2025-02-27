"""
Token Budget Tracking System

This module provides functionality to track token usage across different LLM providers and models.
It allows setting budgets and monitoring usage to control costs.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import logging
from cool_squad.config import get_data_dir

logger = logging.getLogger("token_budget")
logger.setLevel(logging.INFO)

@dataclass
class ModelUsage:
    """Track usage for a specific model"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    def add_usage(self, prompt_tokens: int, completion_tokens: int):
        """Add token usage from an API call"""
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens += prompt_tokens + completion_tokens

@dataclass
class ProviderUsage:
    """Track usage for a specific provider across all models"""
    models: Dict[str, ModelUsage] = field(default_factory=dict)
    
    def get_model(self, model: str) -> ModelUsage:
        """Get or create a model usage tracker"""
        if model not in self.models:
            self.models[model] = ModelUsage()
        return self.models[model]
    
    def add_usage(self, model: str, prompt_tokens: int, completion_tokens: int):
        """Add token usage for a specific model"""
        model_usage = self.get_model(model)
        model_usage.add_usage(prompt_tokens, completion_tokens)
    
    def get_total_tokens(self) -> int:
        """Get total tokens used across all models"""
        return sum(model.total_tokens for model in self.models.values())

@dataclass
class TokenBudget:
    """Token budget settings for a provider or model"""
    daily_limit: Optional[int] = None
    monthly_limit: Optional[int] = None
    
    def is_within_budget(self, daily_usage: int, monthly_usage: int) -> Tuple[bool, str]:
        """Check if usage is within budget limits"""
        if self.daily_limit and daily_usage >= self.daily_limit:
            return False, f"Daily limit of {self.daily_limit} tokens exceeded"
        if self.monthly_limit and monthly_usage >= self.monthly_limit:
            return False, f"Monthly limit of {self.monthly_limit} tokens exceeded"
        return True, ""

class TokenBudgetTracker:
    """Track token usage and enforce budgets"""
    
    def __init__(self):
        self.providers: Dict[str, ProviderUsage] = {}
        self.provider_budgets: Dict[str, TokenBudget] = {}
        self.model_budgets: Dict[str, Dict[str, TokenBudget]] = {}
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.monthly_reset_time = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self.daily_usage: Dict[str, Dict[str, int]] = {}
        self.monthly_usage: Dict[str, Dict[str, int]] = {}
        self.load_state()
    
    def get_provider(self, provider: str) -> ProviderUsage:
        """Get or create a provider usage tracker"""
        if provider not in self.providers:
            self.providers[provider] = ProviderUsage()
        return self.providers[provider]
    
    def add_usage(self, provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> Tuple[bool, str]:
        """
        Add token usage and check if it's within budget
        
        Returns:
            Tuple of (is_within_budget, message)
        """
        # Check if we need to reset daily/monthly counters
        self._check_reset_periods()
        
        # Initialize usage dictionaries if needed
        if provider not in self.daily_usage:
            self.daily_usage[provider] = {}
            self.monthly_usage[provider] = {}
        if model not in self.daily_usage[provider]:
            self.daily_usage[provider][model] = 0
            self.monthly_usage[provider][model] = 0
        
        # Calculate new usage
        new_tokens = prompt_tokens + completion_tokens
        new_daily_usage = self.daily_usage[provider][model] + new_tokens
        new_monthly_usage = self.monthly_usage[provider][model] + new_tokens
        
        # Check model-specific budget
        if provider in self.model_budgets and model in self.model_budgets[provider]:
            budget = self.model_budgets[provider][model]
            within_budget, message = budget.is_within_budget(new_daily_usage, new_monthly_usage)
            if not within_budget:
                return False, f"Model {model}: {message}"
        
        # Check provider-wide budget
        if provider in self.provider_budgets:
            provider_daily_usage = sum(self.daily_usage[provider].values()) + new_tokens
            provider_monthly_usage = sum(self.monthly_usage[provider].values()) + new_tokens
            
            budget = self.provider_budgets[provider]
            within_budget, message = budget.is_within_budget(provider_daily_usage, provider_monthly_usage)
            if not within_budget:
                return False, f"Provider {provider}: {message}"
        
        # Update usage counters
        provider_usage = self.get_provider(provider)
        provider_usage.add_usage(model, prompt_tokens, completion_tokens)
        
        # Update daily and monthly tracking
        self.daily_usage[provider][model] += new_tokens
        self.monthly_usage[provider][model] += new_tokens
        
        # Save state
        self.save_state()
        
        return True, ""
    
    def set_provider_budget(self, provider: str, daily_limit: Optional[int] = None, monthly_limit: Optional[int] = None):
        """Set budget for a provider"""
        self.provider_budgets[provider] = TokenBudget(daily_limit=daily_limit, monthly_limit=monthly_limit)
        self.save_state()
    
    def set_model_budget(self, provider: str, model: str, daily_limit: Optional[int] = None, monthly_limit: Optional[int] = None):
        """Set budget for a specific model"""
        if provider not in self.model_budgets:
            self.model_budgets[provider] = {}
        self.model_budgets[provider][model] = TokenBudget(daily_limit=daily_limit, monthly_limit=monthly_limit)
        self.save_state()
    
    def get_usage_report(self) -> Dict:
        """Get a complete usage report"""
        report = {
            "providers": {},
            "daily_usage": self.daily_usage,
            "monthly_usage": self.monthly_usage,
            "daily_reset": self.daily_reset_time.isoformat(),
            "monthly_reset": self.monthly_reset_time.isoformat(),
            "budgets": {
                "providers": {p: {"daily": b.daily_limit, "monthly": b.monthly_limit} 
                             for p, b in self.provider_budgets.items()},
                "models": {p: {m: {"daily": b.daily_limit, "monthly": b.monthly_limit} 
                              for m, b in models.items()} 
                          for p, models in self.model_budgets.items()}
            }
        }
        
        for provider, usage in self.providers.items():
            provider_data = {
                "total_tokens": usage.get_total_tokens(),
                "models": {}
            }
            
            for model, model_usage in usage.models.items():
                provider_data["models"][model] = {
                    "prompt_tokens": model_usage.prompt_tokens,
                    "completion_tokens": model_usage.completion_tokens,
                    "total_tokens": model_usage.total_tokens
                }
            
            report["providers"][provider] = provider_data
        
        return report
    
    def _check_reset_periods(self):
        """Check if we need to reset daily or monthly counters"""
        now = datetime.now()
        
        # Check daily reset
        if now.date() > self.daily_reset_time.date():
            self.daily_usage = {}
            self.daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            logger.info(f"Reset daily token usage counters at {self.daily_reset_time}")
        
        # Check monthly reset
        if (now.year > self.monthly_reset_time.year or 
            (now.year == self.monthly_reset_time.year and now.month > self.monthly_reset_time.month)):
            self.monthly_usage = {}
            self.monthly_reset_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            logger.info(f"Reset monthly token usage counters at {self.monthly_reset_time}")
    
    def get_state_file_path(self) -> str:
        """Get the path to the state file"""
        data_dir = get_data_dir()
        return os.path.join(data_dir, "token_budget_state.json")
    
    def save_state(self):
        """Save the current state to a file"""
        try:
            state = {
                "daily_reset_time": self.daily_reset_time.isoformat(),
                "monthly_reset_time": self.monthly_reset_time.isoformat(),
                "daily_usage": self.daily_usage,
                "monthly_usage": self.monthly_usage,
                "provider_budgets": {p: {"daily_limit": b.daily_limit, "monthly_limit": b.monthly_limit} 
                                    for p, b in self.provider_budgets.items()},
                "model_budgets": {p: {m: {"daily_limit": b.daily_limit, "monthly_limit": b.monthly_limit} 
                                     for m, b in models.items()} 
                                 for p, models in self.model_budgets.items()}
            }
            
            with open(self.get_state_file_path(), 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving token budget state: {str(e)}")
    
    def load_state(self):
        """Load state from file if it exists"""
        try:
            state_file = self.get_state_file_path()
            if not os.path.exists(state_file):
                return
            
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            self.daily_reset_time = datetime.fromisoformat(state.get("daily_reset_time", datetime.now().isoformat()))
            self.monthly_reset_time = datetime.fromisoformat(state.get("monthly_reset_time", datetime.now().isoformat()))
            self.daily_usage = state.get("daily_usage", {})
            self.monthly_usage = state.get("monthly_usage", {})
            
            # Load provider budgets
            for provider, budget in state.get("provider_budgets", {}).items():
                self.provider_budgets[provider] = TokenBudget(
                    daily_limit=budget.get("daily_limit"),
                    monthly_limit=budget.get("monthly_limit")
                )
            
            # Load model budgets
            for provider, models in state.get("model_budgets", {}).items():
                if provider not in self.model_budgets:
                    self.model_budgets[provider] = {}
                for model, budget in models.items():
                    self.model_budgets[provider][model] = TokenBudget(
                        daily_limit=budget.get("daily_limit"),
                        monthly_limit=budget.get("monthly_limit")
                    )
            
            logger.info(f"Loaded token budget state from {state_file}")
        except Exception as e:
            logger.error(f"Error loading token budget state: {str(e)}")

# Singleton instance
_token_budget_tracker = None

def get_token_budget_tracker() -> TokenBudgetTracker:
    """Get the singleton token budget tracker instance"""
    global _token_budget_tracker
    if _token_budget_tracker is None:
        _token_budget_tracker = TokenBudgetTracker()
    return _token_budget_tracker 
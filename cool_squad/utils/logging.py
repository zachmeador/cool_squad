"""
Custom LLM API Call Logging

This module provides logging functionality for LLM API calls.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from cool_squad.core.config import get_data_dir
from cool_squad.utils.token_budget import get_token_budget_tracker

# Set up logger
logger = logging.getLogger("llm_api")
logger.setLevel(logging.INFO)

# Custom JSON encoder to handle non-serializable objects
class LLMLogEncoder(json.JSONEncoder):
    def default(self, obj):
        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.isoformat()
            
        # Handle OpenAI chat completion objects
        if hasattr(obj, 'model_dump'):
            return obj.model_dump()
            
        # Handle other OpenAI objects
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        
        # Handle other non-serializable objects
        try:
            return str(obj)
        except:
            return "non-serializable-object"

# Default log directory is 'logs' in the data directory
def get_log_dir():
    """Get the log directory."""
    log_dir = os.path.join(get_data_dir(), "logs")
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    return log_dir

def setup_logging(log_file: Optional[str] = None):
    """
    Set up logging for LLM API calls.
    
    Args:
        log_file: Optional custom log file path. If not provided, a default one will be used.
    """
    if not log_file:
        # Create a log file with timestamp in the logs directory
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(get_log_dir(), f"llm_api_{timestamp}.log")
    
    # Create a file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Create a formatter with human readable timestamp
    formatter = logging.Formatter('%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s', 
                                datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    
    # Add the handler to the logger
    logger.addHandler(file_handler)
    
    return logger

def serialize_tool_call(tool_call):
    """
    Serialize a tool call object to a JSON-serializable dict.
    
    Args:
        tool_call: The tool call object from the API response
        
    Returns:
        A JSON-serializable dict representation of the tool call
    """
    return {
        "id": tool_call.id if hasattr(tool_call, "id") else None,
        "type": tool_call.type if hasattr(tool_call, "type") else None,
        "function": {
            "name": tool_call.function.name if hasattr(tool_call.function, "name") else None,
            "arguments": tool_call.function.arguments if hasattr(tool_call.function, "arguments") else None
        }
    }

def log_api_call(provider: str, model: str, messages: list, response: Any, 
                 tools: Optional[list] = None, tool_calls: Optional[list] = None,
                 complexity_info: Optional[Dict[str, Any]] = None):
    """
    Log an LLM API call to the log file.
    
    Args:
        provider: The LLM provider (e.g., 'openai', 'anthropic')
        model: The model name
        messages: The messages sent to the API
        response: The response from the API
        tools: Optional tools provided to the API
        tool_calls: Optional tool calls from the response
        complexity_info: Optional complexity analysis information
    """
    try:
        # Create log entry with human readable timestamp
        now = datetime.now()
        log_entry = {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "provider": provider,
            "model": model,
            "request": {
                "messages": messages,
            }
        }
        
        # Add complexity info if available
        if complexity_info:
            log_entry["complexity"] = complexity_info
        
        # Log full response object
        if response:
            log_entry["response_full"] = response
            
            # Add response summary if available
            if hasattr(response, "choices") and response.choices:
                log_entry["response_summary"] = {
                    "content_length": len(response.choices[0].message.content or "") if hasattr(response.choices[0].message, "content") else 0,
                    "finish_reason": response.choices[0].finish_reason if hasattr(response.choices[0], "finish_reason") else None,
                }
        
        # Add usage if available
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        
        if hasattr(response, "usage"):
            prompt_tokens = response.usage.prompt_tokens if hasattr(response.usage, "prompt_tokens") else 0
            completion_tokens = response.usage.completion_tokens if hasattr(response.usage, "completion_tokens") else 0
            total_tokens = response.usage.total_tokens if hasattr(response.usage, "total_tokens") else 0
            
            log_entry["usage"] = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            }
            
            # Track token usage in the budget tracker
            token_tracker = get_token_budget_tracker()
            within_budget, message = token_tracker.add_usage(
                provider=provider,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            
            # Add budget status to log entry
            log_entry["budget_status"] = {
                "within_budget": within_budget,
                "message": message
            }
            
            # Log warning if over budget
            if not within_budget:
                logger.warning(f"Token budget exceeded: {message}")
        
        # Add tools if provided
        if tools:
            log_entry["request"]["tools"] = tools
        
        # Add tool calls if provided
        if tool_calls:
            log_entry["response_summary"]["tool_calls"] = tool_calls
        
        # Log the entry using the custom encoder
        logger.info(json.dumps(log_entry, cls=LLMLogEncoder, indent=2))
    except Exception as e:
        # If there's an error in logging, log the error but don't crash the application
        logger.error(f"Error logging API call: {str(e)}")

# Initialize logging when module is imported
setup_logging() 
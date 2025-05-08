"""
Prompt Loader Utility

This module provides functions for loading prompts from files.
"""

import os
import logging
from typing import Dict, Optional, Union

# Setup logging
logger = logging.getLogger("prompt_loader")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Directory paths
DEFAULT_PROMPT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")
AGENT_PROMPT_DIR = os.path.join(DEFAULT_PROMPT_DIR, "agents")

# Cache for loaded prompts
_prompt_cache: Dict[str, str] = {}

def load_prompt(prompt_name: str, prompt_dir: Optional[str] = None) -> str:
    """
    Load a prompt from a file.
    
    Args:
        prompt_name: The name of the prompt file (with or without extension)
        prompt_dir: Optional directory path, defaults to prompts/agents
        
    Returns:
        The prompt text
    
    Raises:
        FileNotFoundError: If the prompt file does not exist
    """
    # Add .md extension if not present
    if not prompt_name.endswith(".md") and not prompt_name.endswith(".txt"):
        prompt_name += ".md"
    
    # Determine the directory to look in
    directory = prompt_dir or AGENT_PROMPT_DIR
    
    # Full path to the prompt file
    prompt_path = os.path.join(directory, prompt_name)
    
    # Check cache first
    if prompt_path in _prompt_cache:
        return _prompt_cache[prompt_path]
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_text = f.read()
            _prompt_cache[prompt_path] = prompt_text
            logger.debug(f"Loaded prompt from {prompt_path}")
            return prompt_text
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {prompt_path}")
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    except Exception as e:
        logger.error(f"Error loading prompt from {prompt_path}: {str(e)}")
        raise

def clear_cache() -> None:
    """Clear the prompt cache."""
    _prompt_cache.clear()
    logger.debug("Prompt cache cleared")

def list_available_prompts(directory: Optional[str] = None) -> Dict[str, str]:
    """
    List all available prompts in the specified directory.
    
    Args:
        directory: Optional directory path, defaults to prompts/agents
        
    Returns:
        Dictionary of prompt names to file paths
    """
    directory = directory or AGENT_PROMPT_DIR
    prompts = {}
    
    try:
        for filename in os.listdir(directory):
            if filename.endswith(".md") or filename.endswith(".txt"):
                prompt_name = os.path.splitext(filename)[0]
                prompts[prompt_name] = os.path.join(directory, filename)
        return prompts
    except Exception as e:
        logger.error(f"Error listing prompts in {directory}: {str(e)}")
        return {}

def get_prompt_path(prompt_name: str, prompt_dir: Optional[str] = None) -> str:
    """
    Get the full path to a prompt file.
    
    Args:
        prompt_name: The name of the prompt file (with or without extension)
        prompt_dir: Optional directory path, defaults to prompts/agents
        
    Returns:
        The full path to the prompt file
    """
    # Add .md extension if not present
    if not prompt_name.endswith(".md") and not prompt_name.endswith(".txt"):
        prompt_name += ".md"
    
    # Determine the directory to look in
    directory = prompt_dir or AGENT_PROMPT_DIR
    
    # Full path to the prompt file
    return os.path.join(directory, prompt_name) 
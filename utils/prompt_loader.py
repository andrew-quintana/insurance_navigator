"""
Prompt Loader Utility.

This module provides functions for loading prompts from files,
ensuring consistent prompt management across the system.
"""

import os
import logging
from typing import Optional, List, Dict, Any

# Setup logging
logger = logging.getLogger(__name__)
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

def load_prompt(prompt_path: str) -> str:
    """
    Load a prompt from a file.
    
    Args:
        prompt_path: Path to the prompt file
        
    Returns:
        Prompt text as a string
        
    Raises:
        FileNotFoundError: If the prompt file does not exist
    """
    if not os.path.exists(prompt_path):
        logger.error(f"Prompt file not found: {prompt_path}")
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    try:
        with open(prompt_path, "r") as f:
            prompt_text = f.read()
        
        logger.info(f"Loaded prompt from {prompt_path}")
        return prompt_text
    except Exception as e:
        logger.error(f"Error loading prompt from {prompt_path}: {str(e)}")
        raise

def load_examples(examples_path: str) -> List[Dict[str, Any]]:
    """
    Load examples from a file.
    
    Args:
        examples_path: Path to the examples file
        
    Returns:
        List of example dictionaries
        
    Raises:
        FileNotFoundError: If the examples file does not exist
    """
    if not os.path.exists(examples_path):
        logger.error(f"Examples file not found: {examples_path}")
        raise FileNotFoundError(f"Examples file not found: {examples_path}")
    
    try:
        import json
        with open(examples_path, "r") as f:
            examples = json.load(f)
        
        logger.info(f"Loaded {len(examples)} examples from {examples_path}")
        return examples
    except Exception as e:
        logger.error(f"Error loading examples from {examples_path}: {str(e)}")
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
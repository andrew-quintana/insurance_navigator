"""
Test module for the Prompt Loader utility.
"""

import os
import unittest
import sys
import shutil
import tempfile

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.prompt_loader import (
    load_prompt, clear_cache, list_available_prompts, get_prompt_path,
    DEFAULT_PROMPT_DIR, AGENT_PROMPT_DIR
)

class TestPromptLoader(unittest.TestCase):
    """Tests for the Prompt Loader utility."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test prompts
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test prompt file
        self.test_prompt_content = "This is a test prompt.\nWith multiple lines."
        self.test_prompt_path = os.path.join(self.temp_dir, "test_prompt.md")
        with open(self.test_prompt_path, 'w') as f:
            f.write(self.test_prompt_content)
        
        # Clear the cache before each test
        clear_cache()
    
    def tearDown(self):
        """Clean up after the test."""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_load_prompt_from_file(self):
        """Test loading a prompt from a file."""
        prompt = load_prompt("test_prompt", self.temp_dir)
        self.assertEqual(prompt, self.test_prompt_content)
    
    def test_prompt_cache(self):
        """Test that prompts are cached."""
        # Load the prompt once
        prompt1 = load_prompt("test_prompt", self.temp_dir)
        
        # Modify the file
        with open(self.test_prompt_path, 'w') as f:
            f.write("Modified content")
        
        # Load the prompt again, should get cached version
        prompt2 = load_prompt("test_prompt", self.temp_dir)
        
        # Prompts should be the same (from cache)
        self.assertEqual(prompt1, prompt2)
        
        # Clear the cache
        clear_cache()
        
        # Load the prompt again, should get the modified version
        prompt3 = load_prompt("test_prompt", self.temp_dir)
        
        # Prompt should be different from the cached version
        self.assertNotEqual(prompt1, prompt3)
        self.assertEqual(prompt3, "Modified content")
    
    def test_nonexistent_prompt(self):
        """Test loading a nonexistent prompt."""
        with self.assertRaises(FileNotFoundError):
            load_prompt("nonexistent_prompt", self.temp_dir)
    
    def test_list_available_prompts(self):
        """Test listing available prompts."""
        # Create another test prompt
        with open(os.path.join(self.temp_dir, "another_prompt.md"), 'w') as f:
            f.write("Another test prompt")
        
        # List prompts
        prompts = list_available_prompts(self.temp_dir)
        
        # Should have two prompts
        self.assertEqual(len(prompts), 2)
        self.assertIn("test_prompt", prompts)
        self.assertIn("another_prompt", prompts)
    
    def test_get_prompt_path(self):
        """Test getting the prompt path."""
        # Get path for test prompt
        path = get_prompt_path("test_prompt", self.temp_dir)
        
        # Should match the test prompt path
        self.assertEqual(path, self.test_prompt_path)
        
        # Get path for prompt without extension
        path = get_prompt_path("test_prompt", self.temp_dir)
        self.assertEqual(path, self.test_prompt_path)
        
        # Get path for prompt with extension
        path = get_prompt_path("test_prompt.md", self.temp_dir)
        self.assertEqual(path, self.test_prompt_path)
    
    def test_default_paths(self):
        """Test the default prompt paths."""
        # Check that DEFAULT_PROMPT_DIR points to the prompts directory
        self.assertTrue(DEFAULT_PROMPT_DIR.endswith("prompts"))
        
        # Check that AGENT_PROMPT_DIR points to the agents directory
        self.assertTrue(AGENT_PROMPT_DIR.endswith(os.path.join("prompts", "agents")))

if __name__ == "__main__":
    unittest.main() 
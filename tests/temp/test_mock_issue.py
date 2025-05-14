"""
Test script to isolate the MagicMock validation issue.
"""

import unittest
from unittest.mock import MagicMock
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Dict, Any

class TestModel(BaseModel):
    """Simple test model for validation."""
    text: str = Field(description="Text field that should be a string")
    value: int = Field(description="Value field that should be an integer")

class TestMockValidation(unittest.TestCase):
    """Test class to isolate the MagicMock validation issue."""
    
    def test_mock_as_string(self):
        """Test passing a MagicMock as a string."""
        # Create a mock
        mock = MagicMock()
        mock.__str__.return_value = "This is a mock string"
        
        # Try to create a model with the mock
        try:
            model = TestModel(text=mock, value=42)
            print(f"SUCCESS: Created model with mock as text: {model}")
        except Exception as e:
            print(f"FAILURE: Could not create model with mock as text: {str(e)}")
    
    def test_mock_with_content(self):
        """Test passing a MagicMock with content attribute."""
        # Create a mock with content attribute
        mock = MagicMock()
        mock.content = "This is mock content"
        
        # Try to create a model with the mock
        try:
            model = TestModel(text=str(mock.content), value=42)
            print(f"SUCCESS: Created model with mock.content: {model}")
        except Exception as e:
            print(f"FAILURE: Could not create model with mock.content: {str(e)}")
    
    def test_parser_with_mock(self):
        """Test the PydanticOutputParser with a mock."""
        # Create a parser
        parser = PydanticOutputParser(pydantic_object=TestModel)
        
        # Create a mock
        mock = MagicMock()
        mock.__str__.return_value = '{"text": "Mock text", "value": 42}'
        
        # Try to parse the mock
        try:
            result = parser.parse(mock)
            print(f"SUCCESS: Parser accepted mock: {result}")
        except Exception as e:
            print(f"FAILURE: Parser rejected mock: {str(e)}")
            
    def test_generation_with_mock(self):
        """Test creating a Generation with a mock."""
        from langchain_core.outputs import Generation
        
        # Create a mock
        mock = MagicMock()
        
        # Try to create a Generation with the mock
        try:
            gen = Generation(text=mock)
            print(f"SUCCESS: Created Generation with mock")
        except Exception as e:
            print(f"FAILURE: Could not create Generation with mock: {str(e)}")
            print(f"Mock type: {type(mock)}")
            print(f"Mock repr: {repr(mock)}")

if __name__ == "__main__":
    unittest.main() 